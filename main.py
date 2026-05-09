import os
import sqlite3
from pathlib import Path

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers import user_commands, bot_messages

from aiogram.types import Message

# from config_reader import config

async def main() -> None:
    bot = Bot(token='8677924734:AAEYOs4GQWzdoR0Lf7FMSmPXm_qxwBJn9M8', default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    DATA_DIR = Path("/app/data")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    DB_PATH = DATA_DIR / "bot.db"

    conn = sqlite3.connect(str(DB_PATH))

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            created_at TEXT
        )
    """)

    conn.commit()

    dp = Dispatcher()

    dp.include_routers(
        user_commands.router,
        bot_messages.router,
    )

    await dp.start_polling(bot, conn=conn)

if __name__ == '__main__':
    asyncio.run(main())
