import logging
import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from src.config import DB_PATH, DB_URL
from src.models import (
    Base,
    Client,
    ParcelChina,
    ParcelDushanbe,
    Setting,
    Warehouse,
)

log = logging.getLogger(__name__)

engine = create_async_engine(DB_URL, echo=False)
async_session = async_sessionmaker(
    engine, expire_on_commit=False,
)

RESERVED_NUMBERS = {
    7, 111, 222, 333, 444, 555, 666, 777, 888, 999,
}


def normalize_track(value: str) -> str:
    value = str(value).upper().strip()
    return re.sub(r"[^A-Z0-9]+", "", value)


async def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    log.info("БД подключена: %s", DB_PATH)


# ── TPS code generation ──

def _format_tps_code(num: int) -> str:
    if num < 1000:
        return f"TPS{num:03d}"
    return f"TPS{num}"


def _parse_tps_number(code: str) -> int | None:
    m = re.fullmatch(
        r"TPS(\d+)", (code or "").strip().upper(),
    )
    return int(m.group(1)) if m else None


async def _next_tps_code(s) -> str:
    result = await s.execute(select(Client.tps_code))
    used = {
        n for (code,) in result.all()
        if (n := _parse_tps_number(code)) is not None
    }
    num = 1
    while num in used or num in RESERVED_NUMBERS:
        num += 1
    return _format_tps_code(num)


# ── Clients ──

async def get_client(
    telegram_id: int,
) -> Client | None:
    async with async_session() as s:
        result = await s.execute(
            select(Client).where(
                Client.telegram_id == telegram_id
            )
        )
        return result.scalar_one_or_none()


async def create_client(
    telegram_id: int, full_name: str,
    phone: str, lang: str = "ru",
) -> str:
    async with async_session() as s:
        existing = (await s.execute(
            select(Client).where(
                Client.telegram_id == telegram_id
            )
        )).scalar_one_or_none()
        if existing:
            return existing.tps_code

        for _ in range(50):
            tps_code = await _next_tps_code(s)
            s.add(Client(
                telegram_id=telegram_id,
                tps_code=tps_code,
                full_name=full_name,
                phone=phone,
                lang=lang,
            ))
            try:
                await s.commit()
                return tps_code
            except IntegrityError:
                await s.rollback()
                existing = (await s.execute(
                    select(Client).where(
                        Client.telegram_id == telegram_id
                    )
                )).scalar_one_or_none()
                if existing:
                    return existing.tps_code
        raise RuntimeError(
            "Не удалось сгенерировать уникальный TPS код"
        )


async def update_client_lang(
    telegram_id: int, lang: str,
):
    async with async_session() as s:
        result = await s.execute(
            select(Client).where(
                Client.telegram_id == telegram_id
            )
        )
        client = result.scalar_one_or_none()
        if client:
            client.lang = lang
            await s.commit()


async def update_client_field(
    telegram_id: int, field: str, value: str,
):
    allowed = {"full_name", "phone"}
    if field not in allowed:
        return
    async with async_session() as s:
        result = await s.execute(
            select(Client).where(
                Client.telegram_id == telegram_id
            )
        )
        client = result.scalar_one_or_none()
        if client:
            setattr(client, field, value)
            await s.commit()


async def get_client_by_tps_code(
    tps_code: str,
) -> Client | None:
    code = tps_code.strip().upper()
    async with async_session() as s:
        result = await s.execute(
            select(Client).where(
                Client.tps_code == code
            )
        )
        return result.scalar_one_or_none()


# ── Parcels China ──

async def find_in_china(track: str) -> bool:
    code = normalize_track(track)
    async with async_session() as s:
        result = await s.execute(
            select(ParcelChina).where(
                ParcelChina.track_id == code
            )
        )
        return result.scalar_one_or_none() is not None


# ── Parcels Dushanbe ──

async def find_in_dushanbe(
    track: str,
) -> ParcelDushanbe | None:
    code = normalize_track(track)
    async with async_session() as s:
        result = await s.execute(
            select(ParcelDushanbe).where(
                ParcelDushanbe.track_id == code
            )
        )
        return result.scalar_one_or_none()


async def get_parcels_by_client(
    tps_code: str,
) -> list[ParcelDushanbe]:
    code = tps_code.strip().upper()
    async with async_session() as s:
        client = (await s.execute(
            select(Client).where(
                Client.tps_code == code
            )
        )).scalar_one_or_none()
        if not client:
            return []
        result = await s.execute(
            select(ParcelDushanbe)
            .where(ParcelDushanbe.client_id == client.id)
            .order_by(ParcelDushanbe.created_at.desc())
        )
        return list(result.scalars().all())


# ── Notifications ──

async def get_unnotified_parcels() -> list[dict]:
    async with async_session() as s:
        result = await s.execute(
            select(ParcelDushanbe).where(
                ParcelDushanbe.notified_at.is_(None)
            )
        )
        parcels = result.scalars().all()
        items = []
        for p in parcels:
            client = (await s.execute(
                select(Client).where(
                    Client.id == p.client_id
                )
            )).scalar_one_or_none()
            if client:
                items.append({
                    "track_id": p.track_id,
                    "telegram_id": client.telegram_id,
                    "lang": client.lang or "ru",
                })
        return items


async def mark_notified(track_id: str):
    code = normalize_track(track_id)
    async with async_session() as s:
        result = await s.execute(
            select(ParcelDushanbe).where(
                ParcelDushanbe.track_id == code
            )
        )
        parcel = result.scalar_one_or_none()
        if parcel:
            parcel.notified_at = datetime.utcnow()
            await s.commit()


# ── Warehouses ──

async def list_warehouses() -> list[Warehouse]:
    async with async_session() as s:
        result = await s.execute(
            select(Warehouse)
            .where(Warehouse.is_active.is_(True))
            .order_by(Warehouse.id)
        )
        return list(result.scalars().all())


async def get_warehouse(
    wid: int,
) -> Warehouse | None:
    async with async_session() as s:
        return await s.get(Warehouse, wid)


# ── Settings ──

async def get_setting(key: str) -> str | None:
    async with async_session() as s:
        result = await s.get(Setting, key)
        return result.value if result else None
