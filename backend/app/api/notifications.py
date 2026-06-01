import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notification import NotificationLog
from app.models.staff import StaffUser
from app.api.deps import require_role

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    query = select(NotificationLog)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    pages = max(1, math.ceil(total / per_page))
    result = await db.execute(
        query.order_by(NotificationLog.sent_at.desc())
        .offset((page - 1) * per_page).limit(per_page)
    )
    logs = result.scalars().all()
    items = [
        {
            "id": n.id, "client_id": n.client_id, "parcel_id": n.parcel_id,
            "notification_type": n.notification_type, "status": n.status,
            "error": n.error, "sent_at": n.sent_at.isoformat(),
        }
        for n in logs
    ]
    return {"items": items, "total": total, "page": page, "pages": pages, "per_page": per_page}
