from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import String, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.client import Client
from app.models.issuance import IssuanceOrder
from app.models.parcel_china import ParcelChina
from app.models.parcel_dushanbe import ParcelDushanbe
from app.models.staff import StaffUser
from app.api.deps import require_role

router = APIRouter(prefix="/api/stats", tags=["stats"])


def _resolve_range(period: str, from_date: str | None, to_date: str | None):
    now = datetime.utcnow()
    if period == "custom" and from_date:
        start = datetime.fromisoformat(from_date)
        end = datetime.fromisoformat(to_date) if to_date else now
        return start, end
    if period == "all":
        return None, None
    if period == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0), None
    days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
    return now - timedelta(days=days), None


def _time_filter(col, start, end):
    clauses = []
    if start is not None:
        clauses.append(col >= start)
    if end is not None:
        clauses.append(col <= end)
    return clauses


@router.get("/overview")
async def overview(
    period: str = Query("30d"),
    from_date: str | None = None,
    to_date: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("owner", "admin_china", "admin_dushanbe")),
):
    start, end = _resolve_range(period, from_date, to_date)

    china_count = (await db.execute(
        select(func.count(ParcelChina.id)).where(*_time_filter(ParcelChina.created_at, start, end))
    )).scalar() or 0

    dushanbe_count = (await db.execute(
        select(func.count(ParcelDushanbe.id)).where(*_time_filter(ParcelDushanbe.created_at, start, end))
    )).scalar() or 0

    issued_count = (await db.execute(
        select(func.count(ParcelDushanbe.id)).where(
            ParcelDushanbe.status == "issued", *_time_filter(ParcelDushanbe.updated_at, start, end)
        )
    )).scalar() or 0

    total_weight = (await db.execute(
        select(func.sum(ParcelDushanbe.weight_kg)).where(*_time_filter(ParcelDushanbe.created_at, start, end))
    )).scalar() or 0

    revenue_val = (await db.execute(
        select(func.sum(IssuanceOrder.total_amount)).where(*_time_filter(IssuanceOrder.issued_at, start, end))
    )).scalar() or 0

    new_clients = (await db.execute(
        select(func.count(Client.id)).where(*_time_filter(Client.created_at, start, end))
    )).scalar() or 0

    return {
        "china_count": china_count,
        "dushanbe_count": dushanbe_count,
        "issued_count": issued_count,
        "total_weight": float(total_weight),
        "revenue": float(revenue_val),
        "new_clients": new_clients,
    }


@router.get("/parcels-by-day")
async def parcels_by_day(
    period: str = Query("30d"),
    from_date: str | None = None,
    to_date: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("owner", "admin_china", "admin_dushanbe")),
):
    start, end = _resolve_range(period, from_date, to_date)
    now = datetime.utcnow()
    if start is None:
        start = now - timedelta(days=90)
    if end is None:
        end = now

    day_label = func.substr(func.cast(ParcelChina.created_at, String), 1, 10)
    china = (await db.execute(
        select(day_label.label("day"), func.count(ParcelChina.id))
        .where(ParcelChina.created_at.between(start, end))
        .group_by("day").order_by("day")
    )).all()

    day_label2 = func.substr(func.cast(ParcelDushanbe.created_at, String), 1, 10)
    dushanbe = (await db.execute(
        select(day_label2.label("day"), func.count(ParcelDushanbe.id))
        .where(ParcelDushanbe.created_at.between(start, end))
        .group_by("day").order_by("day")
    )).all()

    combined = defaultdict(int)
    for d in china:
        combined[d[0]] += d[1]
    for d in dushanbe:
        combined[d[0]] += d[1]

    return [{"date": k, "count": v} for k, v in sorted(combined.items())]


@router.get("/revenue")
async def revenue(
    period: str = Query("30d"),
    from_date: str | None = None,
    to_date: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("owner", "admin_china", "admin_dushanbe")),
):
    start, end = _resolve_range(period, from_date, to_date)

    period_label = func.substr(func.cast(IssuanceOrder.issued_at, String), 1, 10)
    query = select(period_label.label("period"), func.sum(IssuanceOrder.total_amount))
    filters = _time_filter(IssuanceOrder.issued_at, start, end)
    if filters:
        query = query.where(*filters)
    result = (await db.execute(query.group_by("period").order_by("period"))).all()
    return [{"period": r[0], "amount": float(r[1])} for r in result]


