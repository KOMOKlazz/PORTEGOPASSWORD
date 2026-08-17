import asyncio
from sqlite3 import Connection

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import db
from filters import IsAdmin
from keyboards import (
    back_to_panel_kb,
    cancel_kb,
    confirm_broadcast_kb,
    draft_button_markup,
    editor_menu_kb,
    main_panel_kb,
)
from states import DraftPostStates
from utils import parse_post_link

router = Router()

# Весь роутер доступен только админу. Если апдейт не от него —
# aiogram передаст его дальше, в user_commands / bot_messages.
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


# Задержка между сообщениями при рассылке.
# 0.05с ≈ 20 сообщений/сек — с запасом от общего лимита Telegram (~30/сек).
BROADCAST_DELAY = 0.05

# Лимит Telegram на длину сообщения — 4096 символов, берём с запасом.
MAX_MESSAGE_CHARS = 3500


def _draft_preview_text(draft) -> str:
    if draft is None or draft["message_id"] is None:
        return "Черновик пуст. Сначала найди пост по ссылке."

    lines = [f"Пост: {draft['channel_chat_id']} / сообщение {draft['message_id']}"]

    if draft["button_text"] and draft["button_url"]:
        lines.append(f"Кнопка: «{draft['button_text']}» → {draft['button_url']}")
    else:
        lines.append("Кнопка: не добавлена")

    return "\n".join(lines)


def _has_draft_and_button(draft) -> tuple[bool, bool]:
    has_draft = draft is not None and draft["message_id"] is not None
    has_button = has_draft and bool(draft["button_text"]) and bool(draft["button_url"])
    return has_draft, has_button


# --- открытие панели ---

@router.message(Command("panel"))
async def open_panel(message: Message) -> None:
    await message.answer("<b>Панель управления PORTEGO</b>", reply_markup=main_panel_kb())


