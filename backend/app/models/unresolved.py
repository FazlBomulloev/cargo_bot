from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UnresolvedParcel(Base):
    __tablename__ = "unresolved_parcels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    track_id: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_tps_code: Mapped[str] = mapped_column(String(50), nullable=False)
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    volume_m3: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    delivery_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    resolved_parcel_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("parcels_dushanbe.id"), nullable=True
    )
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("staff_users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
