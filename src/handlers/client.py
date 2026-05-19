import logging

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from src.config import CHANNEL_URL, CHANNEL_USERNAME
from src.db import (
    create_user,
    find_in_china,
    find_in_dushanbe,
    get_parcels_by_client,
    get_setting,
    get_user,
    get_warehouse,
    list_warehouses,
)
from src.fmt import (
    fmt_my_parcels,
    fmt_profile,
    fmt_track_result_client,
    fmt_warehouse_for_client,
    fmt_welcome,
)
from src.keyboards import (
    back_kb,
    client_main_kb,
    subscription_kb,
    warehouses_inline_kb,
)
from src.utils import validate_phone

log = logging.getLogger(__name__)
router = Router(name="client")


class RegStates(StatesGroup):
    name = State()
    phone = State()


class ClientStates(StatesGroup):
    check_track = State()


async def _check_sub(
    bot: Bot, user_id: int,
) -> bool:
    if not CHANNEL_USERNAME:
        return True
    try:
        member = await bot.get_chat_member(
            chat_id=CHANNEL_USERNAME, user_id=user_id,
        )
        return member.status in (
            "member", "administrator", "creator",
        )
    except Exception as e:
        log.warning(
            "Ошибка проверки подписки %s: %s",
            user_id, e,
        )
        return False


async def _show_sub_screen(msg: Message):
    url = CHANNEL_URL or None
    await msg.answer(
        "📢 Для продолжения подпишитесь на наш канал, "
        "затем нажмите «Проверить подписку».",
        reply_markup=subscription_kb(url),
    )


async def _ensure_sub(
    msg: Message, bot: Bot,
) -> bool:
    if await _check_sub(bot, msg.from_user.id):
        return True
    await _show_sub_screen(msg)
    return False


@router.callback_query(F.data == "check_sub")
async def on_check_sub(
    callback: CallbackQuery, state: FSMContext, bot: Bot,
):
    await callback.answer()
    uid = callback.from_user.id
    if await _check_sub(bot, uid):
        await callback.message.answer(
            "✅ Подписка подтверждена!"
        )
        await _start_client(
            callback.message, state, bot, uid,
        )
    else:
        await callback.message.answer(
            "❌ Подписка не найдена. "
            "Сначала подпишитесь на канал.",
            reply_markup=subscription_kb(
                CHANNEL_URL or None
            ),
        )


async def _start_client(
    msg: Message, state: FSMContext, bot: Bot,
    user_id: int | None = None,
):
    uid = user_id or msg.from_user.id
    user = await get_user(uid)
    if user:
        await state.update_data(
            registered=True,
            client_id=user.client_id,
        )
        await state.set_state(None)
        await msg.answer(
            f"С возвращением, {user.full_name}! 👋",
            reply_markup=client_main_kb(),
        )
        return
    await state.set_state(RegStates.name)
    await msg.answer(
        "👋 Добро пожаловать!\n\n"
        "Для регистрации укажите ваше ФИО:",
    )


async def client_start_handler(
    msg: Message, state: FSMContext, bot: Bot,
):
    if not await _ensure_sub(msg, bot):
        return
    await _start_client(msg, state, bot)


@router.message(RegStates.name)
async def on_reg_name(msg: Message, state: FSMContext):
    text = msg.text.strip()
    if len(text) < 3:
        await msg.answer(
            "⚠️ Слишком короткое имя. "
            "Введите полное ФИО:"
        )
        return
    await state.update_data(reg_name=text)
    await state.set_state(RegStates.phone)
    await msg.answer(
        "📱 Введите номер телефона:\n\n"
        "Формат: +992XXXXXXXXX или 9XXXXXXXX"
    )


@router.message(RegStates.phone)
async def on_reg_phone(msg: Message, state: FSMContext):
    phone = validate_phone(msg.text.strip())
    if not phone:
        await msg.answer(
            "⚠️ Неверный формат номера.\n\n"
            "Введите в формате:\n"
            "+992XXXXXXXXX (12 цифр)\n"
            "или 9XXXXXXXX (9 цифр)"
        )
        return
    data = await state.get_data()
    client_id = await create_user(
        msg.from_user.id, data["reg_name"], phone,
    )
    await state.update_data(
        registered=True, client_id=client_id,
    )
    await state.set_state(None)
    await msg.answer(
        fmt_welcome(client_id),
        reply_markup=client_main_kb(),
    )


