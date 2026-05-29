import logging

from aiogram import Bot, F, Router
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
    update_user_field,
    update_user_lang,
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
    language_kb,
    profile_edit_kb,
    subscription_kb,
    warehouses_inline_kb,
)
from src.texts import get_all_texts, get_text
from src.utils import validate_phone

log = logging.getLogger(__name__)
router = Router(name="client")

# Сеты для фильтров — все варианты перевода
_BTN_PARCELS = get_all_texts("btn_my_parcels")
_BTN_TRACK = get_all_texts("btn_check_track")
_BTN_WH = get_all_texts("btn_warehouses")
_BTN_PRICE = get_all_texts("btn_price")
_BTN_PROFILE = get_all_texts("btn_profile")
_BTN_SUPPORT = get_all_texts("btn_support")
_BTN_BACK = get_all_texts("btn_back")


class RegStates(StatesGroup):
    name = State()
    phone = State()


class ClientStates(StatesGroup):
    check_track = State()


class EditProfileStates(StatesGroup):
    edit_name = State()
    edit_phone = State()


# ── Helpers ──

async def _get_lang(state: FSMContext) -> str:
    data = await state.get_data()
    return data.get("lang", "ru")


async def _check_sub(
    bot: Bot, user_id: int,
) -> bool:
    if not CHANNEL_USERNAME:
        return True
    try:
        member = await bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id,
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


async def _show_sub_screen(
    msg: Message, lang: str,
):
    url = CHANNEL_URL or None
    await msg.answer(
        get_text("subscription_required", lang),
        reply_markup=subscription_kb(url),
    )


async def _ensure_sub(
    msg: Message, bot: Bot, lang: str,
) -> bool:
    if await _check_sub(bot, msg.from_user.id):
        return True
    await _show_sub_screen(msg, lang)
    return False


# ── Выбор языка ──

async def client_start_handler(
    msg: Message, state: FSMContext, bot: Bot,
):
    """Точка входа для клиента из /start."""
    uid = msg.from_user.id
    user = await get_user(uid)
    if user:
        lang = user.lang or "ru"
        await state.update_data(
            registered=True,
            client_id=user.client_id,
            lang=lang,
        )
        if not await _ensure_sub(msg, bot, lang):
            return
        await state.set_state(None)
        await msg.answer(
            get_text(
                "welcome_back", lang,
            ).format(name=user.full_name),
            reply_markup=client_main_kb(lang),
        )
        return
    await msg.answer(
        get_text("choose_language", "ru"),
        reply_markup=language_kb(),
    )


@router.callback_query(F.data.startswith("lang_"))
async def on_lang_select(
    cb: CallbackQuery, state: FSMContext, bot: Bot,
):
    await cb.answer()
    lang = cb.data.split("_")[1]
    await state.update_data(lang=lang)

    uid = cb.from_user.id
    user = await get_user(uid)
    if user:
        await update_user_lang(uid, lang)
        await state.update_data(
            registered=True,
            client_id=user.client_id,
        )
        await state.set_state(None)
        await cb.message.answer(
            get_text(
                "welcome_back", lang,
            ).format(name=user.full_name),
            reply_markup=client_main_kb(lang),
        )
        return

    if not await _check_sub(bot, uid):
        await _show_sub_screen(cb.message, lang)
        return

    await state.set_state(RegStates.name)
    await cb.message.answer(
        get_text("welcome", lang),
    )


@router.callback_query(F.data == "check_sub")
async def on_check_sub(
    cb: CallbackQuery, state: FSMContext, bot: Bot,
):
    await cb.answer()
    uid = cb.from_user.id
    lang = await _get_lang(state)
    if await _check_sub(bot, uid):
        await cb.message.answer(
            get_text("subscription_ok", lang),
        )
        user = await get_user(uid)
        if user:
            await state.update_data(
                registered=True,
                client_id=user.client_id,
            )
            await state.set_state(None)
            await cb.message.answer(
                get_text(
                    "welcome_back", lang,
                ).format(name=user.full_name),
                reply_markup=client_main_kb(lang),
            )
        else:
            await state.set_state(RegStates.name)
            await cb.message.answer(
                get_text("welcome", lang),
            )
    else:
        await cb.message.answer(
            get_text(
                "subscription_not_found", lang,
            ),
            reply_markup=subscription_kb(
                CHANNEL_URL or None
            ),
        )


