import asyncio
import sqlite3
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config_reader import config
from db import init_db
import admin_panel, user_commands, bot_messages

import os


async def main() -> None:
    print("1")
    from dotenv import load_dotenv

    load_dotenv()
    TOKEN = os.getenv('BOT_TOKEN')

    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    print("2")

    # Папка для БД — всегда рядом с этим файлом (main.py), независимо от того,
    # на Windows это, на Linux или в Docker. Раньше был захардкожен "/app/data",
    # что на Windows превращалось в C:\app\data и терялось из виду.
    DATA_DIR = Path(__file__).resolve().parent / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = DATA_DIR / "bot.db"

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    init_db(conn)

    dp = Dispatcher(storage=MemoryStorage())

    # Порядок важен: admin_panel первым, чтобы админ мог пользоваться
    # панелью, а обычные пользователи проваливались дальше по цепочке.
    dp.include_routers(
        admin_panel.router,
        user_commands.router,
        bot_messages.router,
    )

    await dp.start_polling(bot, conn=conn, admin_id=config.admin_id)


if __name__ == "__main__":
    asyncio.run(main())