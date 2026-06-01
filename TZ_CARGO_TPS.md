# ТЗ: Веб-программа Cargo TPS + доработка Telegram-бота

## Общее описание проекта

Cargo TPS — служба доставки грузов из Китая в Таджикистан (Душанбе).
Существует работающий Telegram-бот (aiogram 3.x, SQLAlchemy async, SQLite).
Задача — создать веб-приложение для сотрудников и владельца, перевести бота на новый backend,
отказаться от Excel-операций, перейти на PostgreSQL.

---

## Стек технологий

| Компонент | Технология |
|-----------|------------|
| Backend API | FastAPI + SQLAlchemy async + asyncpg |
| БД | PostgreSQL |
| Аутентификация веб | JWT (python-jose + passlib bcrypt) |
| Фронтенд | React + Ant Design (antd) + @ant-design/charts |
| HTTP-клиент фронта | axios |
| Telegram-бот | aiogram 3.x → ходит в FastAPI по HTTP (axios/aiohttp) |
| Миграции | Alembic |
| Деплой | Docker Compose (postgres + api + bot + frontend nginx) |

---

## Архитектура

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  React SPA   │────▶│   FastAPI API    │◀────│  aiogram Bot │
│  (Ant Design)│     │  (единый backend)│     │  (Telegram)  │
└──────────────┘     └────────┬─────────┘     └──────────────┘
                              │
                     ┌────────▼─────────┐
                     │   PostgreSQL     │
                     └──────────────────┘
