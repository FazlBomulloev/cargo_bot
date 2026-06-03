from pydantic import BaseModel


class LoginRequest(BaseModel):
    login: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class StaffMeResponse(BaseModel):
    id: int
    full_name: str
    login: str
    role: str
    avatar_url: str | None = None
    permissions: list[str] = []
    warehouse_id: int | None = None
    is_active: bool

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
        )


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    login: str | None = None
    current_password: str | None = None
    new_password: str | None = None
