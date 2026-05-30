import logging
import re
from datetime import datetime, timedelta

from sqlalchemy import select, delete, func as sa_func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
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

# Красивые номера — заглушка, не выдаются
RESERVED_IDS = {
    "007", "111", "222", "333", "444",
    "555", "666", "777", "888", "999",
}

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
        "region": (
            "新疆维吾尔自治区 乌鲁木齐市 天山区"
        ),
        "address": (
            "延安路662号边疆宾馆19TPS号库房"
        ),
    },
    {
        "name": "Склад Урумчи (Авто)",
        "phone": "13999210571",
        "region": (
            "新疆维吾尔自治区 乌鲁木齐市 天山区"
        ),
        "address": (
            "延安路662号边疆宾馆19TPS号库房"
        ),
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
    async with async_session() as s:
        result = await s.execute(select(Warehouse))
        if not result.scalars().first():
            for w in SEED_WAREHOUSES:
                s.add(Warehouse(**w))
        await s.commit()


# ── Client ID ──

def _format_client_id(num: int) -> str:
    return f"TPS{num:03d}"


def _is_reserved(num: int) -> bool:
    suffix = f"{num:03d}"
    return suffix in RESERVED_IDS


def _client_id_num(client_id: str) -> int | None:
    m = re.fullmatch(r"TPS(\d+)", (client_id or "").strip().upper())
    return int(m.group(1)) if m else None


async def _next_client_id(s) -> str:
    """Минимальный свободный номер вида TPSNNN.

    Опирается на реально занятые client_id, а не на User.id:
    зарезервированные номера ломают соответствие id↔client_id,
    из-за чего max(id)+1 мог совпасть с уже выданным client_id.
    """
    result = await s.execute(select(User.client_id))
    used = {
        n for (cid,) in result.all()
        if (n := _client_id_num(cid)) is not None
    }
    num = 1
    while num in used or _is_reserved(num):
        num += 1
    return _format_client_id(num)


async def generate_client_id() -> str:
    async with async_session() as s:
        return await _next_client_id(s)


# ── Users ──

async def get_user(telegram_id: int) -> User | None:
    async with async_session() as s:
        result = await s.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )
        return result.scalar_one_or_none()


async def create_user(
    telegram_id: int, full_name: str,
    phone: str, lang: str = "ru",
) -> str:
    async with async_session() as s:
        # Идемпотентность: повторный апдейт / двойное нажатие
        # не должны создавать второго пользователя.
        existing = (await s.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )).scalar_one_or_none()
        if existing:
            return existing.client_id

        # Повторяем на случай гонки за один и тот же client_id.
        for _ in range(50):
            client_id = await _next_client_id(s)
            s.add(User(
                telegram_id=telegram_id,
                client_id=client_id,
                full_name=full_name,
                phone=phone,
                lang=lang,
            ))
            try:
                await s.commit()
                return client_id
            except IntegrityError:
                await s.rollback()
                # Параллельно мог появиться тот же telegram_id.
                existing = (await s.execute(
                    select(User).where(
                        User.telegram_id == telegram_id
                    )
                )).scalar_one_or_none()
                if existing:
                    return existing.client_id
                # Иначе client_id перехвачен — пробуем следующий.
        raise RuntimeError(
            "Не удалось сгенерировать уникальный client_id"
        )


async def update_user_lang(
    telegram_id: int, lang: str,
):
    async with async_session() as s:
        result = await s.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )
        user = result.scalar_one_or_none()
        if user:
            user.lang = lang
            await s.commit()


async def update_user_field(
    telegram_id: int, field: str, value: str,
):
    allowed = {"full_name", "phone"}
    if field not in allowed:
        return
    async with async_session() as s:
        result = await s.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )
        user = result.scalar_one_or_none()
        if user:
            setattr(user, field, value)
            await s.commit()


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
            r.telegram_id
            for r in result.scalars().all()
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
                async with s.begin_nested():
                    s.add(ParcelChina(track_code=code))
                added += 1
            except IntegrityError:
                continue
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
    rows: list[tuple[str, str, str]],
) -> list[dict]:
    """rows: список (track_code, client_id, status_mark).
    status_mark: '+' → received, иначе → waiting.
    """
    new_entries = []
    async with async_session() as s:
        for raw_track, raw_cid, raw_status in rows:
            code = normalize_track(raw_track)
            cid = raw_cid.strip().upper()
            if not code or not cid:
                continue
            status = (
                "received"
                if raw_status.strip() == "+"
                else "waiting"
            )
            existing = await s.execute(
                select(ParcelDushanbe).where(
                    ParcelDushanbe.track_code == code
                )
            )
            parcel = existing.scalar_one_or_none()
            if parcel:
                if (
                    status == "received"
                    and parcel.status != "received"
                ):
                    parcel.status = "received"
                continue
            try:
                async with s.begin_nested():
                    s.add(ParcelDushanbe(
                        track_code=code,
                        client_id=cid,
                        status=status,
                    ))
                new_entries.append({
                    "track_code": code,
                    "client_id": cid,
                    "status": status,
                })
            except IntegrityError:
                continue
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
) -> list[ParcelDushanbe]:
    cid = client_id.strip().upper()
    async with async_session() as s:
        result = await s.execute(
            select(ParcelDushanbe)
            .where(ParcelDushanbe.client_id == cid)
            .order_by(ParcelDushanbe.arrived_at.desc())
        )
        return list(result.scalars().all())


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


