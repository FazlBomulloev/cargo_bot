"""
Seed script: generates 3 months of realistic demo data.
Uses existing staff/warehouses/tariffs from the database.
Run inside api container:  python seed_demo.py
"""
import asyncio
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, func

from app.database import engine, async_session, Base
from app.models.staff import StaffUser
from app.models.client import Client
from app.models.warehouse import Warehouse
from app.models.tariff import Tariff
from app.models.parcel_china import ParcelChina
from app.models.parcel_dushanbe import ParcelDushanbe
from app.models.issuance import IssuanceOrder, IssuanceItem
from app.models.unresolved import UnresolvedParcel
from app.models.audit import AuditLog

random.seed(42)

NOW = datetime(2026, 6, 1, 12, 0, 0)
START = NOW - timedelta(days=90)

FIRST_NAMES_M = [
    "Фируз", "Шерзод", "Бахтиёр", "Далер", "Рустам", "Аброр", "Сардор",
    "Жасур", "Нодир", "Акмал", "Достон", "Ислом", "Комил", "Лутфулло",
    "Мирзо", "Озод", "Парвиз", "Равшан", "Сухроб", "Тохир", "Улугбек",
    "Фаррух", "Хуршед", "Шухрат", "Эльмурод", "Ёкуб", "Зафар", "Икром",
    "Камол", "Набижон", "Ориф", "Рахмат", "Сиёвуш", "Умед", "Файзулло",
]
FIRST_NAMES_F = [
    "Мадина", "Нигора", "Зарина", "Фарида", "Дилноза", "Гулнора",
    "Парвина", "Сабина", "Шахноза", "Азиза", "Малика", "Нилуфар",
    "Рухшона", "Тахмина", "Хилола",
]
LAST_NAMES = [
    "Рахимов", "Каримов", "Ахмедов", "Назаров", "Усмонов", "Шарипов",
    "Муродов", "Холиков", "Саидов", "Бобоев", "Мирзоев", "Олимов",
    "Тошматов", "Хасанов", "Нуров", "Абдуллоев", "Ганиев", "Давлатов",
    "Исмоилов", "Файзуллоев", "Раджабов", "Содиков", "Турсунов",
    "Хамидов", "Юлдашев",
]

TRACK_PREFIXES = ["YT", "SF", "LP", "JN", "ZX", "CR", "TX"]
COMMENTS = [
    None, None, None, None, None,
    "Хрупкий товар", "Электроника", "Одежда", "Обувь", "Запчасти",
    "Косметика", "Аксессуары", "Телефон", "Планшет", "Ноутбук",
]
IPS = ["192.168.1.10", "192.168.1.11", "10.0.0.5", "172.16.0.100", "192.168.4.98"]


def rand_date(start: datetime, end: datetime) -> datetime:
    delta = (end - start).total_seconds()
    return start + timedelta(seconds=random.uniform(0, delta))


def rand_track() -> str:
    prefix = random.choice(TRACK_PREFIXES)
    digits = "".join(random.choices(string.digits, k=12))
    return f"{prefix}{digits}"


