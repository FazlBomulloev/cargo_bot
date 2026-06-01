from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ParcelDushanbe(Base):
    __tablename__ = "parcels_dushanbe"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    track_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="received_dushanbe", server_default="received_dushanbe"
    )
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    volume_m3: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    delivery_method: Mapped[str] = mapped_column(String(20), nullable=False)
    warehouse_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("warehouses.id"), nullable=True
    )
    amount_due: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    tariff_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    has_china_registration: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("staff_users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_parcels_dushanbe_track_id", "track_id", unique=True),
        Index("ix_parcels_dushanbe_client_id", "client_id"),
        Index("ix_parcels_dushanbe_status", "status"),
        Index("ix_parcels_dushanbe_created_at", "created_at"),
        Index("ix_parcels_dushanbe_delivery_method", "delivery_method"),
    )
