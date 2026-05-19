import logging
import random
import re

from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import DB_PATH, DB_URL
from src.models import (
    Admin,
    Base,
    ParcelChina,
    ParcelDushanbe,
    Setting,
    User,
    Warehouse,
)

log = logging.getLogger(__name__)

engine = create_async_engine(DB_URL, echo=False)
async_session = async_sessionmaker(
    engine, expire_on_commit=False,
)

TARIFFS_DEFAULT = (
    "💰 Тарифы доставки\n"
    "\n"
    "✈️ Авиа\n"
    "━━━━━━━━━━━━━━━\n"
    "📍 Урумчи\n"
    "├ 🚚 Стандарт: 3–10 дней — 7.5–10 $\n"
    "└ ⚡ VIP: 1–5 дней — 10–12 $\n"
    "\n"
    "📍 Иву\n"
    "└ 🚚 Стандарт: 9–12 дней — 8.5–12 $\n"
    "\n"
    "🚛 Фура\n"
    "━━━━━━━━━━━━━━━\n"
    "📍 Гуанчжоу — 2.5 $/кг | 280 $/м³\n"
    "📍 Урумчи — 2.5 $/кг | 280 $/м³\n"
    "📍 Иву — 2.5 $/кг | 280 $/м³\n"
    "\n"
    "ℹ️ Сроки и цены могут меняться "
    "в зависимости от условий доставки."
)

SUPPORT_DEFAULT = (
    "🆘 Поддержка\n\n"
    "По вопросам доставки и статуса посылки "
    "свяжитесь с нашей службой поддержки.\n\n"
    "📞 Телефоны компании:\n"
    "+992 XX XXX XX XX\n"
    "+992 XX XXX XX XX"
)

SEED_WAREHOUSES = [
    {
        "name": "Склад Иву",
        "phone": "19878638724",
        "region": "浙江省 金华市 义乌市",
        "address": "洪华小区26幢2单元",
    },
    {
        "name": "Склад Урумчи (Авиа)",
        "phone": "13999210571",
        "region": "新疆维吾尔自治区 乌鲁木齐市 天山区",
        "address": "延安路662号边疆宾馆19TPS号库房",
    },
    {
        "name": "Склад Урумчи (Авто)",
        "phone": "13999210571",
        "region": "新疆维吾尔自治区 乌鲁木齐市 天山区",
        "address": "延安路662号边疆宾馆19TPS号库房",
    },
]


def normalize_track(value: str) -> str:
    value = str(value).upper().strip()
    return re.sub(r"[^A-Z0-9]+", "", value)


async def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed_defaults()
    log.info("БД инициализирована")


async def _seed_defaults():
    defaults = {
        "tariffs": TARIFFS_DEFAULT,
        "support": SUPPORT_DEFAULT,
    }
    async with async_session() as s:
        for key, value in defaults.items():
            existing = await s.get(Setting, key)
            if not existing:
                s.add(Setting(key=key, value=value))
        result = await s.execute(select(Warehouse))
        if not result.scalars().first():
            for w in SEED_WAREHOUSES:
                s.add(Warehouse(**w))
        await s.commit()


# ── Users ──

async def generate_client_id() -> str:
    async with async_session() as s:
        while True:
            cid = f"TPS{random.randint(100000, 999999)}"
            result = await s.execute(
                select(User).where(
                    User.client_id == cid
                )
            )
            if not result.scalar_one_or_none():
                return cid


async def get_user(telegram_id: int) -> User | None:
    async with async_session() as s:
        result = await s.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )
        return result.scalar_one_or_none()


async def create_user(
    telegram_id: int, full_name: str, phone: str,
) -> str:
    client_id = await generate_client_id()
    async with async_session() as s:
        s.add(User(
            telegram_id=telegram_id,
            client_id=client_id,
            full_name=full_name,
            phone=phone,
        ))
        await s.commit()
    return client_id


async def get_user_by_client_id(
    client_id: str,
) -> User | None:
    cid = client_id.strip().upper()
    async with async_session() as s:
        result = await s.execute(
            select(User).where(User.client_id == cid)
        )
        return result.scalar_one_or_none()


# ── Admins ──

async def is_admin(telegram_id: int) -> bool:
    from src.config import SUPER_ADMIN_ID
    if telegram_id == SUPER_ADMIN_ID:
        return True
    async with async_session() as s:
        result = await s.execute(
            select(Admin).where(
                Admin.telegram_id == telegram_id
            )
        )
        return result.scalar_one_or_none() is not None


