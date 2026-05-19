from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Integer,
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


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
    )
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False,
    )
    client_id: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )
    phone: Mapped[str] = mapped_column(
        String(20), nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(),
    )


class Admin(Base):
    __tablename__ = "admins"

    telegram_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True,
    )


class ParcelChina(Base):
    __tablename__ = "parcels_china"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
    )
    track_code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(),
    )


class ParcelDushanbe(Base):
    __tablename__ = "parcels_dushanbe"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
    )
    track_code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False,
    )
    client_id: Mapped[str] = mapped_column(
        String(20), nullable=False,
    )
    notified: Mapped[int] = mapped_column(
        Integer, default=0,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
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


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False,
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