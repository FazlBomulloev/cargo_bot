import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.staff import StaffUser
from app.schemas.staff import PermissionsUpdate, ResetPasswordRequest, StaffCreate, StaffResponse, StaffUpdate
from app.services.audit_service import log_action
from app.utils.security import hash_password
from app.api.deps import get_client_ip, require_role

router = APIRouter(prefix="/api/staff", tags=["staff"])

owner_only = require_role("owner")


@router.get("")
async def list_staff(
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(owner_only),
):
    result = await db.execute(select(StaffUser).order_by(StaffUser.id))
    return [StaffResponse.from_staff(s) for s in result.scalars().all()]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_staff(
    body: StaffCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(owner_only),
):
    if body.role not in ("owner", "admin_china", "admin_dushanbe"):
        raise HTTPException(status_code=400, detail="Invalid role")
    existing = await db.execute(select(StaffUser).where(StaffUser.login == body.login))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Login already exists")
    default_perms = {
        "admin_china": ["parcels_china", "parcels_list"],
        "admin_dushanbe": ["parcels_dushanbe", "parcels_list", "issuance", "issuance_history", "clients", "unresolved"],
        "owner": [],
    }
    staff = StaffUser(
        full_name=body.full_name,
        login=body.login,
        password_hash=hash_password(body.password),
        role=body.role,
        warehouse_id=body.warehouse_id,
        permissions=json.dumps(default_perms.get(body.role, [])),
    )
    db.add(staff)
    await db.flush()
    await log_action(
        db,
        staff_id=current_user.id,
        action="create_staff",
        entity_type="staff",
        entity_id=staff.id,
        after={"login": staff.login, "role": staff.role, "full_name": staff.full_name},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(staff)
    return StaffResponse.from_staff(staff)


@router.patch("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: int,
    body: StaffUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(owner_only),
):
    staff = await db.get(StaffUser, staff_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    before = {"full_name": staff.full_name, "role": staff.role, "is_active": staff.is_active}
    if body.full_name is not None:
        staff.full_name = body.full_name
    if body.role is not None:
        if body.role not in ("owner", "admin_china", "admin_dushanbe"):
            raise HTTPException(status_code=400, detail="Invalid role")
        staff.role = body.role
    if body.warehouse_id is not None:
        staff.warehouse_id = body.warehouse_id
    if body.is_active is not None:
        staff.is_active = body.is_active
    after = {"full_name": staff.full_name, "role": staff.role, "is_active": staff.is_active}
    await log_action(
        db,
        staff_id=current_user.id,
        action="update_staff",
        entity_type="staff",
        entity_id=staff.id,
        before=before,
        after=after,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(staff)
    return staff


@router.delete("/{staff_id}")
async def deactivate_staff(
    staff_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(owner_only),
):
    staff = await db.get(StaffUser, staff_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    if staff.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    staff.is_active = False
    await log_action(
        db,
        staff_id=current_user.id,
        action="deactivate_staff",
        entity_type="staff",
        entity_id=staff.id,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return {"detail": "Staff deactivated"}


@router.post("/{staff_id}/reset-password")
async def reset_password(
    staff_id: int,
    body: ResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(owner_only),
):
    staff = await db.get(StaffUser, staff_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    staff.password_hash = hash_password(body.new_password)
    await log_action(
        db,
        staff_id=current_user.id,
        action="reset_password",
        entity_type="staff",
        entity_id=staff.id,
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return {"detail": "Password reset successfully"}


VALID_PERMISSIONS = [
    "dashboard", "parcels_china", "parcels_dushanbe", "parcels_list",
    "issuance", "issuance_history", "clients", "unresolved",
    "warehouses", "tariffs", "staff", "settings", "audit",
]


@router.patch("/{staff_id}/permissions")
async def update_permissions(
    staff_id: int,
    body: PermissionsUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(owner_only),
):
    staff = await db.get(StaffUser, staff_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    if staff.role == "owner":
        raise HTTPException(status_code=400, detail="Cannot change owner permissions")
    filtered = [p for p in body.permissions if p in VALID_PERMISSIONS]
    before_perms = staff.permissions or "[]"
    staff.permissions = json.dumps(filtered)
    await log_action(
        db,
        staff_id=current_user.id,
        action="update_permissions",
        entity_type="staff",
        entity_id=staff.id,
        before={"permissions": before_perms},
        after={"permissions": filtered},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(staff)
    return StaffResponse.from_staff(staff)
