import logging

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_ID: int
    API_HASH: SecretStr
    BOT_TOKEN: SecretStr
    ADMIN_ID: int
    GROUP_ID: int
    SESSION_NAME: str = "keyword_seeker"
    db_url: str = "sqlite+aiosqlite:///database.db"
    db_echo: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: "
    "%(filename)s: "
    "%(levelname)s: "
    "%(funcName)s(): "
    "%(lineno)d:\t"
    "%(message)s",
)