```

Единый backend API — вся бизнес-логика в одном месте.
Бот НЕ работает с БД напрямую, а вызывает API-эндпоинты.
Веб-приложение — React SPA, общается с API через JWT-токены.

---

## Роли пользователей

### Владелец (owner)
- Полный доступ ко всем разделам веб-панели
- Дашборд со статистикой и аналитикой
- Управление сотрудниками (создание/удаление/редактирование аккаунтов)
- Управление тарифами, складами, контентом бота
- Просмотр журнала действий (audit log)
- Все операции с посылками и клиентами

### Админ Китай (admin_china)
- Добавление трек-кодов на склад Китай (одиночный скан + массовый ввод)
- Просмотр списка посылок Китая (без редактирования)
- Поиск по трек-коду (только свои записи)
- **НЕ имеет доступа к**: дашборду, клиентам, выдаче, тарифам, настройкам, управлению админами

### Админ Душанбе (admin_dushanbe)
- Добавление трек-кодов Душанбе (с TPS-кодом, весом, методом доставки)
- Выдача товара клиенту (расчёт суммы, приём оплаты)
- Просмотр и редактирование посылок (все статусы)
- Просмотр и поиск клиентов
- Управление складами и тарифами
- Редактирование контента бота (поддержка, прайс)
- Просмотр журнала действий
- **НЕ имеет доступа к**: дашборду, управлению админами

### Клиент (client)
- Работает **только через Telegram-бота**
- Регистрация (ФИО, телефон, адрес проживания)
- Просмотр/редактирование профиля
- Мои посылки (группировка по статусам, пагинация)
- Проверка трек-кода
- Адреса складов (с подставленным TPS-кодом)
- Прайс-лист
- Поддержка

---

## Схема базы данных (PostgreSQL)

### Таблица `clients`

Бывшая таблица `users`. Клиенты, зарегистрированные через бота.

| Поле | Тип | Описание |
|------|-----|----------|
| id | SERIAL PK | Внутренний ID |
| telegram_id | BIGINT UNIQUE NOT NULL | Telegram user ID |
| tps_code | VARCHAR(20) UNIQUE NOT NULL | TPS-код клиента (TPS001, TPS1000...) |
| full_name | VARCHAR(255) NOT NULL | ФИО клиента |
| phone | VARCHAR(20) NOT NULL | Телефон (+992XXXXXXXXX) |
| address | TEXT | Адрес проживания (свободный текст) |
| lang | VARCHAR(5) DEFAULT 'ru' | Язык интерфейса (ru/tj) |
| status | VARCHAR(20) DEFAULT 'active' | active / blocked |
| created_at | TIMESTAMP DEFAULT NOW() | Дата регистрации |
| last_activity_at | TIMESTAMP | Последняя активность |

**Индексы:** telegram_id, tps_code, phone, full_name.

### Таблица `staff_users`

Сотрудники веб-панели (владелец + админы).

| Поле | Тип | Описание |
|------|-----|----------|
| id | SERIAL PK | Внутренний ID |
| full_name | VARCHAR(255) NOT NULL | ФИО сотрудника |
| login | VARCHAR(100) UNIQUE NOT NULL | Логин для входа |
| password_hash | VARCHAR(255) NOT NULL | bcrypt хеш пароля |
| role | VARCHAR(20) NOT NULL | owner / admin_china / admin_dushanbe |
| warehouse_id | INT FK warehouses(id) NULL | Привязка к складу (опционально) |
| is_active | BOOLEAN DEFAULT TRUE | Активен или отключён |
| created_at | TIMESTAMP DEFAULT NOW() | Дата создания |

**Роли:** `owner`, `admin_china`, `admin_dushanbe`.

### Таблица `parcels_china`

Посылки, принятые на складе в Китае. На этом этапе клиент неизвестен.

| Поле | Тип | Описание |
|------|-----|----------|
| id | SERIAL PK | Внутренний ID |
| track_id | VARCHAR(100) UNIQUE NOT NULL | Трек-код (нормализованный: uppercase, без спецсимволов) |
| warehouse_id | INT FK warehouses(id) NULL | Склад Китай |
| created_by | INT FK staff_users(id) NOT NULL | Кто добавил |
| created_at | TIMESTAMP DEFAULT NOW() | Дата добавления |

**Индексы:** track_id (unique), created_at.

### Таблица `parcels_dushanbe`

Посылки, прибывшие на склад в Душанбе. Здесь полная карточка посылки.

| Поле | Тип | Описание |
|------|-----|----------|
| id | SERIAL PK | Внутренний ID |
| track_id | VARCHAR(100) UNIQUE NOT NULL | Трек-код |
| client_id | INT FK clients(id) NOT NULL | Клиент-владелец |
| status | VARCHAR(30) NOT NULL DEFAULT 'received_dushanbe' | Текущий статус |
| weight_kg | DECIMAL(10,3) NOT NULL | Вес в кг |
| volume_m3 | DECIMAL(10,4) NULL | Объём в м³ (для фуры) |
| delivery_method | VARCHAR(20) NOT NULL | avia / truck |
| warehouse_id | INT FK warehouses(id) NULL | Склад Душанбе |
| amount_due | DECIMAL(10,2) NULL | Сумма к оплате (рассчитывается при выдаче) |
| tariff_snapshot | DECIMAL(10,2) NULL | Тариф на момент расчёта (фиксируется при выдаче) |
| has_china_registration | BOOLEAN DEFAULT FALSE | Был ли зарегистрирован в Китае |
| comment | TEXT NULL | Комментарий администратора |
| notified_at | TIMESTAMP NULL | Когда отправлено уведомление клиенту |
| created_by | INT FK staff_users(id) NOT NULL | Кто добавил |
| created_at | TIMESTAMP DEFAULT NOW() | Дата добавления |
| updated_at | TIMESTAMP DEFAULT NOW() | Дата последнего изменения |

**Статусы посылок (parcels_dushanbe.status):**

| Статус | Когда ставится | Кто ставит |
|--------|---------------|------------|
| `received_dushanbe` | Посылка прибыла на склад Душанбе | Админ Душанбе |
| `ready_to_issue` | Готова к выдаче | Админ Душанбе |
| `issued` | Выдана клиенту | Админ Душанбе |
| `problem` | Проблема (повреждение, спор, ошибка) | Админ / владелец |

**Индексы:** track_id (unique), client_id, status, created_at, delivery_method.

**Связь таблиц:** при добавлении в Душанбе система ищет track_id в `parcels_china`. Если найден → `has_china_registration = TRUE`, если нет → `has_china_registration = FALSE` (пришло без китайской регистрации).

### Таблица `unresolved_parcels`

Посылки с неизвестным TPS-кодом при добавлении в Душанбе.

| Поле | Тип | Описание |
|------|-----|----------|
| id | SERIAL PK | Внутренний ID |
| track_id | VARCHAR(100) NOT NULL | Трек-код |
| raw_tps_code | VARCHAR(50) NOT NULL | Введённый TPS-код (не найден в базе) |
| weight_kg | DECIMAL(10,3) NULL | Вес |
| volume_m3 | DECIMAL(10,4) NULL | Объём в м³ |
| delivery_method | VARCHAR(20) NULL | avia / truck |
| comment | TEXT NULL | Комментарий |
| resolved | BOOLEAN DEFAULT FALSE | Разрешено или нет |
| resolved_parcel_id | INT FK parcels_dushanbe(id) NULL | Ссылка на созданную посылку после разрешения |
| created_by | INT FK staff_users(id) | Кто добавил |
| created_at | TIMESTAMP DEFAULT NOW() | Дата |

### Таблица `warehouses`

Склады и ПВЗ.

| Поле | Тип | Описание |
|------|-----|----------|
| id | SERIAL PK | ID |
| name | VARCHAR(100) NOT NULL | Название |
| type | VARCHAR(20) NOT NULL | china / dushanbe / pvz |
| country | VARCHAR(50) | Страна |
| city | VARCHAR(100) | Город |
| phone | VARCHAR(50) NOT NULL | Телефон |
| region | VARCHAR(255) NOT NULL | Регион (для китайского адреса) |
| address | TEXT NOT NULL | Адрес |
| is_active | BOOLEAN DEFAULT TRUE | Активен |
| created_at | TIMESTAMP DEFAULT NOW() | Дата создания |

### Таблица `tariffs`

Тарифы доставки.

| Поле | Тип | Описание |
|------|-----|----------|
| id | SERIAL PK | ID |
| method | VARCHAR(20) NOT NULL | avia / truck |
| price_per_kg | DECIMAL(10,2) NOT NULL | Цена за 1 кг |
| price_per_m3 | DECIMAL(10,2) NULL | Цена за 1 м³ (только для truck) |
| currency | VARCHAR(10) DEFAULT 'USD' | Валюта |
| is_active | BOOLEAN DEFAULT TRUE | Активный тариф (при создании нового — старый деактивируется) |
| created_by | INT FK staff_users(id) | Кто создал |
| created_at | TIMESTAMP DEFAULT NOW() | Дата создания |

Логика: при расчёте берётся последний активный тариф по методу (`is_active = TRUE`). При создании нового тарифа старый автоматически деактивируется (`is_active = FALSE`). Для фуры сумма считается как `MAX(weight_kg × price_per_kg, volume_m3 × price_per_m3)` — берётся что больше. Для авиа — только по весу. При выдаче тариф фиксируется в `parcels_dushanbe.tariff_snapshot` и `issuance_items.tariff_applied`.

### Таблица `issuance_orders`

Операции выдачи (один документ выдачи = один визит клиента).

| Поле | Тип | Описание |
|------|-----|----------|
| id | SERIAL PK | ID |
| client_id | INT FK clients(id) NOT NULL | Клиент |
| staff_id | INT FK staff_users(id) NOT NULL | Кто выдал |
| total_weight | DECIMAL(10,3) NOT NULL | Общий вес |
| total_amount | DECIMAL(10,2) NOT NULL | Общая сумма |
| payment_status | VARCHAR(20) NOT NULL | paid / debt |
| payment_method | VARCHAR(20) NULL | cash / transfer / NULL (если долг) |
| issued_at | TIMESTAMP DEFAULT NOW() | Дата/время выдачи |

### Таблица `issuance_items`

Посылки внутри операции выдачи.

| Поле | Тип | Описание |
|------|-----|----------|
| id | SERIAL PK | ID |
| issuance_order_id | INT FK issuance_orders(id) NOT NULL | Ссылка на операцию |
| parcel_id | INT FK parcels_dushanbe(id) NOT NULL | Посылка |
| weight_kg | DECIMAL(10,3) NOT NULL | Вес посылки |
| volume_m3 | DECIMAL(10,4) NULL | Объём посылки в м³ |
| delivery_method | VARCHAR(20) NOT NULL | avia / truck |
| tariff_applied | DECIMAL(10,2) NOT NULL | Тариф на момент выдачи |
| amount | DECIMAL(10,2) NOT NULL | Сумма за эту посылку |

### Таблица `notification_logs`

История уведомлений Telegram.

| Поле | Тип | Описание |
|------|-----|----------|
| id | SERIAL PK | ID |
| client_id | INT FK clients(id) NOT NULL | Клиент |
| parcel_id | INT FK parcels_dushanbe(id) NULL | Посылка |
| notification_type | VARCHAR(50) NOT NULL | parcel_arrived / reminder / custom |
| status | VARCHAR(20) NOT NULL | sent / failed |
| error | TEXT NULL | Текст ошибки (если failed) |
| sent_at | TIMESTAMP DEFAULT NOW() | Дата отправки |

### Таблица `audit_logs`

Журнал ВСЕХ действий сотрудников.

| Поле | Тип | Описание |
|------|-----|----------|
| id | SERIAL PK | ID |
| staff_id | INT FK staff_users(id) NOT NULL | Кто |
| action | VARCHAR(100) NOT NULL | create_parcel / update_status / issue_parcel / create_staff / update_tariff / ... |
| entity_type | VARCHAR(50) NOT NULL | parcel / client / staff / tariff / warehouse / setting |
| entity_id | INT NULL | ID объекта |
| before_json | JSONB NULL | Состояние до |
| after_json | JSONB NULL | Состояние после |
| ip_address | VARCHAR(45) NULL | IP адрес |
| created_at | TIMESTAMP DEFAULT NOW() | Когда |

### Таблица `settings`

Настройки системы (тексты бота, прайс, поддержка и т.д.).

| Поле | Тип | Описание |
|------|-----|----------|
| key | VARCHAR(100) PK | Ключ настройки |
| value | TEXT NOT NULL | Значение |
| updated_at | TIMESTAMP DEFAULT NOW() | Дата обновления |
| updated_by | INT FK staff_users(id) NULL | Кто обновил |

---

## Формат TPS-кода

Динамическая длина, минимум 3 цифры:
- TPS001 ... TPS999 (первые 999 клиентов)
- TPS1000 ... TPS9999 (следующие 9000)
- TPS10000 ... (и далее бесконечно)

Алгоритм генерации:
1. Получить все занятые TPS-коды из таблицы `clients`
2. Найти минимальный свободный номер начиная с 1
3. Пропустить зарезервированные номера (007, 111, 222, 333, 444, 555, 666, 777, 888, 999)
4. Форматировать: если num < 1000 → 3 знака (TPS001), иначе без лидирующих нулей (TPS1000)

```python
def format_tps_code(num: int) -> str:
    if num < 1000:
        return f"TPS{num:03d}"
    return f"TPS{num}"
