import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client

RESERVED_NUMBERS = {7, 111, 222, 333, 444, 555, 666, 777, 888, 999}


def format_tps_code(num: int) -> str:
    if num < 1000:
        return f"TPS{num:03d}"
    return f"TPS{num}"


def parse_tps_number(code: str) -> int | None:
    m = re.fullmatch(r"TPS(\d+)", (code or "").strip().upper())
    return int(m.group(1)) if m else None


async def generate_tps_code(session: AsyncSession) -> str:
    result = await session.execute(select(Client.tps_code))
    used = {n for (code,) in result.all() if (n := parse_tps_number(code)) is not None}
    num = 1
    while num in used or num in RESERVED_NUMBERS:
        num += 1
    return format_tps_code(num)
