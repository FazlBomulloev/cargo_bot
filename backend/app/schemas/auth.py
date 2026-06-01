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
    warehouse_id: int | None = None
    is_active: bool

    model_config = {"from_attributes": True}