@router.message(F.text == "⬅️ Назад в меню")
async def on_back(msg: Message, state: FSMContext):
    await state.set_state(None)
    await msg.answer(
        "🏠 Главное меню",
        reply_markup=client_main_kb(),
    )


@router.message(F.text == "👤 Мой профиль")
async def on_profile(msg: Message, bot: Bot):
    if not await _ensure_sub(msg, bot):
        return
    user = await get_user(msg.from_user.id)
    if user:
        await msg.answer(
            fmt_profile(user),
            reply_markup=client_main_kb(),
        )


@router.message(F.text == "📦 Мои посылки")
async def on_my_parcels(
    msg: Message, state: FSMContext, bot: Bot,
):
    if not await _ensure_sub(msg, bot):
        return
    data = await state.get_data()
    cid = data.get("client_id", "")
    parcels = await get_parcels_by_client(cid)
    await msg.answer(
        fmt_my_parcels(cid, parcels),
        reply_markup=client_main_kb(),
    )


@router.message(F.text == "🔎 Проверить трек")
async def on_check_track_start(
    msg: Message, state: FSMContext, bot: Bot,
):
    if not await _ensure_sub(msg, bot):
        return
    await state.set_state(ClientStates.check_track)
    await msg.answer(
        "🔎 Введите трек-код для проверки:",
        reply_markup=back_kb(),
    )


@router.message(ClientStates.check_track)
async def on_check_track_input(
    msg: Message, state: FSMContext,
):
    text = msg.text.strip()
    if text == "⬅️ Назад в меню":
        await state.set_state(None)
        await msg.answer(
            "🏠 Главное меню",
            reply_markup=client_main_kb(),
        )
        return
    in_china = await find_in_china(text)
    dushanbe = await find_in_dushanbe(text)
    await msg.answer(
        fmt_track_result_client(
            text.upper(), in_china,
            dushanbe is not None,
        ),
        reply_markup=back_kb(),
    )


@router.message(F.text == "🏬 Адреса складов")
async def on_warehouses(msg: Message, bot: Bot):
    if not await _ensure_sub(msg, bot):
        return
    whs = await list_warehouses()
    if not whs:
        await msg.answer(
            "🏬 Складов пока нет.",
            reply_markup=client_main_kb(),
        )
        return
    await msg.answer(
        "🏬 Выберите склад:",
        reply_markup=warehouses_inline_kb(whs),
    )


@router.callback_query(F.data.startswith("wh_"))
async def on_warehouse_select(
    callback: CallbackQuery,
    state: FSMContext, bot: Bot,
):
    await callback.answer()
    wid = int(callback.data.split("_")[1])
    w = await get_warehouse(wid)
    if not w:
        await callback.message.answer("❌ Склад не найден.")
        return
    data = await state.get_data()
    client_id = data.get("client_id", "ВАШ_ID")
    user = await get_user(callback.from_user.id)
    name = user.full_name if user else "Ваше Имя"
    await callback.message.answer(
        fmt_warehouse_for_client(w, client_id, name),
        reply_markup=client_main_kb(),
    )


@router.message(F.text == "💰 Прайс-лист")
async def on_tariffs(msg: Message, bot: Bot):
    if not await _ensure_sub(msg, bot):
        return
    text = await get_setting("tariffs")
    await msg.answer(
        text or "💰 Тарифы пока не указаны.",
        reply_markup=client_main_kb(),
    )


@router.message(F.text == "🆘 Поддержка")
async def on_support(msg: Message, bot: Bot):
    if not await _ensure_sub(msg, bot):
        return
    text = await get_setting("support")
    await msg.answer(
        text or "🆘 Контакт поддержки пока не указан.",
        reply_markup=client_main_kb(),
    )