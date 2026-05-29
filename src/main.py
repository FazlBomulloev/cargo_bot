import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import BaseFilter, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message

from src.config import BOT_TOKEN
from src.db import (
    get_parcels_for_reminder,
    get_user_by_client_id,
    init_db,
    is_admin,
    mark_reminder_sent,
)
from src.fmt import fmt_parcel_reminder
from src.handlers.admin import (
    admin_start,
    router as admin_router,
)
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

REMINDER_CHECK_INTERVAL = 3600  # секунд (1 час)


class IsAdminMode(BaseFilter):
    async def __call__(
        self,
        event: Message | CallbackQuery,
        state: FSMContext,
    ) -> bool:
        data = await state.get_data()
        return data.get("admin_mode", False)


class IsClientMode(BaseFilter):
    async def __call__(
        self,
        event: Message | CallbackQuery,
        state: FSMContext,
    ) -> bool:
        data = await state.get_data()
        return not data.get("admin_mode", False)


@dp.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    if await is_admin(uid):
        await state.update_data(admin_mode=True)
        await admin_start(msg, state)
    else:
        await state.update_data(admin_mode=False)
        await client_start_handler(msg, state, bot)


admin_router.message.filter(IsAdminMode())
admin_router.callback_query.filter(IsAdminMode())
client_router.message.filter(IsClientMode())
client_router.callback_query.filter(IsClientMode())

dp.include_router(admin_router)
dp.include_router(client_router)


async def reminder_loop():
    """Фоновая таска: проверяет посылки,
    ожидающие получения > 7 дней,
    отправляет повторное уведомление.
    """
    while True:
        try:
            parcels = await get_parcels_for_reminder()
            for p in parcels:
                user = await get_user_by_client_id(
                    p.client_id,
                )
                if not user:
                    continue
                lang = user.lang or "ru"
                try:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=fmt_parcel_reminder(
                            p.track_code, lang,
                        ),
                    )
                    await mark_reminder_sent(
                        p.track_code,
                    )
                    log.info(
                        "Напоминание отправлено: "
                        "%s → %s",
                        p.track_code,
                        user.telegram_id,
                    )
                except Exception as e:
                    log.warning(
                        "Не удалось отправить "
                        "напоминание %s: %s",
                        user.telegram_id, e,
                    )
        except Exception as e:
            log.error(
                "Ошибка в reminder_loop: %s", e,
            )
        await asyncio.sleep(REMINDER_CHECK_INTERVAL)


async def main():
    if not BOT_TOKEN:
        raise ValueError(
            "В .env не указан BOT_TOKEN",
        )
    await init_db()
    log.info("Бот запущен 🚀")
    asyncio.create_task(reminder_loop())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())