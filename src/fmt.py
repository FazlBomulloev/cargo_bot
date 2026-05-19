def fmt_profile(user) -> str:
    return (
        "┌─────────────────────────┐\n"
        "│        👤  ПРОФИЛЬ        │\n"
        "├─────────────────────────┤\n"
        f"│ 🆔  {user.client_id}\n"
        f"│ 👤  {user.full_name}\n"
        f"│ 📱  {user.phone}\n"
        "└─────────────────────────┘"
    )


def fmt_welcome(client_id: str) -> str:
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


def fmt_parcel_arrived(track_code: str) -> str:
    return (
        "┌─────────────────────────┐\n"
        "│   📬  ПОСЫЛКА ПРИБЫЛА!   │\n"
        "├─────────────────────────┤\n"
        f"│ 📦  Трек: {track_code}\n"
        "│ 📍  Склад: Душанбе\n"
        "│\n"
        "│ Ваша посылка доступна\n"
        "│ для получения!\n"
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
        lines += [
            "│ 📍  Статус: в Душанбе ✅",
            "│",
            f"│ 🆔  Клиент: {user_info.client_id}",
            f"│ 👤  {user_info.full_name}",
            f"│ 📱  {user_info.phone}",
        ]
    elif dushanbe_info:
        lines += [
            "│ 📍  Статус: в Душанбе ✅",
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


def fmt_client_info_admin(user, parcels: dict) -> str:
    lines = [
        "┌─────────────────────────┐",
        "│   👤  КАРТОЧКА КЛИЕНТА   │",
        "├─────────────────────────┤",
        f"│ 🆔  {user.client_id}",
        f"│ 👤  {user.full_name}",
        f"│ 📱  {user.phone}",
        f"│ 🔗  TG ID: {user.telegram_id}",
    ]
    if parcels["dushanbe"]:
        lines.append("│")
        lines.append("│ 📦 Посылки в Душанбе:")
        for t in parcels["dushanbe"]:
            lines.append(f"│   • {t}")
    else:
        lines.append("│")
        lines.append("│ 📦 Посылок пока нет")
    lines.append("└─────────────────────────┘")
    return "\n".join(lines)


def fmt_track_result_client(
    track_code: str,
    in_china: bool,
    in_dushanbe: bool,
) -> str:
    lines = [
        "┌─────────────────────────┐",
        "│   🔎  РЕЗУЛЬТАТ ПОИСКА   │",
        "├─────────────────────────┤",
        f"│ 📦  Трек: {track_code}",
    ]
    if in_dushanbe:
        lines.append("│ 📍  На складе в Душанбе ✅")
        lines.append("│ 🎉  Можно забирать!")
    elif in_china:
        lines.append("│ 📍  На складе в Китае 🇨🇳")
        lines.append("│ ⏳  Ожидайте доставку")
    else:
        lines.append("│ ❌  Трек-код не найден")
    lines.append("└─────────────────────────┘")
    return "\n".join(lines)


def fmt_my_parcels(
    client_id: str, parcels: dict,
) -> str:
    lines = [
        "┌─────────────────────────┐",
        "│     📦  МОИ ПОСЫЛКИ      │",
        "├─────────────────────────┤",
        f"│ 🆔  {client_id}",
    ]
    if parcels["dushanbe"]:
        lines.append("│")
        lines.append("│ 🏬 В Душанбе:")
        for t in parcels["dushanbe"]:
            lines.append(f"│   ✅ {t}")
    else:
        lines.append("│")
        lines.append("│ Посылок пока нет")
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


def fmt_warehouse_list_admin(warehouses: list) -> str:
    if not warehouses:
        return "🏬 Складов пока нет."
    lines = ["🏬 Список складов:\n"]
    for w in warehouses:
        lines.append(
            f"[{w.id}] {w.name} — {w.phone}"
        )
    return "\n".join(lines)