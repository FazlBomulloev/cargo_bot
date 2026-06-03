from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StaffUser(Base):
    __tablename__ = "staff_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    login: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    permissions: Mapped[str | None] = mapped_column(Text, nullable=True)
    warehouse_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("warehouses.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
