import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import BaseFilter, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message

from src.config import BOT_TOKEN
from src.db import init_db, is_admin
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


async def main():
    if not BOT_TOKEN:
        raise ValueError("В .env не указан BOT_TOKEN")
    await init_db()
    log.info("Бот запущен 🚀")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())