async def add_admin(telegram_id: int) -> bool:
    async with async_session() as s:
        try:
            s.add(Admin(telegram_id=telegram_id))
            await s.commit()
            return True
        except IntegrityError:
            await s.rollback()
            return False


async def remove_admin(telegram_id: int) -> bool:
    async with async_session() as s:
        result = await s.execute(
            delete(Admin).where(
                Admin.telegram_id == telegram_id
            )
        )
        await s.commit()
        return result.rowcount > 0


async def list_admins() -> list[int]:
    async with async_session() as s:
        result = await s.execute(select(Admin))
        return [
            r.telegram_id for r in result.scalars().all()
        ]


# ── Parcels China ──

async def add_parcels_china(
    track_codes: list[str],
) -> int:
    added = 0
    async with async_session() as s:
        for raw in track_codes:
            code = normalize_track(raw)
            if not code:
                continue
            try:
                s.add(ParcelChina(track_code=code))
                await s.flush()
                added += 1
            except IntegrityError:
                await s.rollback()
                s.begin()
        await s.commit()
    return added


async def find_in_china(track_code: str) -> bool:
    code = normalize_track(track_code)
    async with async_session() as s:
        result = await s.execute(
            select(ParcelChina).where(
                ParcelChina.track_code == code
            )
        )
        return result.scalar_one_or_none() is not None


# ── Parcels Dushanbe ──

async def add_parcels_dushanbe(
    rows: list[tuple[str, str]],
) -> list[dict]:
    new_entries = []
    async with async_session() as s:
        for raw_track, raw_cid in rows:
            code = normalize_track(raw_track)
            cid = raw_cid.strip().upper()
            if not code or not cid:
                continue
            try:
                s.add(ParcelDushanbe(
                    track_code=code, client_id=cid,
                ))
                await s.flush()
                new_entries.append({
                    "track_code": code,
                    "client_id": cid,
                })
            except IntegrityError:
                await s.rollback()
                s.begin()
        await s.commit()
    return new_entries


async def find_in_dushanbe(
    track_code: str,
) -> ParcelDushanbe | None:
    code = normalize_track(track_code)
    async with async_session() as s:
        result = await s.execute(
            select(ParcelDushanbe).where(
                ParcelDushanbe.track_code == code
            )
        )
        return result.scalar_one_or_none()


async def get_parcels_by_client(
    client_id: str,
) -> dict:
    cid = client_id.strip().upper()
    async with async_session() as s:
        result = await s.execute(
            select(ParcelDushanbe).where(
                ParcelDushanbe.client_id == cid
            )
        )
        parcels = result.scalars().all()
        return {
            "dushanbe": [p.track_code for p in parcels],
        }


async def mark_notified(track_code: str):
    code = normalize_track(track_code)
    async with async_session() as s:
        result = await s.execute(
            select(ParcelDushanbe).where(
                ParcelDushanbe.track_code == code
            )
        )
        parcel = result.scalar_one_or_none()
        if parcel:
            parcel.notified = 1
            await s.commit()


# ── Warehouses ──

async def list_warehouses() -> list[Warehouse]:
    async with async_session() as s:
        result = await s.execute(
            select(Warehouse).order_by(Warehouse.id)
        )
        return list(result.scalars().all())


async def get_warehouse(wid: int) -> Warehouse | None:
    async with async_session() as s:
        return await s.get(Warehouse, wid)


async def add_warehouse(
    name: str, phone: str,
    region: str, address: str,
) -> int:
    async with async_session() as s:
        w = Warehouse(
            name=name, phone=phone,
            region=region, address=address,
        )
        s.add(w)
        await s.commit()
        return w.id


async def update_warehouse(
    wid: int, field: str, value: str,
):
    allowed = {"name", "phone", "region", "address"}
    if field not in allowed:
        return
    async with async_session() as s:
        w = await s.get(Warehouse, wid)
        if w:
            setattr(w, field, value)
            await s.commit()


async def delete_warehouse(wid: int) -> bool:
    async with async_session() as s:
        w = await s.get(Warehouse, wid)
        if not w:
            return False
        await s.delete(w)
        await s.commit()
        return True


# ── Settings ──

async def get_setting(key: str) -> str | None:
    async with async_session() as s:
        result = await s.get(Setting, key)
        return result.value if result else None


async def set_setting(key: str, value: str):
    async with async_session() as s:
        existing = await s.get(Setting, key)
        if existing:
            existing.value = value
        else:
            s.add(Setting(key=key, value=value))
        await s.commit()