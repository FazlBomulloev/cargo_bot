from datetime import datetime

from pydantic import BaseModel


class StaffCreate(BaseModel):
    full_name: str
    login: str
    password: str
    role: str
    warehouse_id: int | None = None


class StaffUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    warehouse_id: int | None = None
    is_active: bool | None = None


class StaffResponse(BaseModel):
    id: int
    full_name: str
    login: str
    role: str
    warehouse_id: int | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ResetPasswordRequest(BaseModel):
    new_password: str
