from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IssuanceOrder(Base):
    __tablename__ = "issuance_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    staff_id: Mapped[int] = mapped_column(Integer, ForeignKey("staff_users.id"), nullable=False)
    total_weight: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class IssuanceItem(Base):
    __tablename__ = "issuance_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issuance_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("issuance_orders.id"), nullable=False
    )
    parcel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("parcels_dushanbe.id"), nullable=False
    )
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    volume_m3: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    delivery_method: Mapped[str] = mapped_column(String(20), nullable=False)
    tariff_applied: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
