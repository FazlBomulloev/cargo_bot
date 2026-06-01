from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.staff import StaffUser
from app.models.warehouse import Warehouse
from app.schemas.warehouse import WarehouseCreate, WarehouseResponse, WarehouseUpdate
from app.services.audit_service import log_action
from app.api.deps import get_client_ip, require_role

router = APIRouter(prefix="/api/warehouses", tags=["warehouses"])


@router.get("", response_model=list[WarehouseResponse])
async def list_warehouses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Warehouse).where(Warehouse.is_active == True).order_by(Warehouse.id)
    )
    return result.scalars().all()


@router.get("/{wid}", response_model=WarehouseResponse)
async def get_warehouse(wid: int, db: AsyncSession = Depends(get_db)):
    w = await db.get(Warehouse, wid)
    if not w:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return w


@router.post("", response_model=WarehouseResponse, status_code=201)
async def create_warehouse(
    body: WarehouseCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    if body.type not in ("china", "dushanbe", "pvz"):
        raise HTTPException(status_code=400, detail="type must be 'china', 'dushanbe', or 'pvz'")
    w = Warehouse(**body.model_dump())
    db.add(w)
    await db.flush()
    await log_action(
        db, staff_id=current_user.id, action="create_warehouse",
        entity_type="warehouse", entity_id=w.id,
        after=body.model_dump(), ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(w)
    return w


@router.patch("/{wid}", response_model=WarehouseResponse)
async def update_warehouse(
    wid: int,
    body: WarehouseUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    w = await db.get(Warehouse, wid)
    if not w:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    before = {k: getattr(w, k) for k in body.model_dump(exclude_unset=True)}
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(w, field, value)
    after = {k: getattr(w, k) for k in body.model_dump(exclude_unset=True)}
    await log_action(
        db, staff_id=current_user.id, action="update_warehouse",
        entity_type="warehouse", entity_id=wid,
        before=before, after=after, ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(w)
    return w


@router.delete("/{wid}")
async def delete_warehouse(
    wid: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("owner")),
):
    w = await db.get(Warehouse, wid)
    if not w:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    w.is_active = False
    await log_action(
        db, staff_id=current_user.id, action="delete_warehouse",
        entity_type="warehouse", entity_id=wid,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return {"detail": "Warehouse deactivated"}
