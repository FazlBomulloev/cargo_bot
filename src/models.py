from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


class Base(DeclarativeBase):
    pass


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
    )
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False,
    )
    tps_code: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )
    phone: Mapped[str] = mapped_column(
        String(20), nullable=False,
    )
    address: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    lang: Mapped[str] = mapped_column(
        String(5), default="ru", server_default="ru",
    )
    status: Mapped[str] = mapped_column(
        String(20), default="active",
        server_default="active",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(),
    )
    last_activity_at: Mapped[datetime | None] = (
        mapped_column(DateTime, nullable=True)
    )


class ParcelChina(Base):
    __tablename__ = "parcels_china"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
    )
    track_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False,
    )
    warehouse_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
    )
    created_by: Mapped[int] = mapped_column(
        Integer, nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(),
    )


class ParcelDushanbe(Base):
    __tablename__ = "parcels_dushanbe"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
    )
    track_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False,
    )
    client_id: Mapped[int] = mapped_column(
        Integer, nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False,
        default="received_dushanbe",
        server_default="received_dushanbe",
    )
    weight_kg: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), nullable=False,
    )
    volume_m3: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), nullable=True,
    )
    delivery_method: Mapped[str] = mapped_column(
        String(20), nullable=False,
    )
    warehouse_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
    )
    amount_due: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True,
    )
    tariff_snapshot: Mapped[Decimal | None] = (
        mapped_column(Numeric(10, 2), nullable=True)
    )
    has_china_registration: Mapped[bool] = (
        mapped_column(Boolean, default=False)
    )
    comment: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    notified_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True,
    )
    created_by: Mapped[int] = mapped_column(
        Integer, nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(),
    )


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(
        String(100), primary_key=True,
    )
    value: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(),
    )
    updated_by: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
    )


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False,
    )
    type: Mapped[str] = mapped_column(
        String(20), nullable=False,
    )
    country: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
    )
    city: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
    )
    phone: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )
    region: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )
    address: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(),
    )