```

---

## Флоу бизнес-процессов (подробно)

### Флоу 1: Регистрация клиента (Telegram-бот)

```
Клиент нажимает /start
    │
    ▼
Бот → API: GET /api/clients/by-telegram/{telegram_id}
    │
    ├── Клиент найден → «С возвращением, {name}!» → главное меню
    │
    └── Клиент НЕ найден
         │
         ▼
    Бот проверяет подписку на канал
         │
         ├── Не подписан → «Подпишитесь на канал» + кнопка проверки
         │
         └── Подписан
              │
              ▼
         Выбор языка (ru / tj)
              │
              ▼
         «Введите ФИО» → пользователь вводит ФИО
              │
              ▼
         Валидация: длина >= 3 символов
              │
              ▼
         «Введите телефон» → пользователь вводит номер
              │
              ▼
         Валидация: +992XXXXXXXXX или 9 цифр → нормализация в +992...
              │
              ▼
         «Введите адрес проживания» → пользователь вводит адрес
              │
              ▼
         Бот → API: POST /api/clients/register
         Body: { telegram_id, full_name, phone, address, lang }
              │
              ▼
         API генерирует TPS-код, создаёт клиента, возвращает tps_code
              │
              ▼
         Бот показывает:
         «Регистрация завершена! Ваш ID: TPS001
          Укажите этот код при отправке посылок»
              │
              ▼
         Главное меню
```

### Флоу 2: Добавление трека — Китай (веб-панель)

```
Админ Китай авторизуется в веб-панели (логин + пароль → JWT)
    │
    ▼
Система проверяет role == admin_china или owner
    │
    ▼
Открывается раздел «Склад Китай»
    │
    ▼
Два режима ввода:

── Режим 1: Одиночный скан ──
    │
    Курсор в поле track_id (автофокус)
    │
    Сканер пикает → track_id попадает в поле → автоматический Enter
    │
    ▼
    Фронт → API: POST /api/parcels/china
    Body: { track_id }
    │
    ▼
    API:
    1. Нормализует трек (uppercase, убрать спецсимволы)
    2. Проверяет дубликат в parcels_china (track_id UNIQUE)
       ├── Дубликат → вернуть ошибку «Трек уже существует»
       └── Нет дубликата
            │
            3. Создаёт запись в parcels_china:
               - track_id = нормализованный
               - warehouse_id = склад Китай
               - created_by = staff_id из JWT
            │
            4. Создаёт запись в audit_logs
            │
            ▼
    Фронт показывает «✅ Трек XXXXX добавлен»
    Поле очищается, фокус возвращается в поле → готов к следующему скану


── Режим 2: Массовый ввод ──
    │
    Textarea: каждая строка — отдельный track_id
    │
    Кнопка «Добавить все»
    │
    ▼
    Фронт → API: POST /api/parcels/china/bulk
    Body: { track_ids: ["TRACK1", "TRACK2", ...] }
    │
    ▼
    API обрабатывает каждый трек:
    - Нормализация
    - Проверка дубликатов
    - Создание записей
    │
    ▼
    Ответ: { total: 50, added: 47, duplicates: 3, duplicate_list: [...] }
    │
    ▼
    Фронт показывает результат:
    «Всего строк: 50 | Добавлено: 47 | Пропущено (дубли): 3»
