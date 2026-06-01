from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.staff import StaffUser
from app.models.tariff import Tariff
from app.schemas.tariff import TariffCreate, TariffResponse, TariffUpdate
from app.services.audit_service import log_action
from app.api.deps import get_client_ip, require_role

router = APIRouter(prefix="/api/tariffs", tags=["tariffs"])


@router.get("", response_model=list[TariffResponse])
async def list_tariffs(
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    result = await db.execute(select(Tariff).order_by(Tariff.created_at.desc()))
    return result.scalars().all()


@router.get("/active", response_model=list[TariffResponse])
async def active_tariffs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Tariff).where(Tariff.is_active == True).order_by(Tariff.method)
    )
    return result.scalars().all()


@router.post("", response_model=TariffResponse, status_code=201)
async def create_tariff(
    body: TariffCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    if body.method not in ("avia", "truck"):
        raise HTTPException(status_code=400, detail="method must be 'avia' or 'truck'")
    old_tariffs = (await db.execute(
        select(Tariff).where(Tariff.method == body.method, Tariff.is_active == True)
    )).scalars().all()
    for t in old_tariffs:
        t.is_active = False
    tariff = Tariff(
        method=body.method, price_per_kg=body.price_per_kg,
        price_per_m3=body.price_per_m3, currency=body.currency,
        created_by=current_user.id,
    )
    db.add(tariff)
    await db.flush()
    await log_action(
        db, staff_id=current_user.id, action="create_tariff",
        entity_type="tariff", entity_id=tariff.id,
        after={"method": body.method, "price_per_kg": str(body.price_per_kg)},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(tariff)
    return tariff


@router.patch("/{tariff_id}", response_model=TariffResponse)
async def update_tariff(
    tariff_id: int,
    body: TariffUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("owner")),
):
    tariff = await db.get(Tariff, tariff_id)
    if not tariff:
        raise HTTPException(status_code=404, detail="Tariff not found")
    before = {"price_per_kg": str(tariff.price_per_kg)}
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(tariff, field, value)
    after = {"price_per_kg": str(tariff.price_per_kg)}
    await log_action(
        db, staff_id=current_user.id, action="update_tariff",
        entity_type="tariff", entity_id=tariff_id,
        before=before, after=after, ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(tariff)
    return tariff
