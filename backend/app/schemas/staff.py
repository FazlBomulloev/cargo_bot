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
    avatar_url: str | None = None
    permissions: list[str] = []
    warehouse_id: int | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_staff(cls, staff):
        import json
        perms = []
        if staff.permissions:
            try:
                perms = json.loads(staff.permissions)
            except (json.JSONDecodeError, TypeError):
                perms = []
        return cls(
            id=staff.id,
            full_name=staff.full_name,
            login=staff.login,
            role=staff.role,
            avatar_url=staff.avatar_url,
            permissions=perms,
            warehouse_id=staff.warehouse_id,
            is_active=staff.is_active,
            created_at=staff.created_at,
        )


class PermissionsUpdate(BaseModel):
    permissions: list[str]


class ResetPasswordRequest(BaseModel):
    new_password: str