# ── Регистрация ──

@router.message(RegStates.name)
async def on_reg_name(
    msg: Message, state: FSMContext,
):
    lang = await _get_lang(state)
    text = msg.text.strip()
    if len(text) < 3:
        await msg.answer(
            get_text("name_too_short", lang),
        )
        return
    await state.update_data(reg_name=text)
    await state.set_state(RegStates.phone)
    await msg.answer(
        get_text("enter_phone", lang),
    )


@router.message(RegStates.phone)
async def on_reg_phone(
    msg: Message, state: FSMContext,
):
    lang = await _get_lang(state)
    phone = validate_phone(msg.text.strip())
    if not phone:
        await msg.answer(
            get_text("phone_invalid", lang),
        )
        return
    data = await state.get_data()
    client_id = await create_user(
        msg.from_user.id,
        data["reg_name"],
        phone,
        lang,
    )
    await state.update_data(
        registered=True, client_id=client_id,
    )
    await state.set_state(None)
    await msg.answer(
        fmt_welcome(client_id, lang),
        reply_markup=client_main_kb(lang),
    )


# ── Навигация ──

@router.message(F.text.in_(_BTN_BACK))
async def on_back(msg: Message, state: FSMContext):
    lang = await _get_lang(state)
    await state.set_state(None)
    await msg.answer(
        get_text("menu", lang),
        reply_markup=client_main_kb(lang),
    )


# ── Профиль ──

@router.message(F.text.in_(_BTN_PROFILE))
async def on_profile(
    msg: Message, state: FSMContext, bot: Bot,
):
    lang = await _get_lang(state)
    if not await _ensure_sub(msg, bot, lang):
        return
    user = await get_user(msg.from_user.id)
    if user:
        await msg.answer(
            fmt_profile(user, lang),
            reply_markup=profile_edit_kb(lang),
        )


@router.callback_query(F.data == "edit_profile_name")
async def on_edit_name_start(
    cb: CallbackQuery, state: FSMContext,
):
    await cb.answer()
    lang = await _get_lang(state)
    await state.set_state(EditProfileStates.edit_name)
    await cb.message.answer(
        get_text("edit_name_prompt", lang),
        reply_markup=back_kb(lang),
    )


@router.message(EditProfileStates.edit_name)
async def on_edit_name_input(
    msg: Message, state: FSMContext,
):
    lang = await _get_lang(state)
    text = msg.text.strip()
    if text in _BTN_BACK:
        await state.set_state(None)
        await msg.answer(
            get_text("menu", lang),
            reply_markup=client_main_kb(lang),
        )
        return
    if len(text) < 3:
        await msg.answer(
            get_text("name_too_short", lang),
        )
        return
    await update_user_field(
        msg.from_user.id, "full_name", text,
    )
    await state.set_state(None)
    user = await get_user(msg.from_user.id)
    await msg.answer(
        get_text("profile_updated", lang),
    )
    await msg.answer(
        fmt_profile(user, lang),
        reply_markup=profile_edit_kb(lang),
    )


@router.callback_query(F.data == "edit_profile_phone")
async def on_edit_phone_start(
    cb: CallbackQuery, state: FSMContext,
):
    await cb.answer()
    lang = await _get_lang(state)
    await state.set_state(EditProfileStates.edit_phone)
    await cb.message.answer(
        get_text("edit_phone_prompt", lang),
        reply_markup=back_kb(lang),
    )


@router.message(EditProfileStates.edit_phone)
async def on_edit_phone_input(
    msg: Message, state: FSMContext,
):
    lang = await _get_lang(state)
    text = msg.text.strip()
    if text in _BTN_BACK:
        await state.set_state(None)
        await msg.answer(
            get_text("menu", lang),
            reply_markup=client_main_kb(lang),
        )
        return
    phone = validate_phone(text)
    if not phone:
        await msg.answer(
            get_text("phone_invalid", lang),
        )
        return
    await update_user_field(
        msg.from_user.id, "phone", phone,
    )
    await state.set_state(None)
    user = await get_user(msg.from_user.id)
    await msg.answer(
        get_text("profile_updated", lang),
    )
    await msg.answer(
        fmt_profile(user, lang),
        reply_markup=profile_edit_kb(lang),
    )


