from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.client import Client
from app.models.parcel_china import ParcelChina
from app.models.parcel_dushanbe import ParcelDushanbe
from app.models.staff import StaffUser
from app.models.unresolved import UnresolvedParcel
from app.services.audit_service import log_action
from app.api.deps import get_client_ip, require_role

router = APIRouter(prefix="/api/unresolved", tags=["unresolved"])


class ResolveRequest(BaseModel):
    tps_code: str


@router.get("")
async def list_unresolved(
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    result = await db.execute(
        select(UnresolvedParcel)
        .where(UnresolvedParcel.resolved == False)
        .order_by(UnresolvedParcel.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{item_id}/resolve")
async def resolve_parcel(
    item_id: int,
    body: ResolveRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    unresolved = await db.get(UnresolvedParcel, item_id)
    if not unresolved or unresolved.resolved:
        raise HTTPException(status_code=404, detail="Unresolved parcel not found")

    tps = body.tps_code.strip().upper()
    client = (await db.execute(select(Client).where(Client.tps_code == tps))).scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client with this TPS code not found")

    china = (await db.execute(
        select(ParcelChina).where(ParcelChina.track_id == unresolved.track_id)
    )).scalar_one_or_none()

    parcel = ParcelDushanbe(
        track_id=unresolved.track_id, client_id=client.id,
        weight_kg=unresolved.weight_kg or 0, volume_m3=unresolved.volume_m3,
        delivery_method=unresolved.delivery_method or "avia",
        comment=unresolved.comment, has_china_registration=china is not None,
        created_by=current_user.id,
    )
    db.add(parcel)
    await db.flush()

    unresolved.resolved = True
    unresolved.resolved_parcel_id = parcel.id

    await log_action(
        db, staff_id=current_user.id, action="resolve_unresolved",
        entity_type="parcel", entity_id=parcel.id,
        after={"track_id": unresolved.track_id, "tps_code": tps},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return {"detail": "Resolved", "parcel_id": parcel.id, "client_name": client.full_name}


@router.delete("/{item_id}")
async def delete_unresolved(
    item_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    unresolved = await db.get(UnresolvedParcel, item_id)
    if not unresolved:
        raise HTTPException(status_code=404, detail="Not found")
    unresolved.resolved = True
    await log_action(
        db, staff_id=current_user.id, action="delete_unresolved",
        entity_type="unresolved", entity_id=item_id,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return {"detail": "Deleted (soft)"}