def rand_phone_tj() -> str:
    code = random.choice(["90", "91", "92", "93", "98", "88", "77"])
    num = "".join(random.choices(string.digits, k=7))
    return f"+992{code}{num}"


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # ── Use existing staff ──
        staff_result = await db.execute(select(StaffUser))
        staff_list = staff_result.scalars().all()
        if not staff_list:
            print("ERROR: No staff users found. Start the API first to create the owner.")
            return
        staff_ids = [s.id for s in staff_list]
        owner_id = next((s.id for s in staff_list if s.role == "owner"), staff_ids[0])
        china_admin_id = next((s.id for s in staff_list if s.role == "admin_china"), owner_id)
        dushanbe_admin_id = next((s.id for s in staff_list if s.role == "admin_dushanbe"), owner_id)
        print(f"Staff: using {len(staff_ids)} existing users")

        # ── Use existing warehouses ──
        wh_result = await db.execute(select(Warehouse))
        warehouses = wh_result.scalars().all()
        if not warehouses:
            print("ERROR: No warehouses found. Start the API first to seed warehouses.")
            return
        china_wh_ids = [w.id for w in warehouses if w.type == "china"]
        dushanbe_wh_id = next((w.id for w in warehouses if w.type == "dushanbe"), warehouses[0].id)
        if not china_wh_ids:
            china_wh_ids = [warehouses[0].id]
        print(f"Warehouses: using {len(warehouses)} existing")

        # ── Use existing tariffs ──
        tariff_result = await db.execute(select(Tariff).where(Tariff.is_active == True))
        tariffs = tariff_result.scalars().all()
        tariff_avia = next((t for t in tariffs if t.method == "avia"), None)
        tariff_truck = next((t for t in tariffs if t.method == "truck"), None)
        if not tariff_avia or not tariff_truck:
            print("ERROR: Tariffs not found. Start the API first to seed tariffs.")
            return
        print(f"Tariffs: avia ${tariff_avia.price_per_kg}/kg, truck ${tariff_truck.price_per_kg}/kg")

        # ── Check existing data ──
        existing_clients = (await db.execute(select(func.count()).select_from(Client))).scalar() or 0
        existing_china = (await db.execute(select(func.count()).select_from(ParcelChina))).scalar() or 0
        existing_dushanbe = (await db.execute(select(func.count()).select_from(ParcelDushanbe))).scalar() or 0
        if existing_clients > 10 or existing_china > 10 or existing_dushanbe > 10:
            print(f"WARNING: Database already has data (clients={existing_clients}, china={existing_china}, dushanbe={existing_dushanbe})")
            print("Skipping seed to avoid duplicates. Clear tables first if you want to re-seed.")
            return

        # ── Find next TPS code ──
        tps_result = await db.execute(select(Client.tps_code))
        used_tps = {row[0] for row in tps_result.all()}
        next_tps_num = 1
        while f"TPS{next_tps_num:03d}" in used_tps:
            next_tps_num += 1

        # ── Clients (75) ──
        clients = []
        used_tg_ids = set()
        for i in range(75):
            is_female = random.random() < 0.3
            first = random.choice(FIRST_NAMES_F if is_female else FIRST_NAMES_M)
            last = random.choice(LAST_NAMES)
            if is_female and last.endswith("ов"):
                last = last + "а"
            elif is_female and last.endswith("ев"):
                last = last + "а"
            full_name = f"{last} {first}"
            tg_id = random.randint(100_000_000, 999_999_999)
            while tg_id in used_tg_ids:
                tg_id = random.randint(100_000_000, 999_999_999)
            used_tg_ids.add(tg_id)
            reg_date = rand_date(START - timedelta(days=10), NOW - timedelta(days=5))
            tps_code = f"TPS{next_tps_num + i:03d}"
            c = Client(
                telegram_id=tg_id,
                tps_code=tps_code,
                full_name=full_name,
                phone=rand_phone_tj(),
                address=random.choice([None, "Душанбе", "Худжанд", "Куляб", "Бохтар"]),
                lang=random.choice(["ru", "tj", "uz"]),
                status="active",
                created_at=reg_date,
                last_activity_at=rand_date(reg_date, NOW),
            )
            clients.append(c)
        random.choice(clients).status = "blocked"
        random.choice(clients).status = "blocked"
        db.add_all(clients)
        await db.flush()
        print(f"Clients: {len(clients)}")

        # ── China parcels (300) ──
        china_parcels = []
        track_ids_china = set()
        for _ in range(300):
            track = rand_track()
            while track in track_ids_china:
                track = rand_track()
            track_ids_china.add(track)
            p = ParcelChina(
                track_id=track,
                warehouse_id=random.choice(china_wh_ids),
                created_by=china_admin_id,
                created_at=rand_date(START, NOW - timedelta(days=2)),
            )
            china_parcels.append(p)
        db.add_all(china_parcels)
        await db.flush()
        print(f"China parcels: {len(china_parcels)}")

        # ── Dushanbe parcels (230 of the 300 arrived) ──
        arrived_tracks = random.sample(china_parcels, 230)
        dushanbe_parcels = []
        for cp in arrived_tracks:
            method = random.choices(["avia", "truck"], weights=[70, 30])[0]
            weight = round(random.uniform(0.3, 25.0), 2)
            volume = round(random.uniform(0.01, 2.0), 3) if method == "truck" else None
            tariff = tariff_avia if method == "avia" else tariff_truck
            if method == "avia":
                amount = round(weight * float(tariff.price_per_kg), 2)
            else:
                by_kg = weight * float(tariff.price_per_kg)
                by_m3 = float(volume or 0) * float(tariff.price_per_m3 or 0)
                amount = round(max(by_kg, by_m3), 2)
            arrival = cp.created_at + timedelta(days=random.randint(3, 18))
            if arrival > NOW:
                arrival = NOW - timedelta(hours=random.randint(1, 48))
            client = random.choice(clients[:70])
            p = ParcelDushanbe(
                track_id=cp.track_id,
                client_id=client.id,
                status="received_dushanbe",
                weight_kg=Decimal(str(weight)),
                volume_m3=Decimal(str(volume)) if volume else None,
                delivery_method=method,
                warehouse_id=dushanbe_wh_id,
                amount_due=Decimal(str(amount)),
                tariff_snapshot=tariff.price_per_kg,
                has_china_registration=True,
                comment=random.choice(COMMENTS),
                notified_at=arrival,
                created_by=dushanbe_admin_id,
                created_at=arrival,
                updated_at=arrival,
            )
            dushanbe_parcels.append(p)
        db.add_all(dushanbe_parcels)
        await db.flush()
        print(f"Dushanbe parcels: {len(dushanbe_parcels)}")

        # ── Issue ~70% of dushanbe parcels ──
        to_issue = random.sample(dushanbe_parcels, int(len(dushanbe_parcels) * 0.70))
        by_client: dict[int, list] = {}
        for p in to_issue:
            by_client.setdefault(p.client_id, []).append(p)

        issuance_count = 0
        for cid, parcel_batch in by_client.items():
            random.shuffle(parcel_batch)
            batches = []
            i = 0
            while i < len(parcel_batch):
                size = random.randint(1, 5)
                batches.append(parcel_batch[i:i + size])
                i += size

            for batch in batches:
                total_weight = sum(float(p.weight_kg) for p in batch)
                total_amount = sum(float(p.amount_due or 0) for p in batch)
                issue_date = max(p.created_at for p in batch) + timedelta(
                    days=random.randint(1, 7)
                )
                if issue_date > NOW:
                    issue_date = NOW - timedelta(hours=random.randint(1, 24))
                pay_status = random.choices(["paid", "debt"], weights=[85, 15])[0]
                pay_method = random.choice(["cash", "transfer"]) if pay_status == "paid" else None

                order = IssuanceOrder(
                    client_id=cid,
                    staff_id=random.choice([owner_id, dushanbe_admin_id]),
                    total_weight=Decimal(str(round(total_weight, 3))),
                    total_amount=Decimal(str(round(total_amount, 2))),
                    payment_status=pay_status,
                    payment_method=pay_method,
                    issued_at=issue_date,
                )
                db.add(order)
                await db.flush()

                for p in batch:
                    tariff_rate = tariff_avia.price_per_kg if p.delivery_method == "avia" else tariff_truck.price_per_kg
                    item = IssuanceItem(
                        issuance_order_id=order.id,
                        parcel_id=p.id,
                        weight_kg=p.weight_kg,
                        volume_m3=p.volume_m3,
                        delivery_method=p.delivery_method,
                        tariff_applied=tariff_rate,
                        amount=p.amount_due or Decimal("0"),
                    )
                    db.add(item)
                    p.status = "issued"
                    p.updated_at = issue_date

                issuance_count += 1

        await db.flush()
        print(f"Issuance orders: {issuance_count}")

        # ── Unresolved parcels (8) ──
        unresolved = []
        for _ in range(8):
            track = rand_track()
            u = UnresolvedParcel(
                track_id=track,
                raw_tps_code=f"TPS{random.randint(900, 999)}",
                weight_kg=Decimal(str(round(random.uniform(0.5, 10.0), 2))),
                delivery_method=random.choice(["avia", "truck"]),
                resolved=False,
                created_by=dushanbe_admin_id,
                created_at=rand_date(NOW - timedelta(days=14), NOW),
            )
            unresolved.append(u)
        db.add_all(unresolved)
        print(f"Unresolved: {len(unresolved)}")

        # ── Audit logs (180) ──
        actions = [
            ("create_parcel_china", "parcel"),
            ("create_parcel_dushanbe", "parcel"),
            ("issue_parcels", "issuance"),
            ("update_status", "parcel"),
            ("update_client", "client"),
            ("block_client", "client"),
            ("create_tariff", "tariff"),
            ("update_warehouse", "warehouse"),
            ("update_setting", "setting"),
            ("reset_password", "staff"),
        ]
        audit_logs = []
        for _ in range(180):
            action, etype = random.choice(actions)
            log = AuditLog(
                staff_id=random.choice(staff_ids),
                action=action,
                entity_type=etype,
                entity_id=random.randint(1, 230),
                ip_address=random.choice(IPS),
                created_at=rand_date(START, NOW),
            )
            audit_logs.append(log)
        db.add_all(audit_logs)
        print(f"Audit logs: {len(audit_logs)}")

        await db.commit()
        print("\n=== Seed complete! ===")
        print(f"  Clients:    {len(clients)}")
        print(f"  China:      {len(china_parcels)}")
        print(f"  Dushanbe:   {len(dushanbe_parcels)}")
        print(f"  Issued:     {len(to_issue)} parcels in {issuance_count} orders")
        print(f"  Unresolved: {len(unresolved)}")
        print(f"  Audit:      {len(audit_logs)}")


if __name__ == "__main__":
    asyncio.run(main())
