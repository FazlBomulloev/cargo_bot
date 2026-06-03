import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.client import Client
from app.models.parcel_china import ParcelChina
from app.models.parcel_dushanbe import ParcelDushanbe
from app.models.staff import StaffUser
from app.models.unresolved import UnresolvedParcel
from app.schemas.parcel import (
    ParcelChinaBulk,
    ParcelChinaCreate,
    ParcelChinaResponse,
    ParcelDushanbeCreate,
    ParcelDushanbeResponse,
    ParcelStatusUpdate,
    ParcelUpdate,
)
from app.services.audit_service import log_action
from app.utils.track_normalize import normalize_track
from app.api.deps import get_client_ip, require_role, verify_bot_secret

router = APIRouter(prefix="/api/parcels", tags=["parcels"])

VALID_STATUSES = {"received_dushanbe", "issued", "problem"}


# ── China ──

@router.post("/china", response_model=ParcelChinaResponse, status_code=201)
async def add_china(
    body: ParcelChinaCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_china", "owner")),
):
    track = normalize_track(body.track_id)
    if not track:
        raise HTTPException(status_code=400, detail="Invalid track code")
    existing = await db.execute(select(ParcelChina).where(ParcelChina.track_id == track))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Track already exists")
    parcel = ParcelChina(track_id=track, created_by=current_user.id)
    db.add(parcel)
    await db.flush()
    await log_action(
        db, staff_id=current_user.id, action="create_parcel_china",
        entity_type="parcel", entity_id=parcel.id,
        after={"track_id": track}, ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(parcel)
    return parcel


@router.post("/china/bulk")
async def add_china_bulk(
    body: ParcelChinaBulk,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_china", "owner")),
):
    added = 0
    duplicates = []
    for raw in body.track_ids:
        track = normalize_track(raw)
        if not track:
            continue
        existing = await db.execute(select(ParcelChina).where(ParcelChina.track_id == track))
        if existing.scalar_one_or_none():
            duplicates.append(track)
            continue
        db.add(ParcelChina(track_id=track, created_by=current_user.id))
        added += 1
    if added:
        await log_action(
            db, staff_id=current_user.id, action="bulk_create_parcel_china",
            entity_type="parcel", after={"count": added}, ip_address=get_client_ip(request),
        )
    await db.commit()
    return {
        "total": len(body.track_ids),
        "added": added,
        "duplicates": len(duplicates),
        "duplicate_list": duplicates,
    }


@router.get("/china", response_model=dict)
async def list_china(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_china", "owner")),
):
    query = select(ParcelChina)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    pages = max(1, math.ceil(total / per_page))
    result = await db.execute(
        query.order_by(ParcelChina.created_at.desc())
        .offset((page - 1) * per_page).limit(per_page)
    )
    items = [ParcelChinaResponse.model_validate(p) for p in result.scalars().all()]
    return {"items": items, "total": total, "page": page, "pages": pages, "per_page": per_page}


# ── Dushanbe ──

@router.post("/dushanbe", status_code=201)
async def add_dushanbe(
    body: ParcelDushanbeCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    track = normalize_track(body.track_id)
    if not track:
        raise HTTPException(status_code=400, detail="Invalid track code")
    if body.delivery_method not in ("avia", "truck"):
        raise HTTPException(status_code=400, detail="delivery_method must be 'avia' or 'truck'")

    tps = body.tps_code.strip().upper()
    result = await db.execute(select(Client).where(Client.tps_code == tps))
    client = result.scalar_one_or_none()

    if not client:
        unresolved = UnresolvedParcel(
            track_id=track, raw_tps_code=tps, weight_kg=body.weight_kg,
            volume_m3=body.volume_m3, delivery_method=body.delivery_method,
            comment=body.comment, created_by=current_user.id,
        )
        db.add(unresolved)
        await db.commit()
        return {"status": "unresolved", "message": "TPS code not found, saved as unresolved"}

    existing = await db.execute(select(ParcelDushanbe).where(ParcelDushanbe.track_id == track))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Track already processed in Dushanbe")

    china_result = await db.execute(select(ParcelChina).where(ParcelChina.track_id == track))
    has_china = china_result.scalar_one_or_none() is not None

    parcel = ParcelDushanbe(
        track_id=track, client_id=client.id, weight_kg=body.weight_kg,
        volume_m3=body.volume_m3, delivery_method=body.delivery_method,
        comment=body.comment, has_china_registration=has_china,
        created_by=current_user.id,
    )
    db.add(parcel)
    await db.flush()
    await log_action(
        db, staff_id=current_user.id, action="create_parcel_dushanbe",
        entity_type="parcel", entity_id=parcel.id,
        after={"track_id": track, "client_id": client.id, "tps_code": tps},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(parcel)
    return {
        "status": "ok", "parcel_id": parcel.id,
        "client_name": client.full_name, "telegram_id": client.telegram_id,
    }


# ── List / detail ──

@router.get("/all")
async def list_all_parcels(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_china", "admin_dushanbe", "owner")),
):
    async def _unresolved_items(db: AsyncSession, query=None):
        if query is None:
            query = select(UnresolvedParcel).where(UnresolvedParcel.resolved == False)
        result = await db.execute(query.order_by(UnresolvedParcel.created_at.desc()))
        items = []
        for p in result.scalars().all():
            items.append({
                "id": p.id, "track_id": p.track_id, "status": "unresolved",
                "weight_kg": float(p.weight_kg) if p.weight_kg else None,
                "delivery_method": p.delivery_method,
                "client_name": None, "tps_code": p.raw_tps_code,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            })
        return items

    async def _dushanbe_items(db: AsyncSession, query):
        result = await db.execute(query.order_by(ParcelDushanbe.created_at.desc()))
        items = []
        for p in result.scalars().all():
            c = await db.get(Client, p.client_id) if p.client_id else None
            items.append({
                "id": p.id, "track_id": p.track_id, "status": p.status,
                "weight_kg": float(p.weight_kg) if p.weight_kg else None,
                "delivery_method": p.delivery_method,
                "client_name": c.full_name if c else None,
                "tps_code": c.tps_code if c else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            })
        return items

    if status_filter == "in_china":
        query = select(ParcelChina)
        total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
        pages = max(1, math.ceil(total / per_page))
        result = await db.execute(
            query.order_by(ParcelChina.created_at.desc())
            .offset((page - 1) * per_page).limit(per_page)
        )
        items = []
        for p in result.scalars().all():
            items.append({
                "id": p.id, "track_id": p.track_id, "status": "in_china",
                "weight_kg": None, "delivery_method": None,
                "client_name": None, "tps_code": None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            })
        return {"items": items, "total": total, "page": page, "pages": pages}

    if status_filter == "unresolved":
        all_items = await _unresolved_items(db)
        total = len(all_items)
        pages = max(1, math.ceil(total / per_page))
        start = (page - 1) * per_page
        return {"items": all_items[start:start + per_page], "total": total, "page": page, "pages": pages}

    if status_filter:
        query = select(ParcelDushanbe).where(ParcelDushanbe.status == status_filter)
        all_items = await _dushanbe_items(db, query)
        total = len(all_items)
        pages = max(1, math.ceil(total / per_page))
        start = (page - 1) * per_page
        return {"items": all_items[start:start + per_page], "total": total, "page": page, "pages": pages}

    # No filter — combine China + Dushanbe + Unresolved
    china_result = await db.execute(
        select(ParcelChina).order_by(ParcelChina.created_at.desc())
    )
    all_items = []
    for p in china_result.scalars().all():
        all_items.append({
            "id": p.id, "track_id": p.track_id, "status": "in_china",
            "weight_kg": None, "delivery_method": None,
            "client_name": None, "tps_code": None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })
    all_items.extend(await _dushanbe_items(db, select(ParcelDushanbe)))
    all_items.extend(await _unresolved_items(db))

    all_items.sort(key=lambda x: x["created_at"] or "", reverse=True)
    total = len(all_items)
    pages = max(1, math.ceil(total / per_page))
    start = (page - 1) * per_page
    items = all_items[start:start + per_page]
    return {"items": items, "total": total, "page": page, "pages": pages}


@router.get("", response_model=dict)
async def list_parcels(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    client_id: int | None = None,
    delivery_method: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    query = select(ParcelDushanbe)
    if status_filter:
        query = query.where(ParcelDushanbe.status == status_filter)
    if client_id:
        query = query.where(ParcelDushanbe.client_id == client_id)
    if delivery_method:
        query = query.where(ParcelDushanbe.delivery_method == delivery_method)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    pages = max(1, math.ceil(total / per_page))
    result = await db.execute(
        query.order_by(ParcelDushanbe.created_at.desc())
        .offset((page - 1) * per_page).limit(per_page)
    )
    items = [ParcelDushanbeResponse.model_validate(p) for p in result.scalars().all()]
    return {"items": items, "total": total, "page": page, "pages": pages, "per_page": per_page}


@router.get("/track/{track_id}")
async def search_by_track(track_id: str, db: AsyncSession = Depends(get_db)):
    track = normalize_track(track_id)
    dushanbe = (await db.execute(
        select(ParcelDushanbe).where(ParcelDushanbe.track_id == track)
    )).scalar_one_or_none()
    if dushanbe:
        return {"location": "dushanbe", "status": dushanbe.status, "track_id": track}
    china = (await db.execute(
        select(ParcelChina).where(ParcelChina.track_id == track)
    )).scalar_one_or_none()
    if china:
        return {"location": "china", "status": "in_china", "track_id": track}
    return {"location": None, "status": "not_found", "track_id": track}


@router.get("/my", dependencies=[Depends(verify_bot_secret)])
async def my_parcels(
    telegram_id: int,
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    client = (await db.execute(
        select(Client).where(Client.telegram_id == telegram_id)
    )).scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    query = select(ParcelDushanbe).where(ParcelDushanbe.client_id == client.id)
    if status_filter:
        query = query.where(ParcelDushanbe.status == status_filter)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    pages = max(1, math.ceil(total / per_page))
    result = await db.execute(
        query.order_by(ParcelDushanbe.created_at.desc())
        .offset((page - 1) * per_page).limit(per_page)
    )
    items = [ParcelDushanbeResponse.model_validate(p) for p in result.scalars().all()]
    return {"items": items, "total": total, "page": page, "pages": pages, "per_page": per_page}


@router.get("/{parcel_id}", response_model=ParcelDushanbeResponse)
async def get_parcel(
    parcel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    parcel = await db.get(ParcelDushanbe, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return parcel


@router.patch("/{parcel_id}/status", response_model=ParcelDushanbeResponse)
async def update_status(
    parcel_id: int,
    body: ParcelStatusUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")
    parcel = await db.get(ParcelDushanbe, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    before = {"status": parcel.status}
    parcel.status = body.status
    await log_action(
        db, staff_id=current_user.id, action="update_status",
        entity_type="parcel", entity_id=parcel.id,
        before=before, after={"status": body.status},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(parcel)
    return parcel


@router.patch("/{parcel_id}", response_model=ParcelDushanbeResponse)
async def update_parcel(
    parcel_id: int,
    body: ParcelUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    parcel = await db.get(ParcelDushanbe, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    before = {}
    after = {}
    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "status" and value not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status")
        before[field] = getattr(parcel, field)
        setattr(parcel, field, value)
        after[field] = value
    await log_action(
        db, staff_id=current_user.id, action="update_parcel",
        entity_type="parcel", entity_id=parcel.id,
        before=before, after=after, ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(parcel)
    return parcel
