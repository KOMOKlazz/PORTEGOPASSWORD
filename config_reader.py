import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str
    admin_id: int


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN")
    admin_id_raw = os.getenv("ADMIN_ID")

    if not token:
        raise RuntimeError("BOT_TOKEN не задан в .env")
    if not admin_id_raw:
        raise RuntimeError("ADMIN_ID не задан в .env")

    try:
        admin_id = int(admin_id_raw)
    except ValueError as exc:
        raise RuntimeError("ADMIN_ID в .env должен быть числом") from exc

    return Config(bot_token=token, admin_id=admin_id)


config = load_config()