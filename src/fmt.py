from src.texts import get_text


def fmt_profile(user, lang: str = "ru") -> str:
    title = get_text("profile_title", lang)
    return (
        "┌─────────────────────────┐\n"
        f"│        {title}        │\n"
        "├─────────────────────────┤\n"
        f"│ 🆔  {user.client_id}\n"
        f"│ 👤  {user.full_name}\n"
        f"│ 📱  {user.phone}\n"
        "└─────────────────────────┘"
    )


def fmt_welcome(client_id: str, lang: str = "ru") -> str:
    if lang == "tj":
        return (
            "╔══════════════════════════╗\n"
            "║   🎉  ХУШ ОМАДЕД!         ║\n"
            "╠══════════════════════════╣\n"
            "║                          ║\n"
            "║  Сабти ном анҷом ёфт!    ║\n"
            "║                          ║\n"
            f"║  ID-и шумо:  {client_id}     \n"
            "║                          ║\n"
            "║  📌 Ин рамзро ҳангоми    ║\n"
            "║  фиристодани посылкаҳо    ║\n"
            "║  нишон диҳед              ║\n"
            "║                          ║\n"
            "╚══════════════════════════╝"
        )
    return (
        "╔══════════════════════════╗\n"
        "║   🎉  ДОБРО ПОЖАЛОВАТЬ!   ║\n"
        "╠══════════════════════════╣\n"
        "║                          ║\n"
        "║  Регистрация завершена!   ║\n"
        "║                          ║\n"
        f"║  Ваш ID:  {client_id}     \n"
        "║                          ║\n"
        "║  📌 Укажите этот код при  ║\n"
        "║  отправке посылок         ║\n"
        "║                          ║\n"
        "╚══════════════════════════╝"
    )


def _status_text(
    status: str, lang: str = "ru",
) -> str:
    if status == "received":
        return get_text("status_received", lang)
    return get_text("status_waiting", lang)


def _format_date(dt) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%d.%m.%Y")


def fmt_parcel_arrived(
    track_code: str, lang: str = "ru",
) -> str:
    title = get_text("parcel_arrived_title", lang)
    body = get_text("parcel_arrived_body", lang)
    return (
        "┌─────────────────────────┐\n"
        f"│   {title}   │\n"
        "├─────────────────────────┤\n"
        f"│ 📦  Трек: {track_code}\n"
        "│ 📍  Склад: Душанбе\n"
        "│\n"
        f"│ {body}\n"
        "└─────────────────────────┘"
    )


def fmt_parcel_reminder(
    track_code: str, lang: str = "ru",
) -> str:
    title = get_text("parcel_reminder_title", lang)
    body = get_text("parcel_reminder_body", lang)
    return (
        "┌─────────────────────────┐\n"
        f"│   {title}   │\n"
        "├─────────────────────────┤\n"
        f"│ 📦  Трек: {track_code}\n"
        "│\n"
        f"│ {body}\n"
        "└─────────────────────────┘"
    )


def fmt_track_result_admin(
    track_code: str,
    in_china: bool,
    dushanbe_info,
    user_info,
) -> str:
    lines = [
        "┌─────────────────────────┐",
        "│   🔎  РЕЗУЛЬТАТ ПОИСКА   │",
        "├─────────────────────────┤",
        f"│ 📦  Трек: {track_code}",
    ]
    if dushanbe_info and user_info:
        status = _status_text(dushanbe_info.status)
        date = _format_date(dushanbe_info.arrived_at)
        lines += [
            f"│ 📍  Статус: {status}",
            f"│ 📅  Дата: {date}",
            "│",
            f"│ 🆔  Клиент: {user_info.client_id}",
            f"│ 👤  {user_info.full_name}",
            f"│ 📱  {user_info.phone}",
        ]
    elif dushanbe_info:
        status = _status_text(dushanbe_info.status)
        date = _format_date(dushanbe_info.arrived_at)
        lines += [
            f"│ 📍  Статус: {status}",
            f"│ 📅  Дата: {date}",
            f"│ 🆔  Клиент: {dushanbe_info.client_id}",
            "│ ⚠️  Клиент не найден в базе",
        ]
    elif in_china:
        lines.append(
            "│ 📍  Статус: на складе в Китае 🇨🇳"
        )
    else:
        lines.append("│ ❌  Трек-код не найден")
    lines.append("└─────────────────────────┘")
    return "\n".join(lines)