@router.get("/top-clients")
async def top_clients(
    period: str = Query("30d"),
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = Query(10, ge=1, le=50),
    sort_by: str = Query("amount"),
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("owner", "admin_china", "admin_dushanbe")),
):
    start, end = _resolve_range(period, from_date, to_date)

    if sort_by in ("amount", "weight"):
        order_col = func.sum(IssuanceOrder.total_amount).desc() if sort_by == "amount" else func.sum(IssuanceOrder.total_weight).desc()
        query = (
            select(
                IssuanceOrder.client_id,
                func.sum(IssuanceOrder.total_amount).label("total_amount"),
                func.sum(IssuanceOrder.total_weight).label("total_weight"),
                func.count(IssuanceOrder.id).label("order_count"),
            )
        )
        filters = _time_filter(IssuanceOrder.issued_at, start, end)
        if filters:
            query = query.where(*filters)
        result = (await db.execute(
            query.group_by(IssuanceOrder.client_id).order_by(order_col).limit(limit)
        )).all()
        clients = []
        for r in result:
            c = await db.get(Client, r.client_id)
            clients.append({
                "client_id": r.client_id,
                "tps_code": c.tps_code if c else "?",
                "full_name": c.full_name if c else "?",
                "total_amount": float(r.total_amount),
                "total_weight": float(r.total_weight),
                "order_count": r.order_count,
            })
        return clients

    query = (
        select(
            ParcelDushanbe.client_id,
            func.count(ParcelDushanbe.id).label("parcel_count"),
        )
    )
    filters = _time_filter(ParcelDushanbe.created_at, start, end)
    if filters:
        query = query.where(*filters)
    result = (await db.execute(
        query.group_by(ParcelDushanbe.client_id)
        .order_by(func.count(ParcelDushanbe.id).desc())
        .limit(limit)
    )).all()
    clients = []
    for r in result:
        c = await db.get(Client, r.client_id)
        clients.append({
            "client_id": r.client_id,
            "tps_code": c.tps_code if c else "?",
            "full_name": c.full_name if c else "?",
            "parcel_count": r.parcel_count,
        })
    return clients


@router.get("/stuck-parcels")
async def stuck_parcels(
    period: str = Query("30d"),
    from_date: str | None = None,
    to_date: str | None = None,
    days: int = Query(14),
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("owner", "admin_china", "admin_dushanbe")),
):
    start, end = _resolve_range(period, from_date, to_date)
    cutoff = datetime.utcnow() - timedelta(days=days)

    query = (
        select(ParcelDushanbe)
        .where(
            ParcelDushanbe.status == "received_dushanbe",
            ParcelDushanbe.created_at <= cutoff,
        )
    )
    filters = _time_filter(ParcelDushanbe.created_at, start, end)
    if filters:
        query = query.where(*filters)
    result = (await db.execute(query.order_by(ParcelDushanbe.created_at.asc()))).scalars().all()
    items = []
    for p in result:
        c = await db.get(Client, p.client_id)
        waiting = (datetime.utcnow() - p.created_at).days
        items.append({
            "parcel_id": p.id, "track_id": p.track_id,
            "client_id": p.client_id,
            "tps_code": c.tps_code if c else "?",
            "full_name": c.full_name if c else "?",
            "phone": c.phone if c else "?",
            "waiting_days": waiting,
        })
    return items


@router.get("/staff-activity")
async def staff_activity(
    period: str = Query("30d"),
    from_date: str | None = None,
    to_date: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("owner", "admin_china", "admin_dushanbe")),
):
    from app.models.audit import AuditLog
    start, end = _resolve_range(period, from_date, to_date)
    query = select(
        AuditLog.staff_id,
        func.count(AuditLog.id).label("action_count"),
    ).group_by(AuditLog.staff_id).order_by(func.count(AuditLog.id).desc())
    filters = _time_filter(AuditLog.created_at, start, end)
    if filters:
        query = query.where(*filters)
    result = (await db.execute(query)).all()
    items = []
    for r in result:
        staff = await db.get(StaffUser, r.staff_id)
        items.append({
            "staff_id": r.staff_id,
            "full_name": staff.full_name if staff else "?",
            "role": staff.role if staff else "?",
            "action_count": r.action_count,
        })
    return items
