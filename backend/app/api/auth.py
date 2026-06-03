import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.staff import StaffUser
from app.schemas.auth import LoginRequest, ProfileUpdate, StaffMeResponse, TokenResponse
from app.utils.security import create_access_token, hash_password, verify_password
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

AVATARS_DIR = Path("data/avatars")
AVATARS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StaffUser).where(StaffUser.login == body.login))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token)


@router.get("/me")
async def get_me(current_user: StaffUser = Depends(get_current_user)):
    return StaffMeResponse.from_staff(current_user)


@router.patch("/profile")
async def update_profile(
    body: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user),
):
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.login is not None:
        existing = await db.execute(
            select(StaffUser).where(StaffUser.login == body.login, StaffUser.id != current_user.id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Логин уже занят")
        current_user.login = body.login
    if body.new_password:
        if not body.current_password or not verify_password(body.current_password, current_user.password_hash):
            raise HTTPException(status_code=400, detail="Неверный текущий пароль")
        current_user.password_hash = hash_password(body.new_password)
    await db.commit()
    await db.refresh(current_user)
    return StaffMeResponse.from_staff(current_user)


@router.post("/profile/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user),
):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Допустимы только JPEG, PNG, WebP")
    ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "jpg"
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = AVATARS_DIR / filename
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    if current_user.avatar_url:
        old_path = AVATARS_DIR / current_user.avatar_url.split("/")[-1]
        if old_path.exists() and old_path != filepath:
            old_path.unlink(missing_ok=True)
    current_user.avatar_url = f"/api/auth/avatars/{filename}"
    await db.commit()
    await db.refresh(current_user)
    return StaffMeResponse.from_staff(current_user)


from fastapi.responses import FileResponse

@router.get("/avatars/{filename}")
async def get_avatar(filename: str):
    path = AVATARS_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path)
