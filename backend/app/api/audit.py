import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit import AuditLog
from app.models.staff import StaffUser
from app.api.deps import require_role

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


@router.get("")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    staff_id: int | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    query = select(AuditLog)
    if staff_id:
        query = query.where(AuditLog.staff_id == staff_id)
    if action:
        query = query.where(AuditLog.action == action)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    pages = max(1, math.ceil(total / per_page))
    result = await db.execute(
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * per_page).limit(per_page)
    )
    logs = result.scalars().all()
    staff_cache: dict[int, str] = {}
    items = []
    for log in logs:
        if log.staff_id not in staff_cache:
            s = await db.get(StaffUser, log.staff_id)
            staff_cache[log.staff_id] = s.full_name if s else "?"
        items.append({
            "id": log.id, "staff_id": log.staff_id,
            "staff_name": staff_cache[log.staff_id],
            "action": log.action,
            "entity_type": log.entity_type, "entity_id": log.entity_id,
            "created_at": log.created_at.isoformat(),
        })
    return {"items": items, "total": total, "page": page, "pages": pages, "per_page": per_page}
