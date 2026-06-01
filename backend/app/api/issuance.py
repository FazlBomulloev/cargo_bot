import math
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.issuance import IssuanceItem, IssuanceOrder
from app.models.parcel_dushanbe import ParcelDushanbe
from app.models.staff import StaffUser
from app.models.tariff import Tariff
from app.schemas.issuance import IssuanceCreate, IssuanceItemResponse, IssuanceResponse
from app.services.audit_service import log_action
from app.api.deps import get_client_ip, require_role

router = APIRouter(prefix="/api/issuance", tags=["issuance"])


@router.post("", response_model=IssuanceResponse, status_code=201)
async def create_issuance(
    body: IssuanceCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    if body.payment_status not in ("paid", "debt"):
        raise HTTPException(status_code=400, detail="payment_status must be 'paid' or 'debt'")
    if body.payment_status == "paid" and body.payment_method not in ("cash", "transfer"):
        raise HTTPException(status_code=400, detail="payment_method must be 'cash' or 'transfer' when paid")

    total_weight = Decimal(0)
    total_amount = Decimal(0)
    items_data = []

    for pid in body.parcel_ids:
        parcel = await db.get(ParcelDushanbe, pid)
        if not parcel:
            raise HTTPException(status_code=404, detail=f"Parcel {pid} not found")
        if parcel.status == "issued":
            raise HTTPException(status_code=400, detail=f"Parcel {pid} already issued")

        tariff = (await db.execute(
            select(Tariff)
            .where(Tariff.method == parcel.delivery_method, Tariff.is_active == True)
            .order_by(Tariff.created_at.desc())
            .limit(1)
        )).scalar_one_or_none()
        if not tariff:
            raise HTTPException(status_code=400, detail=f"No active tariff for {parcel.delivery_method}")

        if parcel.delivery_method == "avia":
            amount = parcel.weight_kg * tariff.price_per_kg
        else:
            amount_by_kg = parcel.weight_kg * tariff.price_per_kg
            amount_by_m3 = (parcel.volume_m3 or Decimal(0)) * (tariff.price_per_m3 or Decimal(0))
            amount = max(amount_by_kg, amount_by_m3)

        parcel.status = "issued"
        parcel.amount_due = amount
        parcel.tariff_snapshot = tariff.price_per_kg

        total_weight += parcel.weight_kg
        total_amount += amount
        items_data.append({
            "parcel": parcel, "tariff": tariff, "amount": amount,
        })

    order = IssuanceOrder(
        client_id=body.client_id, staff_id=current_user.id,
        total_weight=total_weight, total_amount=total_amount,
        payment_status=body.payment_status, payment_method=body.payment_method,
    )
    db.add(order)
    await db.flush()

    items = []
    for d in items_data:
        p = d["parcel"]
        item = IssuanceItem(
            issuance_order_id=order.id, parcel_id=p.id,
            weight_kg=p.weight_kg, volume_m3=p.volume_m3,
            delivery_method=p.delivery_method,
            tariff_applied=d["tariff"].price_per_kg, amount=d["amount"],
        )
        db.add(item)
        items.append(item)

    await log_action(
        db, staff_id=current_user.id, action="issue_parcels",
        entity_type="issuance", entity_id=order.id,
        after={"client_id": body.client_id, "parcel_count": len(body.parcel_ids), "total_amount": str(total_amount)},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(order)
    for item in items:
        await db.refresh(item)

    return IssuanceResponse(
        id=order.id, client_id=order.client_id, staff_id=order.staff_id,
        total_weight=order.total_weight, total_amount=order.total_amount,
        payment_status=order.payment_status, payment_method=order.payment_method,
        issued_at=order.issued_at,
        items=[IssuanceItemResponse.model_validate(i) for i in items],
    )


@router.get("", response_model=dict)
async def list_issuance(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    client_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    query = select(IssuanceOrder)
    if client_id:
        query = query.where(IssuanceOrder.client_id == client_id)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    pages = max(1, math.ceil(total / per_page))
    result = await db.execute(
        query.order_by(IssuanceOrder.issued_at.desc())
        .offset((page - 1) * per_page).limit(per_page)
    )
    orders = result.scalars().all()
    items_out = []
    for order in orders:
        order_items = (await db.execute(
            select(IssuanceItem).where(IssuanceItem.issuance_order_id == order.id)
        )).scalars().all()
        items_out.append(IssuanceResponse(
            id=order.id, client_id=order.client_id, staff_id=order.staff_id,
            total_weight=order.total_weight, total_amount=order.total_amount,
            payment_status=order.payment_status, payment_method=order.payment_method,
            issued_at=order.issued_at,
            items=[IssuanceItemResponse.model_validate(i) for i in order_items],
        ))
    return {"items": items_out, "total": total, "page": page, "pages": pages, "per_page": per_page}


@router.get("/{order_id}", response_model=IssuanceResponse)
async def get_issuance(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    order = await db.get(IssuanceOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Issuance order not found")
    order_items = (await db.execute(
        select(IssuanceItem).where(IssuanceItem.issuance_order_id == order.id)
    )).scalars().all()
    return IssuanceResponse(
        id=order.id, client_id=order.client_id, staff_id=order.staff_id,
        total_weight=order.total_weight, total_amount=order.total_amount,
        payment_status=order.payment_status, payment_method=order.payment_method,
        issued_at=order.issued_at,
        items=[IssuanceItemResponse.model_validate(i) for i in order_items],
    )
