import re
from typing import Optional, Tuple


def parse_post_link(text: str) -> Optional[Tuple[str, int]]:
    """
    Разбирает ссылку на сообщение в Telegram-канале.

    Поддерживает:
      https://t.me/channelusername/123   (публичный канал)
      t.me/channelusername/123
      https://t.me/c/1234567890/123      (приватный канал, внутренний ID)

    Возвращает (chat_id_для_api, message_id) либо None, если не распознано.
    """
    text = text.strip()

    match = re.match(r"^(?:https?://)?t\.me/c/(\d+)/(\d+)$", text)
    if match:
        internal_id, message_id = match.groups()
        chat_id = f"-100{internal_id}"
        return chat_id, int(message_id)

    match = re.match(r"^(?:https?://)?t\.me/([A-Za-z0-9_]{5,32})/(\d+)$", text)
    if match:
        username, message_id = match.groups()
        return f"@{username}", int(message_id)

    return None