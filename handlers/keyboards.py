from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_panel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактор следующего сообщения", callback_data="panel:editor")
    builder.button(text="📋 Список пользователей", callback_data="panel:user_list")
    builder.adjust(1)
    return builder.as_markup()


def editor_menu_kb(has_draft: bool, has_button: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Найти пост по ссылке", callback_data="editor:find_post")

    if has_draft:
        btn_label = "🔘 Изменить кнопку" if has_button else "🔘 Добавить кнопку"
        builder.button(text=btn_label, callback_data="editor:set_button")

        if has_button:
            builder.button(text="🗑 Убрать кнопку", callback_data="editor:remove_button")

        builder.button(text="📤 Отправить всем", callback_data="editor:broadcast")

    builder.button(text="⬅️ Назад", callback_data="panel:back")
    builder.adjust(1)
    return builder.as_markup()


def confirm_broadcast_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, отправить", callback_data="broadcast:confirm")
    builder.button(text="❌ Отмена", callback_data="broadcast:cancel")
    builder.adjust(2)
    return builder.as_markup()


def cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="editor:cancel")
    builder.adjust(1)
    return builder.as_markup()


def back_to_panel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="panel:back")
    builder.adjust(1)
    return builder.as_markup()


def draft_button_markup(draft):
    """Инлайн-кнопка, которая будет прикреплена к посту при рассылке."""
    if draft and draft["button_text"] and draft["button_url"]:
        builder = InlineKeyboardBuilder()
        builder.button(text=draft["button_text"], url=draft["button_url"])
        return builder.as_markup()
    return None