```

### Флоу 3: Добавление трека — Душанбе (веб-панель)

```
Админ Душанбе авторизуется → раздел «Склад Душанбе»
    │
    ▼
Форма добавления:
    - track_id      (обязательно) — скан или ручной ввод
    - tps_code      (обязательно) — код клиента
    - weight_kg     (обязательно) — вес в кг
    - volume_m3     (необязательно) — объём в м³ (для фуры)
    - delivery_method (обязательно) — выбор: Авиа / Фура
    - comment       (необязательно) — текст
    │
    ▼
Фронт → API: POST /api/parcels/dushanbe
Body: { track_id, tps_code, weight_kg, volume_m3, delivery_method, comment }
    │
    ▼
API:
    1. Нормализовать track_id

    2. Проверить tps_code → SELECT FROM clients WHERE tps_code = ?
       │
       ├── Клиент НЕ найден
       │    │
       │    ▼
       │    Сохранить в таблицу unresolved_parcels:
       │    { track_id, raw_tps_code, weight_kg, volume_m3, delivery_method, comment, created_by }
       │    │
       │    ▼
       │    Вернуть: { status: "unresolved", message: "TPS-код не найден" }
       │    │
       │    ▼
       │    Фронт показывает: «⚠️ TPS-код не найден, посылка сохранена как проблемная»
       │
       └── Клиент найден
            │
            3. Проверить track_id в parcels_dushanbe:
               │
               ├── Трек уже существует в parcels_dushanbe
               │    → Вернуть ошибку «Трек уже обработан»
               │
               └── Трек НЕ существует в parcels_dushanbe
                    │
                    4. Проверить track_id в parcels_china:
                       ├── Найден → has_china_registration = TRUE
                       └── Не найден → has_china_registration = FALSE
                    │
                    5. Создать запись в parcels_dushanbe:
                       - track_id, client_id, weight_kg, volume_m3
                       - delivery_method, comment
                       - status = 'received_dushanbe'
                       - has_china_registration
                       - warehouse_id = склад Душанбе
                       - created_by = staff_id из JWT
            │
            6. Создать audit_log
            │
            6. Отправить уведомление клиенту через Telegram:
               API → Бот (или напрямую через Bot API):
               «📬 Ваша посылка {track_id} прибыла на склад Душанбе!
                Можно забирать!»
               │
               ├── Успешно → записать в notification_logs (status=sent)
               │             обновить parcels.notified_at
               └── Ошибка → записать в notification_logs (status=failed, error=...)
            │
            ▼
    Вернуть: { status: "ok", parcel_id, client_name, notified: true/false }
    │
    ▼
    Фронт показывает: «✅ Посылка добавлена, клиент уведомлён»
```

### Флоу 4: Выдача товара в ПВЗ (веб-панель)

```
Админ Душанбе → раздел «Выдача товара»
    │
    ▼
Поле ввода: TPS-код или номер телефона клиента
    │
    ▼
Фронт → API: GET /api/clients/search?q=TPS001  (или ?q=+992...)
    │
    ▼
API возвращает клиента + список невыданных посылок:
    GET /api/parcels?client_id=X&status=received_dushanbe,ready_to_issue
    │
    ▼
Фронт показывает:
    ┌──────────────────────────────────────────────────────────────┐
    │ Клиент: Иванов Иван | TPS001 | +992901234567               │
    ├──────────────────────────────────────────────────────────────┤
    │ ☑ TRACK001  │ 2.5 кг │  —  м³ │ Авиа  │ $25.00            │
    │ ☑ TRACK002  │ 1.8 кг │ 0.5 м³ │ Фура  │ $140.00           │
    │ ☐ TRACK003  │ 5.0 кг │  —  м³ │ Авиа  │ $50.00            │
    ├──────────────────────────────────────────────────────────────┤
    │ Итого (выбрано): 4.3 кг | $165.00                          │
    │ Способ оплаты: [Наличные] [Перевод] [Долг]                 │
    │                        [Выдать]                             │
    └──────────────────────────────────────────────────────────────┘
    │
    ▼
Админ выбирает посылки галочками → сумма пересчитывается на лету
    │
    ▼
Выбирает способ оплаты → нажимает «Выдать»
    │
    ▼
Фронт → API: POST /api/issuance
Body: {
    client_id: 1,
    parcel_ids: [1, 2],
    payment_method: "cash",   // "cash" | "transfer" | null (для долга)
    payment_status: "paid"    // "paid" | "debt"
}
    │
    ▼
API (в одной транзакции):
    1. Для каждой посылки:
       - Получить текущий активный тариф по delivery_method
       - Расчёт суммы:
           Авиа: amount = weight_kg × tariff.price_per_kg
           Фура: amount = MAX(weight_kg × price_per_kg, volume_m3 × price_per_m3)
       - Обновить parcels_dushanbe:
           status = 'issued'
           amount_due = amount
           tariff_snapshot = примененный тариф

    2. Создать issuance_order:
       { client_id, staff_id, total_weight, total_amount, payment_status, payment_method }

    3. Для каждой посылки создать issuance_item:
       { issuance_order_id, parcel_id, weight_kg, delivery_method, tariff_applied, amount }

    4. Создать audit_log

    5. Вернуть: { issuance_order_id, total_weight, total_amount, items: [...] }
    │
    ▼
Фронт показывает:
    «✅ Выдача оформлена! Итого: 4.3 кг, $29.50, оплата: наличные»
    │
    ▼
Форма очищается, готова к следующему клиенту
```

### Флоу 5: Мои посылки (Telegram-бот)

```
Клиент нажимает «📦 Мои посылки»
    │
    ▼
Бот показывает inline-кнопки со статусами:
    [🏬 В Душанбе (2)]  [✅ Выдано (15)]
    │
    ▼
Клиент нажимает, например, «🏬 В Душанбе (2)»
    │
    ▼
Бот → API: GET /api/parcels/my?telegram_id=123&status=received_dushanbe&page=1&per_page=5
    │
    ▼
API ищет в parcels_dushanbe по client_id
Возвращает: { items: [...], total: 2, page: 1, pages: 1 }
    │
    ▼
