from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from src.texts import get_text


def _kb(
    buttons: list[list[str]],
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=b) for b in row]
            for row in buttons
        ],
        resize_keyboard=True,
    )


# ── Выбор языка ──

def language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🇷🇺 Русский",
                callback_data="lang_ru",
            ),
            InlineKeyboardButton(
                text="🇹🇯 Тоҷикӣ",
                callback_data="lang_tj",
            ),
        ],
    ])


# ── Клиент ──

def client_main_kb(
    lang: str = "ru",
) -> ReplyKeyboardMarkup:
    return _kb([
        [
            get_text("btn_my_parcels", lang),
            get_text("btn_check_track", lang),
        ],
        [
            get_text("btn_warehouses", lang),
            get_text("btn_price", lang),
        ],
        [
            get_text("btn_profile", lang),
            get_text("btn_support", lang),
        ],
    ])


def back_kb(
    lang: str = "ru",
) -> ReplyKeyboardMarkup:
    return _kb([
        [get_text("btn_back", lang)],
    ])


def profile_edit_kb(
    lang: str = "ru",
) -> InlineKeyboardMarkup:
    if lang == "tj":
        name_label = "✏️ Иваз кардани ном"
        phone_label = "📱 Иваз кардани рақам"
    else:
        name_label = "✏️ Изменить ФИО"
        phone_label = "📱 Изменить телефон"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=name_label,
            callback_data="edit_profile_name",
        )],
        [InlineKeyboardButton(
            text=phone_label,
            callback_data="edit_profile_phone",
        )],
    ])


# ── Склады (inline) ──

def warehouses_inline_kb(
    warehouses: list,
) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"📍 {w.name}",
            callback_data=f"wh_{w.id}",
        )]
        for w in warehouses
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=buttons,
    )


# ── Подписка ──

def subscription_kb(
    channel_url: str | None,
) -> InlineKeyboardMarkup:
    buttons = []
    if channel_url:
        buttons.append([InlineKeyboardButton(
            text="📢 Подписаться на канал",
            url=channel_url,
        )])
    buttons.append([InlineKeyboardButton(
        text="✅ Проверить подписку",
        callback_data="check_sub",
    )])
    return InlineKeyboardMarkup(
        inline_keyboard=buttons,
    )