# ── Reminder ──

async def get_parcels_for_reminder(
) -> list[ParcelDushanbe]:
    cutoff = datetime.utcnow() - timedelta(days=7)
    async with async_session() as s:
        result = await s.execute(
            select(ParcelDushanbe).where(
                ParcelDushanbe.status == "waiting",
                ParcelDushanbe.notified == 1,
                ParcelDushanbe.reminder_sent == 0,
                ParcelDushanbe.arrived_at <= cutoff,
            )
        )
        return list(result.scalars().all())


async def mark_reminder_sent(track_code: str):
    code = normalize_track(track_code)
    async with async_session() as s:
        result = await s.execute(
            select(ParcelDushanbe).where(
                ParcelDushanbe.track_code == code
            )
        )
        parcel = result.scalar_one_or_none()
        if parcel:
            parcel.reminder_sent = 1
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


# ── Statistics ──

async def get_general_stats() -> dict:
    now = datetime.utcnow()
    today_start = now.replace(
        hour=0, minute=0, second=0, microsecond=0,
    )
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    async with async_session() as s:
        total_users = (await s.execute(
            select(sa_func.count(User.id))
        )).scalar() or 0

        users_today = (await s.execute(
            select(sa_func.count(User.id)).where(
                User.created_at >= today_start
            )
        )).scalar() or 0

        users_week = (await s.execute(
            select(sa_func.count(User.id)).where(
                User.created_at >= week_ago
            )
        )).scalar() or 0

        users_month = (await s.execute(
            select(sa_func.count(User.id)).where(
                User.created_at >= month_ago
            )
        )).scalar() or 0

        china_total = (await s.execute(
            select(sa_func.count(ParcelChina.id))
        )).scalar() or 0

        dushanbe_total = (await s.execute(
            select(sa_func.count(ParcelDushanbe.id))
        )).scalar() or 0

        dushanbe_waiting = (await s.execute(
            select(sa_func.count(ParcelDushanbe.id)).where(
                ParcelDushanbe.status == "waiting"
            )
        )).scalar() or 0

        dushanbe_received = (await s.execute(
            select(sa_func.count(ParcelDushanbe.id)).where(
                ParcelDushanbe.status == "received"
            )
        )).scalar() or 0

    return {
        "total_users": total_users,
        "users_today": users_today,
        "users_week": users_week,
        "users_month": users_month,
        "china_total": china_total,
        "dushanbe_total": dushanbe_total,
        "dushanbe_waiting": dushanbe_waiting,
        "dushanbe_received": dushanbe_received,
    }


async def get_top_clients(
    limit: int = 10,
) -> list[dict]:
    async with async_session() as s:
        result = await s.execute(
            select(
                ParcelDushanbe.client_id,
                sa_func.count(ParcelDushanbe.id).label(
                    "cnt",
                ),
            )
            .group_by(ParcelDushanbe.client_id)
            .order_by(
                sa_func.count(ParcelDushanbe.id).desc()
            )
            .limit(limit)
        )
        rows = result.all()

    clients = []
    for row in rows:
        async with async_session() as s:
            user = (await s.execute(
                select(User).where(
                    User.client_id == row.client_id
                )
            )).scalar_one_or_none()
        clients.append({
            "client_id": row.client_id,
            "count": row.cnt,
            "full_name": (
                user.full_name if user else "—"
            ),
        })
    return clients


async def get_stuck_parcels(
    days: int = 14,
) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    async with async_session() as s:
        result = await s.execute(
            select(ParcelDushanbe)
            .where(
                ParcelDushanbe.status == "waiting",
                ParcelDushanbe.arrived_at <= cutoff,
            )
            .order_by(ParcelDushanbe.arrived_at.asc())
        )
        parcels = result.scalars().all()

    items = []
    for p in parcels:
        waiting_days = (
            datetime.utcnow() - p.arrived_at
        ).days
        async with async_session() as s:
            user = (await s.execute(
                select(User).where(
                    User.client_id == p.client_id
                )
            )).scalar_one_or_none()
        items.append({
            "track_code": p.track_code,
            "client_id": p.client_id,
            "full_name": (
                user.full_name if user else "—"
            ),
            "phone": user.phone if user else "—",
            "waiting_days": waiting_days,
        })
    return items