# ── Мои посылки ──

@router.message(F.text.in_(_BTN_PARCELS))
async def on_my_parcels(
    msg: Message, state: FSMContext, bot: Bot,
):
    lang = await _get_lang(state)
    if not await _ensure_sub(msg, bot, lang):
        return
    data = await state.get_data()
    cid = data.get("client_id", "")
    parcels = await get_parcels_by_client(cid)
    await msg.answer(
        fmt_my_parcels(cid, parcels, lang),
        reply_markup=client_main_kb(lang),
    )


# ── Проверка трека ──

@router.message(F.text.in_(_BTN_TRACK))
async def on_check_track_start(
    msg: Message, state: FSMContext, bot: Bot,
):
    lang = await _get_lang(state)
    if not await _ensure_sub(msg, bot, lang):
        return
    await state.set_state(ClientStates.check_track)
    await msg.answer(
        get_text("enter_track", lang),
        reply_markup=back_kb(lang),
    )


@router.message(ClientStates.check_track)
async def on_check_track_input(
    msg: Message, state: FSMContext,
):
    lang = await _get_lang(state)
    text = msg.text.strip()
    if text in _BTN_BACK:
        await state.set_state(None)
        await msg.answer(
            get_text("menu", lang),
            reply_markup=client_main_kb(lang),
        )
        return
    in_china = await find_in_china(text)
    dushanbe = await find_in_dushanbe(text)
    await msg.answer(
        fmt_track_result_client(
            text.upper(), in_china,
            dushanbe, lang,
        ),
        reply_markup=back_kb(lang),
    )


# ── Склады ──

@router.message(F.text.in_(_BTN_WH))
async def on_warehouses(
    msg: Message, state: FSMContext, bot: Bot,
):
    lang = await _get_lang(state)
    if not await _ensure_sub(msg, bot, lang):
        return
    whs = await list_warehouses()
    if not whs:
        await msg.answer(
            get_text("no_warehouses", lang),
            reply_markup=client_main_kb(lang),
        )
        return
    await msg.answer(
        get_text("warehouses_title", lang),
        reply_markup=warehouses_inline_kb(whs),
    )


@router.callback_query(F.data.startswith("wh_"))
async def on_warehouse_select(
    cb: CallbackQuery,
    state: FSMContext, bot: Bot,
):
    await cb.answer()
    lang = await _get_lang(state)
    wid = int(cb.data.split("_")[1])
    w = await get_warehouse(wid)
    if not w:
        await cb.message.answer(
            get_text("warehouse_not_found", lang),
        )
        return
    data = await state.get_data()
    client_id = data.get("client_id", "ВАШ_ID")
    user = await get_user(cb.from_user.id)
    name = user.full_name if user else "Ваше Имя"
    await cb.message.answer(
        fmt_warehouse_for_client(
            w, client_id, name,
        ),
        reply_markup=client_main_kb(lang),
    )


# ── Тарифы ──

@router.message(F.text.in_(_BTN_PRICE))
async def on_tariffs(
    msg: Message, state: FSMContext, bot: Bot,
):
    lang = await _get_lang(state)
    if not await _ensure_sub(msg, bot, lang):
        return
    text = await get_setting("tariffs")
    if text:
        await msg.answer(
            text,
            reply_markup=client_main_kb(lang),
        )
    else:
        await msg.answer(
            get_text("price", lang),
            reply_markup=client_main_kb(lang),
        )


# ── Поддержка ──

@router.message(F.text.in_(_BTN_SUPPORT))
async def on_support(
    msg: Message, state: FSMContext, bot: Bot,
):
    lang = await _get_lang(state)
    if not await _ensure_sub(msg, bot, lang):
        return
    text = await get_setting("support")
    if text:
        await msg.answer(
            text,
            reply_markup=client_main_kb(lang),
        )
    else:
        await msg.answer(
            get_text("support", lang),
            reply_markup=client_main_kb(lang),
        )