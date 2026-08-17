from sqlite3 import Connection

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

import db

router = Router()

# Открыт ли бот для новых подписчиков.
# Переключай вручную перед/после запуска дропа.
preorder = True


@router.message(CommandStart())
async def start(message: Message, conn: Connection) -> None:
    is_new = db.add_user(conn, message.from_user.id, message.from_user.username)

    if is_new:
        print(f"Пользователь добавлен: {message.from_user.id}")
    else:
        print(f"Пользователь уже в базе: {message.from_user.id}")

    if preorder:
        await message.bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id="@testoport",
            message_id=2,
        )
    else:
        await message.answer("<b>Закрыто для посещения</b>\n\n")


@router.message(F.text == "База")
async def send_db_stats(message: Message, conn: Connection) -> None:
    total, active = db.get_users_count(conn)
    await message.answer(f"Всего пользователей: {total}\nАктивных: {active}")