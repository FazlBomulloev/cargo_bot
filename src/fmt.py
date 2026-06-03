from src.texts import get_text


def fmt_profile(client, lang: str = "ru") -> str:
    title = get_text("profile_title", lang)
    return (
        "┌─────────────────────────┐\n"
        f"│        {title}        │\n"
        "├─────────────────────────┤\n"
        f"│ 🆔  {client.tps_code}\n"
        f"│ 👤  {client.full_name}\n"
        f"│ 📱  {client.phone}\n"
        "└─────────────────────────┘"
    )


def fmt_welcome(tps_code: str, lang: str = "ru") -> str:
    if lang == "tj":
        return (
            "╔══════════════════════════╗\n"
            "║   🎉  ХУШ ОМАДЕД!         ║\n"
            "╠══════════════════════════╣\n"
            "║                          ║\n"
            "║  Сабти ном анҷом ёфт!    ║\n"
            "║                          ║\n"
            f"║  ID-и шумо:  {tps_code}     \n"
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
        f"║  Ваш ID:  {tps_code}     \n"
        "║                          ║\n"
        "║  📌 Укажите этот код при  ║\n"
        "║  отправке посылок         ║\n"
        "║                          ║\n"
        "╚══════════════════════════╝"
    )


def _status_text(
    status: str, lang: str = "ru",
) -> str:
    if status == "issued":
        return get_text("status_received", lang)
    if status == "ready_to_issue":
        return get_text("status_ready", lang)
    if status == "problem":
        return get_text("status_problem", lang)
    return get_text("status_waiting", lang)


def _format_date(dt) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%d.%m.%Y")


def fmt_parcel_arrived(
    track_id: str, lang: str = "ru",
) -> str:
    title = get_text("parcel_arrived_title", lang)
    body = get_text("parcel_arrived_body", lang)
    return (
        "┌─────────────────────────┐\n"
        f"│   {title}   │\n"
        "├─────────────────────────┤\n"
        f"│ 📦  Трек: {track_id}\n"
        "│ 📍  Склад: Душанбе\n"
        "│\n"
        f"│ {body}\n"
        "└─────────────────────────┘"
    )


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
        if dushanbe_info.status == "issued":
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
    tps_code: str,
    parcels: list,
    lang: str = "ru",
) -> str:
    title = get_text("my_parcels_title", lang)
    lines = [
        "┌─────────────────────────┐",
        f"│     {title}      │",
        "├─────────────────────────┤",
        f"│ 🆔  {tps_code}",
    ]
    if parcels:
        lines.append("│")
        for p in parcels:
            status = _status_text(p.status, lang)
            date = _format_date(p.created_at)
            lines.append(
                f"│ {p.track_id}  "
                f"{date}  {status}"
            )
    else:
        lines.append("│")
        lines.append(
            "│ " + get_text("no_parcels", lang)
        )
    lines.append("└─────────────────────────┘")
    return "\n".join(lines)


def fmt_warehouse_for_client(
    w, tps_code: str, name: str,
) -> str:
    return (
        f"📍 {w.name}\n"
        "━━━━━━━━━━━━━━━\n"
        "Заполните адрес в Pinduoduo:\n\n"
        f"👤 {name}\n"
        f"📞 {w.phone}\n"
        f"🌏 {w.region}\n"
        f"📍 {w.address} {tps_code}"
    )
