import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "0"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "").strip()
CHANNEL_URL = os.getenv("CHANNEL_URL", "").strip()

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    DB_PATH = Path("backend/data/cargo_tps.db")
    DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
