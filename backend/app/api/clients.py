import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.client import Client
from app.models.staff import StaffUser
from app.schemas.client import ClientRegister, ClientResponse, ClientUpdate
from app.services.audit_service import log_action
from app.utils.tps_code import generate_tps_code
from app.api.deps import get_client_ip, require_role, verify_bot_secret

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.post("/register", response_model=ClientResponse, status_code=201, dependencies=[Depends(verify_bot_secret)])
async def register_client(body: ClientRegister, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(Client).where(Client.telegram_id == body.telegram_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Client already registered")
    tps_code = await generate_tps_code(db)
    client = Client(
        telegram_id=body.telegram_id,
        tps_code=tps_code,
        full_name=body.full_name,
        phone=body.phone,
        address=body.address,
        lang=body.lang,
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


@router.get("/by-telegram/{telegram_id}", response_model=ClientResponse | None, dependencies=[Depends(verify_bot_secret)])
async def get_by_telegram(telegram_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Client).where(Client.telegram_id == telegram_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.patch("/by-telegram/{telegram_id}", response_model=ClientResponse, dependencies=[Depends(verify_bot_secret)])
async def update_by_telegram(
    telegram_id: int, body: ClientUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Client).where(Client.telegram_id == telegram_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    await db.commit()
    await db.refresh(client)
    return client


@router.get("", response_model=dict)
async def list_clients(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    query = select(Client).where(Client.status != "deleted")
    if q:
        q_upper = q.strip().upper()
        query = query.where(
            or_(
                Client.tps_code.ilike(f"%{q}%"),
                Client.phone.ilike(f"%{q}%"),
                Client.full_name.ilike(f"%{q}%"),
            )
        )
    total_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_q)).scalar() or 0
    pages = max(1, math.ceil(total / per_page))
    result = await db.execute(
        query.order_by(Client.id.desc()).offset((page - 1) * per_page).limit(per_page)
    )
    items = [ClientResponse.model_validate(c) for c in result.scalars().all()]
    return {"items": items, "total": total, "page": page, "pages": pages, "per_page": per_page}


@router.get("/search", response_model=list[ClientResponse])
async def search_clients(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    result = await db.execute(
        select(Client)
        .where(
            Client.status != "deleted",
            or_(
                Client.tps_code.ilike(f"%{q}%"),
                Client.phone.ilike(f"%{q}%"),
                Client.full_name.ilike(f"%{q}%"),
            ),
        )
        .limit(20)
    )
    return result.scalars().all()


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    body: ClientUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("owner")),
):
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    before = {"full_name": client.full_name, "phone": client.phone, "address": client.address}
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    after = {"full_name": client.full_name, "phone": client.phone, "address": client.address}
    await log_action(
        db,
        staff_id=current_user.id,
        action="update_client",
        entity_type="client",
        entity_id=client.id,
        before=before,
        after=after,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(client)
    return client


@router.patch("/{client_id}/block")
async def block_client(
    client_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("owner")),
):
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    new_status = "blocked" if client.status == "active" else "active"
    await log_action(
        db,
        staff_id=current_user.id,
        action="block_client" if new_status == "blocked" else "unblock_client",
        entity_type="client",
        entity_id=client.id,
        before={"status": client.status},
        after={"status": new_status},
        ip_address=get_client_ip(request),
    )
    client.status = new_status
    await db.commit()
    return {"detail": f"Client {new_status}", "status": new_status}