Бот показывает:
    ┌─────────────────────────┐
    │   🏬 В ДУШАНБЕ (2)      │
    ├─────────────────────────┤
    │ TRACK001  02.06.2026 ⏳  │
    │ TRACK002  01.06.2026 ⏳  │
    └─────────────────────────┘
    [⬅️ Назад]

Если посылок > 5:
    [⬅️ 1/3 ▶️]
    Кнопки пагинации (inline callback: parcels_dushanbe_page_2)
```

### Флоу 6: Проверка трека (Telegram-бот)

```
Клиент нажимает «🔎 Проверить трек»
    │
    ▼
Бот: «Введите трек-код:»
    │
    ▼
Клиент вводит трек-код
    │
    ▼
Бот → API: GET /api/parcels/track/{track_id}?telegram_id=123
    │
    ▼
API:
    1. Нормализовать track_id
    2. Найти в parcels_dushanbe (приоритет)
    3. Если не найден — найти в parcels_china
    4. Вернуть статус (без чужих персональных данных)
    │
    ▼
Варианты ответа:
    - «📍 На складе в Китае 🇨🇳 — Ожидайте доставку»
    - «📍 На складе в Душанбе ✅ — Можно забирать!»
    - «📍 Выдана клиенту ✅»
    - «❌ Трек-код не найден»
```

### Флоу 7: Разрешение проблемных посылок (веб-панель)

```
Админ Душанбе / Владелец → раздел «Проблемные посылки»
    │
    ▼
Таблица из unresolved_parcels (resolved = FALSE)
    │
    ▼
Админ открывает запись:
    track_id: TRACKXXX
    Введённый TPS: TPS999999 (не найден)
    Вес: 2.5 кг | Метод: Авиа
    │
    ▼
Два действия:
    │
    ├── «Привязать к клиенту» → ввести правильный TPS-код
    │    → API создаёт запись в parcels, обновляет unresolved_parcels.resolved = TRUE
    │    → Отправляет уведомление клиенту
    │
    └── «Удалить» → мягкое удаление (resolved = TRUE, resolved_parcel_id = NULL)
```

### Флоу 8: Статистика владельца (веб-панель — дашборд)

```
Владелец авторизуется → Дашборд (главная страница)
    │
    ▼
Фильтры вверху:
    [Период: Сегодня / 7 дней / 30 дней / Произвольный]
    [Склад: Все / Китай / Душанбе]
    [Метод: Все / Авиа / Фура]
    [Сотрудник: Все / выбрать]
    │
    ▼
Карточки-метрики (верхняя панель):
    ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
    │ Посылок │  │  Вес    │  │ Выручка │  │ Клиенты │
    │  в Китае│  │  общий  │  │  за     │  │  новых  │
    │   156   │  │ 1250 кг │  │ $15,400 │  │   +23   │
    └─────────┘  └─────────┘  └─────────┘  └─────────┘
    │
    ▼
Графики (средняя панель):
    - Линейный: Посылки по дням (принято Китай / Душанбе / выдано)
    - Столбчатый: Выручка по неделям/месяцам
    - Круговая: Авиа vs Фура (по количеству и весу)
    - Столбчатый: Активность сотрудников (кто сколько добавил/выдал)
    │
    ▼
Таблицы (нижняя панель):
    - Топ-10 клиентов по количеству посылок / весу / сумме
    - Зависшие посылки (в Душанбе > 14 дней без выдачи)
    - Последние операции (лог действий)
    │
    ▼
Все данные → API:
    GET /api/stats/overview?period=7d&warehouse=all&method=all
    GET /api/stats/parcels-by-day?from=2026-05-25&to=2026-06-01
    GET /api/stats/revenue?group_by=week
    GET /api/stats/top-clients?limit=10&sort_by=amount
    GET /api/stats/stuck-parcels?days=14
    GET /api/stats/staff-activity?period=30d
    GET /api/stats/bot-activity (регистрации, уведомления, ошибки)