@router.callback_query(F.data == "panel:back")
async def back_to_panel(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text("<b>Панель управления PORTEGO</b>", reply_markup=main_panel_kb())
    await call.answer()


@router.callback_query(F.data == "panel:editor")
async def open_editor(call: CallbackQuery, conn: Connection) -> None:
    draft = db.get_draft(conn)
    has_draft, has_button = _has_draft_and_button(draft)

    text = "<b>Редактор следующего сообщения</b>\n\n" + _draft_preview_text(draft)
    await call.message.edit_text(text, reply_markup=editor_menu_kb(has_draft, has_button))
    await call.answer()


# --- список пользователей ---

@router.callback_query(F.data == "panel:user_list")
async def send_user_list(call: CallbackQuery, conn: Connection) -> None:
    users = db.get_all_users_list(conn)

    if not users:
        await call.answer("В базе пока нет пользователей", show_alert=True)
        return

    await call.answer()

    lines = []
    for i, user in enumerate(users, start=1):
        name = user["full_name"] or "(без имени)"
        username = f"@{user['username']}" if user["username"] else "без ника"
        mark = "" if user["is_active"] else " ❌"
        lines.append(f"{i}. {name} — {username}{mark}")

    header = f"<b>Пользователи ({len(users)})</b>\n❌ — заблокировал бота\n\n"

    chunk = header
    for line in lines:
        # +1 на перевод строки
        if len(chunk) + len(line) + 1 > MAX_MESSAGE_CHARS:
            await call.message.answer(chunk)
            chunk = ""
        chunk += line + "\n"

    if chunk.strip():
        await call.message.answer(chunk)

    await call.message.answer("Готово.", reply_markup=back_to_panel_kb())


# --- поиск поста по ссылке ---

@router.callback_query(F.data == "editor:find_post")
async def ask_post_link(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(DraftPostStates.waiting_post_link)
    await call.message.edit_text(
        "Пришли ссылку на пост в канале, например:\n"
        "<code>https://t.me/portegoclo/123</code>",
        reply_markup=cancel_kb(),
    )
    await call.answer()


@router.message(DraftPostStates.waiting_post_link)
async def receive_post_link(message: Message, conn: Connection, state: FSMContext) -> None:
    parsed = parse_post_link(message.text or "")
    if parsed is None:
        await message.answer(
            "Не смог разобрать ссылку. Формат: <code>https://t.me/channel/123</code>",
            reply_markup=cancel_kb(),
        )
        return

    chat_id, message_id = parsed

    try:
        await message.bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=chat_id,
            message_id=message_id,
        )
    except Exception:
        await message.answer(
            "Не получилось найти это сообщение. Проверь ссылку и что бот "
            "добавлен в канал (для приватных каналов — обязательно как админ).",
            reply_markup=cancel_kb(),
        )
        return

    db.save_draft_post(conn, chat_id, message_id)
    await state.clear()

    draft = db.get_draft(conn)
    await message.answer(
        "Пост сохранён как черновик.\n\n" + _draft_preview_text(draft),
        reply_markup=editor_menu_kb(True, False),
    )


# --- кнопка ---

@router.callback_query(F.data == "editor:set_button")
async def ask_button_text(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(DraftPostStates.waiting_button_text)
    await call.message.edit_text("Введи текст кнопки:", reply_markup=cancel_kb())
    await call.answer()


@router.message(DraftPostStates.waiting_button_text)
async def receive_button_text(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Текст не может быть пустым. Введи текст кнопки:", reply_markup=cancel_kb())
        return

    await state.update_data(button_text=text)
    await state.set_state(DraftPostStates.waiting_button_url)
    await message.answer(
        "Теперь пришли ссылку для кнопки (полный URL, начиная с https://):",
        reply_markup=cancel_kb(),
    )


@router.message(DraftPostStates.waiting_button_url)
async def receive_button_url(message: Message, conn: Connection, state: FSMContext) -> None:
    url = (message.text or "").strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        await message.answer(
            "Похоже на невалидную ссылку. Нужен полный URL, начиная с https://",
            reply_markup=cancel_kb(),
        )
        return

    data = await state.get_data()
    button_text = data.get("button_text", "Подробнее")

    db.save_draft_button(conn, button_text, url)
    await state.clear()

    draft = db.get_draft(conn)
    await message.answer(
        "Кнопка сохранена (заменяет предыдущую, если была).\n\n" + _draft_preview_text(draft),
        reply_markup=editor_menu_kb(True, True),
    )


@router.callback_query(F.data == "editor:remove_button")
async def remove_button(call: CallbackQuery, conn: Connection) -> None:
    db.clear_draft_button(conn)
    draft = db.get_draft(conn)
    await call.message.edit_text(
        "Кнопка убрана.\n\n" + _draft_preview_text(draft),
        reply_markup=editor_menu_kb(True, False),
    )
    await call.answer()


@router.callback_query(F.data == "editor:cancel")
async def cancel_editor_step(call: CallbackQuery, conn: Connection, state: FSMContext) -> None:
    await state.clear()
    draft = db.get_draft(conn)
    has_draft, has_button = _has_draft_and_button(draft)
    await call.message.edit_text(
        "<b>Редактор следующего сообщения</b>\n\n" + _draft_preview_text(draft),
        reply_markup=editor_menu_kb(has_draft, has_button),
    )
    await call.answer()


# --- рассылка ---

@router.callback_query(F.data == "editor:broadcast")
async def ask_broadcast_confirm(call: CallbackQuery, conn: Connection) -> None:
    total, active = db.get_users_count(conn)
    eta_sec = active * BROADCAST_DELAY

    await call.message.edit_text(
        "Отправить этот пост всем пользователям?\n\n"
        f"Активных получателей: <b>{active}</b> из {total}\n"
        f"Примерное время: ~{eta_sec:.0f} сек",
        reply_markup=confirm_broadcast_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "broadcast:cancel")
async def cancel_broadcast(call: CallbackQuery, conn: Connection) -> None:
    draft = db.get_draft(conn)
    _, has_button = _has_draft_and_button(draft)
    await call.message.edit_text(
        "Рассылка отменена.\n\n" + _draft_preview_text(draft),
        reply_markup=editor_menu_kb(True, has_button),
    )
    await call.answer()


@router.callback_query(F.data == "broadcast:confirm")
async def run_broadcast(call: CallbackQuery, conn: Connection, bot: Bot) -> None:
    draft = db.get_draft(conn)
    if draft is None or draft["message_id"] is None:
        await call.answer("Черновик пуст", show_alert=True)
        return

    await call.message.edit_text("Рассылка запущена, это может занять время…")
    await call.answer()

    reply_markup = draft_button_markup(draft)
    users = db.get_active_users(conn)

    sent = 0
    failed = 0

    for user_id in users:
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=draft["channel_chat_id"],
                message_id=draft["message_id"],
                reply_markup=reply_markup,
            )
            sent += 1
        except Exception:
            # Чаще всего — пользователь заблокировал бота. Деактивируем,
            # чтобы следующие рассылки на него не тратили время.
            failed += 1
            db.deactivate_user(conn, user_id)

        await asyncio.sleep(BROADCAST_DELAY)

    await call.message.answer(
        f"Рассылка завершена.\nОтправлено: {sent}\nНе доставлено: {failed}"
    )