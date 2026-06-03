import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from src.config import BOT_TOKEN
from src.db import (
    get_unnotified_parcels,
    init_db,
    mark_notified,
)
from src.fmt import fmt_parcel_arrived
from src.handlers.client import (
    client_start_handler,
    router as client_router,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

dp = Dispatcher(storage=MemoryStorage())
bot = Bot(token=BOT_TOKEN)

NOTIFY_CHECK_INTERVAL = 60


@dp.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await client_start_handler(msg, state, bot)


dp.include_router(client_router)


async def notification_loop():
    while True:
        try:
            parcels = await get_unnotified_parcels()
            for p in parcels:
                try:
                    await bot.send_message(
                        chat_id=p["telegram_id"],
                        text=fmt_parcel_arrived(
                            p["track_id"], p["lang"],
                        ),
                    )
                    await mark_notified(p["track_id"])
                    log.info(
                        "Уведомление отправлено: "
                        "%s -> %s",
                        p["track_id"],
                        p["telegram_id"],
                    )
                except Exception as e:
                    log.warning(
                        "Не удалось отправить "
                        "уведомление %s: %s",
                        p["telegram_id"], e,
                    )
        except Exception as e:
            log.error(
                "Ошибка в notification_loop: %s", e,
            )
        await asyncio.sleep(NOTIFY_CHECK_INTERVAL)


async def main():
    if not BOT_TOKEN:
        raise ValueError(
            "В .env не указан BOT_TOKEN",
        )
    await init_db()
    log.info("Бот запущен")
    asyncio.create_task(notification_loop())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