```

---

## API эндпоинты (полный список)

### Аутентификация

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| POST | /api/auth/login | Логин, возвращает JWT | Все |
| POST | /api/auth/refresh | Обновление токена | Авторизованные |
| GET | /api/auth/me | Текущий пользователь | Авторизованные |

### Клиенты

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| POST | /api/clients/register | Регистрация через бота | Бот |
| GET | /api/clients/by-telegram/{telegram_id} | Поиск по Telegram ID | Бот |
| GET | /api/clients | Список клиентов с фильтрами и пагинацией | admin_dushanbe, owner |
| GET | /api/clients/{id} | Карточка клиента | admin_dushanbe, owner |
| GET | /api/clients/search?q= | Поиск по TPS/телефону/ФИО | admin_dushanbe, owner |
| PATCH | /api/clients/{id} | Редактирование данных клиента | owner |
| PATCH | /api/clients/{id}/block | Блокировка клиента | owner |
| PATCH | /api/clients/by-telegram/{telegram_id} | Обновление профиля из бота | Бот |

### Посылки

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| POST | /api/parcels/china | Добавить трек Китай (одиночный) | admin_china, owner |
| POST | /api/parcels/china/bulk | Массовое добавление Китай | admin_china, owner |
| POST | /api/parcels/dushanbe | Добавить трек Душанбе | admin_dushanbe, owner |
| GET | /api/parcels | Список посылок с фильтрами | admin_dushanbe, owner |
| GET | /api/parcels/{id} | Карточка посылки | admin_dushanbe, owner |
| GET | /api/parcels/track/{track_id} | Поиск по трек-коду | Все роли |
| GET | /api/parcels/my?telegram_id=&status=&page= | Посылки клиента (для бота) | Бот |
| PATCH | /api/parcels/{id}/status | Смена статуса | admin_dushanbe, owner |
| PATCH | /api/parcels/{id} | Редактирование посылки | admin_dushanbe, owner |

### Проблемные посылки

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| GET | /api/unresolved | Список проблемных | admin_dushanbe, owner |
| POST | /api/unresolved/{id}/resolve | Привязать к клиенту | admin_dushanbe, owner |
| DELETE | /api/unresolved/{id} | Мягкое удаление | admin_dushanbe, owner |

### Выдача

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| POST | /api/issuance | Оформить выдачу | admin_dushanbe, owner |
| GET | /api/issuance | Список выдач с фильтрами | admin_dushanbe, owner |
| GET | /api/issuance/{id} | Детали выдачи | admin_dushanbe, owner |

### Склады

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| GET | /api/warehouses | Список складов | Все роли |
| GET | /api/warehouses/{id} | Детали склада | Все роли |
| POST | /api/warehouses | Создать склад | admin_dushanbe, owner |
| PATCH | /api/warehouses/{id} | Редактировать | admin_dushanbe, owner |
| DELETE | /api/warehouses/{id} | Удалить (soft delete) | owner |

### Тарифы

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| GET | /api/tariffs | Список тарифов | admin_dushanbe, owner |
| GET | /api/tariffs/active | Текущие активные | Все роли |
| POST | /api/tariffs | Создать тариф | admin_dushanbe, owner |
| PATCH | /api/tariffs/{id} | Редактировать | owner |

### Сотрудники

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| GET | /api/staff | Список сотрудников | owner |
| POST | /api/staff | Создать сотрудника | owner |
| PATCH | /api/staff/{id} | Редактировать | owner |
| DELETE | /api/staff/{id} | Деактивировать | owner |
| POST | /api/staff/{id}/reset-password | Сброс пароля | owner |

### Настройки (контент бота)

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| GET | /api/settings | Все настройки | admin_dushanbe, owner |
| GET | /api/settings/{key} | Одна настройка | Все роли |
| PUT | /api/settings/{key} | Обновить | admin_dushanbe, owner |

### Статистика (дашборд)

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| GET | /api/stats/overview | Общие метрики с фильтрами | owner |
| GET | /api/stats/parcels-by-day | Посылки по дням | owner |
| GET | /api/stats/revenue | Выручка по периодам | owner |
| GET | /api/stats/top-clients | Топ клиентов | owner |
| GET | /api/stats/stuck-parcels | Зависшие посылки | owner |
| GET | /api/stats/staff-activity | Активность сотрудников | owner |
| GET | /api/stats/bot-activity | Статистика бота | owner |

### Журнал действий

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| GET | /api/audit-logs | Журнал с фильтрами | admin_dushanbe, owner |

### Уведомления

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| GET | /api/notifications | Лог уведомлений | admin_dushanbe, owner |
| POST | /api/notifications/resend/{parcel_id} | Повторная отправка | admin_dushanbe, owner |

---

## Структура проекта

```
cargo-tps/
├── docker-compose.yml
├── .env.example
│
├── backend/
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │
│   └── app/
│       ├── main.py                  # FastAPI app, startup/shutdown
│       ├── config.py                # Настройки из .env
│       ├── database.py              # Engine, session, Base
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── client.py            # Client
│       │   ├── staff.py             # StaffUser
│       │   ├── parcel_china.py      # ParcelChina
│       │   ├── parcel_dushanbe.py   # ParcelDushanbe
│       │   ├── unresolved.py        # UnresolvedParcel
│       │   ├── warehouse.py         # Warehouse
│       │   ├── tariff.py            # Tariff
│       │   ├── issuance.py          # IssuanceOrder, IssuanceItem
│       │   ├── notification.py      # NotificationLog
│       │   ├── audit.py             # AuditLog
│       │   └── setting.py           # Setting
│       │
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── auth.py              # LoginRequest, TokenResponse
│       │   ├── client.py            # ClientCreate, ClientResponse, ...
│       │   ├── parcel.py            # ParcelCreate, ParcelResponse, ...
│       │   ├── issuance.py          # IssuanceCreate, IssuanceResponse, ...
│       │   ├── warehouse.py
│       │   ├── tariff.py
│       │   ├── staff.py
│       │   ├── stats.py
│       │   └── common.py            # PaginatedResponse, ...
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── deps.py              # get_db, get_current_user, require_role
│       │   ├── auth.py              # /api/auth/*
│       │   ├── clients.py           # /api/clients/*
│       │   ├── parcels.py           # /api/parcels/*
│       │   ├── unresolved.py        # /api/unresolved/*
│       │   ├── issuance.py          # /api/issuance/*
│       │   ├── warehouses.py        # /api/warehouses/*
│       │   ├── tariffs.py           # /api/tariffs/*
│       │   ├── staff.py             # /api/staff/*
│       │   ├── settings.py          # /api/settings/*
│       │   ├── stats.py             # /api/stats/*
│       │   ├── audit.py             # /api/audit-logs
│       │   └── notifications.py     # /api/notifications/*
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── client_service.py    # Бизнес-логика клиентов, генерация TPS
│       │   ├── parcel_service.py    # Бизнес-логика посылок
│       │   ├── issuance_service.py  # Расчёт суммы, выдача
│       │   ├── tariff_service.py    # Получение активного тарифа
│       │   ├── notification_service.py  # Отправка через Telegram Bot API
│       │   └── audit_service.py     # Запись в audit_logs
│       │
│       └── utils/
│           ├── __init__.py
│           ├── security.py          # JWT encode/decode, password hash/verify
│           ├── tps_code.py          # Генерация TPS-кода
│           └── track_normalize.py   # Нормализация трек-кодов
│
├── bot/
│   ├── requirements.txt
│   └── src/
│       ├── main.py                  # Запуск бота
│       ├── config.py                # BOT_TOKEN, API_BASE_URL
│       ├── api_client.py            # HTTP-клиент к FastAPI (aiohttp)
│       ├── texts.py                 # Тексты ru/tj
│       ├── keyboards.py            # Клавиатуры
│       ├── fmt.py                   # Форматирование сообщений
│       ├── utils.py                 # validate_phone и др.
│       │
│       └── handlers/
│           ├── __init__.py
│           ├── start.py             # /start, регистрация, выбор языка
│           ├── profile.py           # Профиль, редактирование
│           ├── parcels.py           # Мои посылки, проверка трека
│           ├── warehouses.py        # Адреса складов
│           ├── info.py              # Прайс, поддержка
│           └── subscription.py      # Проверка подписки на канал
│
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    │
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api/
        │   ├── client.ts            # axios instance с JWT interceptor
        │   ├── auth.ts              # login, refresh, getMe
        │   ├── clients.ts           # CRUD клиентов
        │   ├── parcels.ts           # CRUD посылок
        │   ├── issuance.ts          # Выдача
        │   ├── warehouses.ts
        │   ├── tariffs.ts
        │   ├── staff.ts
        │   ├── stats.ts
        │   ├── audit.ts
        │   └── settings.ts
        │
        ├── components/
        │   ├── Layout.tsx           # Sidebar + header + content
        │   ├── ProtectedRoute.tsx   # Проверка JWT + роли
        │   └── common/              # Переиспользуемые компоненты
        │
        ├── pages/
        │   ├── Login.tsx
        │   ├── Dashboard.tsx        # Дашборд владельца
        │   ├── ParcelsChina.tsx     # Добавление треков Китай
        │   ├── ParcelsDushanbe.tsx  # Добавление треков Душанбе
        │   ├── ParcelsList.tsx      # Список всех посылок
        │   ├── ParcelDetail.tsx     # Карточка посылки
        │   ├── Issuance.tsx         # Выдача товара
        │   ├── IssuanceHistory.tsx  # История выдач
        │   ├── Clients.tsx          # Список клиентов
        │   ├── ClientDetail.tsx     # Карточка клиента
        │   ├── Unresolved.tsx       # Проблемные посылки
        │   ├── Warehouses.tsx       # Склады
        │   ├── Tariffs.tsx          # Тарифы
        │   ├── Staff.tsx            # Сотрудники
        │   ├── Settings.tsx         # Настройки контента бота
        │   └── AuditLog.tsx         # Журнал действий
        │
        ├── hooks/
        │   ├── useAuth.ts
        │   └── usePermissions.ts
        │
        ├── store/
        │   └── authStore.ts         # Zustand или Context
        │
        └── utils/
            └── permissions.ts       # Матрица доступа по ролям