def fmt_client_info_admin(
    user, parcels: list,
) -> str:
    lines = [
        "┌─────────────────────────┐",
        "│   👤  КАРТОЧКА КЛИЕНТА   │",
        "├─────────────────────────┤",
        f"│ 🆔  {user.client_id}",
        f"│ 👤  {user.full_name}",
        f"│ 📱  {user.phone}",
        f"│ 🔗  TG ID: {user.telegram_id}",
    ]
    if parcels:
        lines.append("│")
        lines.append("│ 📦 Посылки:")
        for p in parcels:
            status = _status_text(p.status)
            date = _format_date(p.arrived_at)
            lines.append(
                f"│   {p.track_code}  "
                f"{date}  {status}"
            )
    else:
        lines.append("│")
        lines.append("│ 📦 Посылок пока нет")
    lines.append("└─────────────────────────┘")
    return "\n".join(lines)


def fmt_track_result_client(
    track_code: str,
    in_china: bool,
    dushanbe_info,
    lang: str = "ru",
) -> str:
    title = get_text("track_title", lang)
    lines = [
        "┌─────────────────────────┐",
        f"│   {title}   │",
        "├─────────────────────────┤",
        f"│ 📦  Трек: {track_code}",
    ]
    if dushanbe_info:
        if dushanbe_info.status == "received":
            lines.append(
                "│ "
                + get_text(
                    "track_in_dushanbe_received", lang
                )
            )
        else:
            lines.append(
                "│ "
                + get_text("track_in_dushanbe", lang)
            )
            lines.append(
                "│ "
                + get_text("track_can_pickup", lang)
            )
    elif in_china:
        lines.append(
            "│ " + get_text("track_in_china", lang)
        )
        lines.append(
            "│ "
            + get_text("track_wait_delivery", lang)
        )
    else:
        lines.append(
            "│ " + get_text("track_not_found", lang)
        )
    lines.append("└─────────────────────────┘")
    return "\n".join(lines)


def fmt_my_parcels(
    client_id: str,
    parcels: list,
    lang: str = "ru",
) -> str:
    title = get_text("my_parcels_title", lang)
    lines = [
        "┌─────────────────────────┐",
        f"│     {title}      │",
        "├─────────────────────────┤",
        f"│ 🆔  {client_id}",
    ]
    if parcels:
        lines.append("│")
        for p in parcels:
            status = _status_text(p.status, lang)
            date = _format_date(p.arrived_at)
            lines.append(
                f"│ {p.track_code}  "
                f"{date}  {status}"
            )
    else:
        lines.append("│")
        lines.append(
            "│ " + get_text("no_parcels", lang)
        )
    lines.append("└─────────────────────────┘")
    return "\n".join(lines)


def fmt_upload_result(
    label: str, total: int, added: int,
) -> str:
    return (
        "┌─────────────────────────┐\n"
        f"│  📥  {label}\n"
        "├─────────────────────────┤\n"
        f"│ 📊  Всего строк: {total}\n"
        f"│ ✅  Добавлено: {added}\n"
        f"│ ⏭️  Пропущено: {total - added}\n"
        "└─────────────────────────┘"
    )


def fmt_warehouse_for_client(
    w, client_id: str, name: str,
) -> str:
    return (
        f"📍 {w.name}\n"
        "━━━━━━━━━━━━━━━\n"
        "Заполните адрес в Pinduoduo:\n\n"
        f"👤 {name}\n"
        f"📞 {w.phone}\n"
        f"🌏 {w.region}\n"
        f"📍 {w.address} {client_id}"
    )


def fmt_warehouse_admin(w) -> str:
    return (
        f"🏬 [{w.id}] {w.name}\n"
        f"📞 {w.phone}\n"
        f"🌏 {w.region}\n"
        f"📍 {w.address}"
    )


def fmt_warehouse_list_admin(
    warehouses: list,
) -> str:
    if not warehouses:
        return "🏬 Складов пока нет."
    lines = ["🏬 Список складов:\n"]
    for w in warehouses:
        lines.append(
            f"[{w.id}] {w.name} — {w.phone}"
        )
    return "\n".join(lines)