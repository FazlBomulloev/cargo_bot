from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = ""

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "cargo_tps"
    POSTGRES_USER: str = "cargo"
    POSTGRES_PASSWORD: str = "secret"

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    BOT_TOKEN: str = ""
    CHANNEL_USERNAME: str = ""
    CHANNEL_URL: str = ""

    API_BOT_SECRET: str = "shared-secret-for-bot-to-api"

    OWNER_LOGIN: str = "owner"
    OWNER_PASSWORD: str = "change-me"
    OWNER_FULL_NAME: str = "Owner"

    @property
    def database_url_resolved(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return "sqlite+aiosqlite:///./data/cargo_tps.db"

    model_config = {"env_file": "../.env", "extra": "ignore"}


settings = Settings()
