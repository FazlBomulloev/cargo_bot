"""
Seed script: generates 3 months of realistic demo data.
Run:  python seed_demo.py   (from backend/ directory, with .env loaded)
"""
import asyncio
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal

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
from app.models.setting import Setting
from app.utils.security import hash_password

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
        # ── Staff ──
        owner = StaffUser(
            full_name="Owner", login="owner",
            password_hash=hash_password("admin123"), role="owner",
            created_at=START - timedelta(days=5),
        )
        china_admin = StaffUser(
            full_name="Алишер Каримов", login="alisher",
            password_hash=hash_password("china123"), role="admin_china",
            created_at=START - timedelta(days=3),
        )
        dushanbe_admin = StaffUser(
            full_name="Бахром Назаров", login="bakhrom",
            password_hash=hash_password("dushanbe123"), role="admin_dushanbe",
            created_at=START - timedelta(days=3),
        )
        db.add_all([owner, china_admin, dushanbe_admin])
        await db.flush()
        staff_ids = [owner.id, china_admin.id, dushanbe_admin.id]
        print(f"Staff: {len(staff_ids)} users")

        # ── Warehouses ──
        wh_china1 = Warehouse(
            name="Склад Иву", type="china", country="Китай", city="Иву",
            phone="19878638724", region="浙江省 金华市 义乌市",
            address="洪华小区26幢2单元",
        )
        wh_china2 = Warehouse(
            name="Склад Урумчи (Авиа)", type="china", country="Китай", city="Урумчи",
            phone="13999210571", region="新疆维吾尔自治区 乌鲁木齐市 天山区",
            address="延安路662号边疆宾馆19TPS号库房",
        )
        wh_dushanbe = Warehouse(
            name="Склад Душанбе", type="dushanbe", country="Таджикистан", city="Душанбе",
            phone="+992900000000", region="Душанбе",
            address="ул. Исмоили Сомони 42",
        )
        wh_pvz = Warehouse(
            name="ПВЗ Центр", type="pvz", country="Таджикистан", city="Душанбе",
            phone="+992917001122", region="Душанбе",
            address="пр. Рудаки 105",
        )
        db.add_all([wh_china1, wh_china2, wh_dushanbe, wh_pvz])
        await db.flush()
        china_wh_ids = [wh_china1.id, wh_china2.id]
        print("Warehouses: 4")

        # ── Tariffs ──
        tariff_avia = Tariff(
            method="avia", price_per_kg=Decimal("10.00"),
            created_by=owner.id, is_active=True,
            created_at=START - timedelta(days=2),
        )
        tariff_truck = Tariff(
            method="truck", price_per_kg=Decimal("2.50"),
            price_per_m3=Decimal("280.00"),
            created_by=owner.id, is_active=True,
            created_at=START - timedelta(days=2),
        )
        db.add_all([tariff_avia, tariff_truck])
        await db.flush()
        print("Tariffs: avia $10/kg, truck $2.5/kg")

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
            c = Client(
                telegram_id=tg_id,
                tps_code=f"TPS{i + 1:03d}",
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

        # ── China parcels (300 — some have no dushanbe counterpart) ──
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
                created_by=china_admin.id,
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
                warehouse_id=wh_dushanbe.id,
                amount_due=Decimal(str(amount)),
                tariff_snapshot=tariff.price_per_kg,
                has_china_registration=True,
                comment=random.choice(COMMENTS),
                created_by=dushanbe_admin.id,
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
                    staff_id=random.choice([owner.id, dushanbe_admin.id]),
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

        # ── Some parcels ready_to_issue, some still received ──
        not_issued = [p for p in dushanbe_parcels if p.status == "received_dushanbe"]
        for p in random.sample(not_issued, min(15, len(not_issued))):
            p.status = "ready_to_issue"
            p.updated_at = NOW - timedelta(hours=random.randint(1, 72))
        for p in random.sample(not_issued, min(3, len(not_issued))):
            p.status = "problem"
            p.comment = random.choice(["Повреждена упаковка", "Неверный вес", "Запрещённый товар"])
            p.updated_at = NOW - timedelta(hours=random.randint(1, 48))

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
                created_by=dushanbe_admin.id,
                created_at=rand_date(NOW - timedelta(days=14), NOW),
            )
            unresolved.append(u)
        db.add_all(unresolved)
        print(f"Unresolved: {len(unresolved)}")

        # ── Audit logs (150+) ──
        actions = [
            ("create_parcel_china", "parcel"),
            ("create_parcel_dushanbe", "parcel"),
            ("issue_parcels", "issuance"),
            ("update_status", "parcel"),
            ("create_client", "client"),
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

        # ── Settings ──
        db.add(Setting(key="tariffs", value="Авиа: $10/кг\nФура: $2.5/кг, $280/м³"))
        db.add(Setting(key="support", value="Поддержка: @tps_support\nТел: +992 90 000 00 00"))

        await db.commit()
        print("\n=== Seed complete! ===")
        print(f"  Clients:    {len(clients)}")
        print(f"  China:      {len(china_parcels)}")
        print(f"  Dushanbe:   {len(dushanbe_parcels)}")
        print(f"  Issued:     {len(to_issue)} parcels in {issuance_count} orders")
        print(f"  Unresolved: {len(unresolved)}")
        print(f"  Audit:      {len(audit_logs)}")
        print(f"\n  Login: owner / admin123")
        print(f"         alisher / china123")
        print(f"         bakhrom / dushanbe123")


if __name__ == "__main__":
    asyncio.run(main())