```

---

## Матрица доступа (фронтенд — видимость страниц)

| Страница | owner | admin_china | admin_dushanbe |
|----------|-------|-------------|----------------|
| Дашборд | ✅ | ❌ | ❌ |
| Добавить Китай | ✅ | ✅ | ❌ |
| Посылки Китай (просмотр) | ✅ | ✅ (только просмотр) | ✅ |
| Добавить Душанбе | ✅ | ❌ | ✅ |
| Все посылки | ✅ | ❌ | ✅ |
| Карточка посылки | ✅ | ❌ | ✅ |
| Выдача товара | ✅ | ❌ | ✅ |
| История выдач | ✅ | ❌ | ✅ |
| Клиенты | ✅ | ❌ | ✅ |
| Проблемные посылки | ✅ | ❌ | ✅ |
| Склады | ✅ | ❌ | ✅ |
| Тарифы | ✅ | ❌ | ✅ |
| Сотрудники | ✅ | ❌ | ❌ |
| Настройки бота | ✅ | ❌ | ✅ |
| Журнал действий | ✅ | ❌ | ✅ |

---

## Миграция данных (с текущей версии)

### Что мигрировать

| Старая таблица | Новая таблица | Действия |
|---------------|---------------|----------|
| users | clients | Перенести telegram_id, client_id→tps_code, full_name, phone, lang, created_at. Добавить address=NULL, status='active' |
| parcels_china | parcels_china | Перенести track_code→track_id, добавить warehouse_id, created_by |
| parcels_dushanbe | parcels_dushanbe | Перенести track_code→track_id, client_id (связать через tps_code), status, добавить weight_kg, volume_m3, delivery_method, has_china_registration (проверить наличие в parcels_china) |
| warehouses | warehouses | Перенести все поля, добавить type/country/city/is_active |
| settings | settings | Перенести key/value |
| admins | staff_users | Создать записи с role='admin_dushanbe', сгенерировать логины/пароли |

### Скрипт миграции

Создать отдельный скрипт `scripts/migrate_from_sqlite.py`:
1. Подключиться к старой SQLite (data/bot.db)
2. Подключиться к новой PostgreSQL
3. Перенести данные с маппингом полей
4. Проверить целостность: количество записей, уникальность tps_code, связи client_id
5. Логировать результат

---

## Этапы разработки

### Этап 1: Backend — база, авторизация, модели (3-5 дней)

**Задачи:**
1. Настроить FastAPI проект (структура папок, config, database.py)
2. Настроить PostgreSQL + Alembic миграции
3. Создать ВСЕ модели SQLAlchemy (clients, staff_users, parcels_china, parcels_dushanbe, unresolved_parcels, warehouses, tariffs, issuance_orders, issuance_items, notification_logs, audit_logs, settings)
4. Реализовать JWT авторизацию (login, refresh, middleware)
5. Реализовать систему ролей (deps: get_current_user, require_role)
6. Реализовать audit_service (автоматическая запись действий)
7. API эндпоинты: auth/*, staff/*
8. Seed-скрипт: создать владельца (owner) с логином/паролем
9. Seed-скрипт: начальные склады и тарифы

**Критерии готовности:**
- Сотрудник входит по логину/паролю, получает JWT
- Роли проверяются на каждом эндпоинте
- Владелец может создать/удалить сотрудника
- Все действия логируются в audit_logs

### Этап 2: Backend — посылки Китай/Душанбе (3-4 дня)

**Задачи:**
1. Сервис генерации TPS-кода (tps_code.py)
2. Сервис нормализации трек-кодов (track_normalize.py)
3. API: POST /api/parcels/china (одиночный)
4. API: POST /api/parcels/china/bulk (массовый)
5. API: POST /api/parcels/dushanbe (с проверкой TPS, весом, методом)
6. API: GET/PATCH посылки, поиск, фильтры, пагинация
7. Логика unresolved_parcels (сохранение, разрешение)
8. API: клиенты (регистрация, поиск, карточка)
9. Сервис уведомлений (notification_service.py) — отправка через Bot API

**Критерии готовности:**
- Админ добавляет трек Китай без Excel
- Админ добавляет трек Душанбе с TPS/весом/методом
- Дубликаты блокируются
- Неизвестный TPS → unresolved_parcels
- Клиент получает уведомление в Telegram

### Этап 3: Backend — выдача товара (2-3 дня)

**Задачи:**
1. Сервис тарифов (получение активного тарифа по методу)
2. API: POST /api/issuance (расчёт суммы, фиксация выдачи)
3. Расчёт: авиа = вес × тариф_кг; фура = MAX(вес × тариф_кг, объём × тариф_м3)
4. Фиксация тарифа в момент выдачи (tariff_snapshot)
5. Обновление статусов посылок → issued
6. issuance_orders + issuance_items
7. Способы оплаты: cash, transfer, debt
8. API: GET /api/issuance (история выдач с фильтрами)

**Критерии готовности:**
- Сумма считается корректно (авиа по весу, фура — MAX из кг и м³)
- Выдача фиксируется с сотрудником и способом оплаты
- Тариф сохраняется в момент выдачи
- Посылки меняют статус на issued

### Этап 4: Backend — статистика и настройки (2-3 дня)

**Задачи:**
1. API: /api/stats/* (все эндпоинты дашборда)
2. API: /api/settings/* (контент бота)
3. API: /api/warehouses/* (CRUD)
4. API: /api/tariffs/* (CRUD)
5. API: /api/audit-logs (фильтры, пагинация)
6. API: /api/notifications (лог, повторная отправка)

**Критерии готовности:**
- Все метрики дашборда возвращают корректные данные
- Фильтры по периоду, складу, методу, сотруднику работают

### Этап 5: Фронтенд — авторизация, layout, посылки (5-7 дней)

**Задачи:**
1. Настроить React + Vite + TypeScript + Ant Design
2. Авторизация (Login.tsx, JWT interceptor, ProtectedRoute)
3. Layout (сайдбар с навигацией по ролям)
4. ParcelsChina.tsx (одиночный скан + массовый ввод)
5. ParcelsDushanbe.tsx (форма с TPS, вес, метод)
6. ParcelsList.tsx (таблица с фильтрами)
7. ParcelDetail.tsx (карточка посылки с историей)
8. Unresolved.tsx (проблемные посылки)

**Критерии готовности:**
- Авторизация работает, сайдбар адаптируется под роль
- Режим сканирования: фокус в поле, автодобавление, очистка
- Таблицы с сортировкой, фильтрами, пагинацией

### Этап 6: Фронтенд — выдача, клиенты, настройки (4-5 дней)

**Задачи:**
1. Issuance.tsx (поиск клиента, выбор посылок, расчёт, оплата)
2. IssuanceHistory.tsx (история выдач)
3. Clients.tsx (список, поиск)
4. ClientDetail.tsx (карточка с историей посылок и оплат)
5. Warehouses.tsx (CRUD)
6. Tariffs.tsx (CRUD)
7. Staff.tsx (создание, редактирование, деактивация)
8. Settings.tsx (контент бота)
9. AuditLog.tsx (журнал с фильтрами)

**Критерии готовности:**
- Полный цикл выдачи работает через веб-интерфейс
- Все CRUD-разделы функциональны

### Этап 7: Фронтенд — дашборд владельца (3-4 дня)

**Задачи:**
1. Dashboard.tsx — карточки метрик
2. Графики: линейные (по дням), столбчатые (выручка), круговые (авиа/фура)
3. Таблицы: топ клиентов, зависшие посылки, последние операции
4. Фильтры: период, склад, метод, сотрудник
5. Адаптивность (@ant-design/charts)

**Критерии готовности:**
- Все метрики из раздела 8 ТЗ отображаются
- Фильтры работают, графики обновляются

### Этап 8: Интеграция бота с новым API (3-4 дня)

**Задачи:**
1. Создать api_client.py (aiohttp клиент к FastAPI)
2. Переписать все хендлеры: вместо прямых вызовов db → вызовы API
3. Добавить поле «адрес» в регистрацию и профиль
4. Переделать «Мои посылки»: две кнопки (В Душанбе / Выдано) + пагинация (inline)
5. Обновить проверку трека (через API)
6. Обновить адреса складов, прайс, поддержку (через API /api/settings)
7. Убрать админский режим из бота (всё в веб-панели)

**Критерии готовности:**
- Бот не обращается к БД напрямую
- Регистрация с адресом работает
- Мои посылки: две кнопки (В Душанбе / Выдано) с пагинацией
- Уведомления доходят

### Этап 9: Миграция данных + Docker + деплой (2-3 дня)

**Задачи:**
1. Скрипт миграции SQLite → PostgreSQL
2. Docker Compose (postgres, api, bot, frontend/nginx)
3. .env.example с описанием всех переменных
4. Backup-скрипт для PostgreSQL (pg_dump по cron)
5. Тестирование полного цикла на проде
6. Создание аккаунта владельца

**Критерии готовности:**
- Все данные перенесены корректно
- docker-compose up поднимает весь стек
- Backup настроен и протестирован

---

## Переменные окружения (.env)

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=cargo_tps
POSTGRES_USER=cargo
POSTGRES_PASSWORD=secret

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480

# Telegram Bot
BOT_TOKEN=123456:ABC-DEF...
CHANNEL_USERNAME=@your_channel
CHANNEL_URL=https://t.me/your_channel

# API
API_BASE_URL=http://localhost:8000
API_BOT_SECRET=shared-secret-for-bot-to-api

# Owner seed
OWNER_LOGIN=owner
OWNER_PASSWORD=change-me
OWNER_FULL_NAME=Владелец
```

---

## Важные правила разработки

1. **Все операции записи → audit_logs.** Никаких исключений.
2. **Soft delete everywhere.** Посылки, клиенты, склады — не удалять физически.
3. **Тариф фиксируется при выдаче.** Изменение тарифа не влияет на историю.
4. **track_id нормализуется при записи:** uppercase, убрать пробелы и спецсимволы.
5. **tps_code нормализуется при поиске:** uppercase, trim.
6. **Пагинация на всех списочных эндпоинтах:** page, per_page, total, pages.
7. **Валидация на backend**, не доверять фронту.
8. **CORS** настроить для фронтенда.
9. **Бот аутентифицируется к API** через отдельный shared secret (заголовок X-Bot-Secret).
10. **Индексы в БД** на все поля, по которым идёт поиск/фильтрация.
