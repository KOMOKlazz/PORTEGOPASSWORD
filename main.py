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


async def main() -> None:
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    DATA_DIR = Path("/app/data")
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