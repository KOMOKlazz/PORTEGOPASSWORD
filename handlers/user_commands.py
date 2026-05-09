from contextlib import suppress

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.enums import DiceEmoji
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from motor.core import AgnosticDatabase as MDB
from pymongo.errors import DuplicateKeyError

from sqlite3 import Connection

import datetime

router = Router()

preorder = True

@router.message(CommandStart())
@router.message(F.text == '🏠 Главная')
async def start(message: Message, conn: Connection):
    with suppress(DuplicateKeyError):
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE id = ?",
            (message.from_user.id,)
        )

        user = cursor.fetchone()

        if user is None:
            conn.execute(
                "INSERT INTO users (id, username, created_at) VALUES (?, ?, ?)",
                (
                    message.from_user.id,
                    message.from_user.username,
                    datetime.date.today()
                )
            )
            print('Пользователь добавлен')

            conn.commit()
        else:
            print('Пользователь уже в базе')

        conn.commit()
        if preorder == True:
            await message.bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id='@testoport',
                message_id=2,
            )
        else:
            await message.answer(
                f'<b>Закрыто для посещения</b>\n\n'
            )