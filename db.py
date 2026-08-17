import datetime
from sqlite3 import Connection, Row
from typing import Optional


def init_db(conn: Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            created_at TEXT,
            is_active INTEGER NOT NULL DEFAULT 1
        )
    """)

    # Черновик поста — всегда одна строка с id=1 (панель одна, редактор один).
    conn.execute("""
        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            channel_chat_id TEXT,
            message_id INTEGER,
            button_text TEXT,
            button_url TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()


# --- users ---

def add_user(conn: Connection, user_id: int, username: Optional[str]) -> bool:
    """Добавляет пользователя, если его нет. Возвращает True, если он новый."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    existing = cursor.fetchone()

    if existing is None:
        conn.execute(
            "INSERT INTO users (id, username, created_at, is_active) VALUES (?, ?, ?, 1)",
            (user_id, username, datetime.date.today().isoformat()),
        )
        conn.commit()
        return True

    # Если пользователь раньше заблокировал бота и вернулся — реактивируем.
    conn.execute("UPDATE users SET is_active = 1, username = ? WHERE id = ?", (username, user_id))
    conn.commit()
    return False


def get_active_users(conn: Connection) -> list[int]:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE is_active = 1")
    return [row[0] for row in cursor.fetchall()]


def deactivate_user(conn: Connection, user_id: int) -> None:
    conn.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
    conn.commit()


def get_users_count(conn: Connection) -> tuple[int, int]:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    active = cursor.fetchone()[0]
    return total, active


def get_all_users_raw(conn: Connection) -> list[Row]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()


# --- drafts ---

def save_draft_post(conn: Connection, channel_chat_id: str, message_id: int) -> None:
    """Сохраняет новый пост в черновик, кнопка при этом сбрасывается."""
    conn.execute("""
        INSERT INTO drafts (id, channel_chat_id, message_id, button_text, button_url, updated_at)
        VALUES (1, ?, ?, NULL, NULL, ?)
        ON CONFLICT(id) DO UPDATE SET
            channel_chat_id = excluded.channel_chat_id,
            message_id = excluded.message_id,
            button_text = NULL,
            button_url = NULL,
            updated_at = excluded.updated_at
    """, (channel_chat_id, message_id, datetime.datetime.now().isoformat()))
    conn.commit()


def save_draft_button(conn: Connection, text: str, url: str) -> None:
    """Ставит кнопку на текущий черновик (максимум одна — старая заменяется)."""
    conn.execute(
        "UPDATE drafts SET button_text = ?, button_url = ?, updated_at = ? WHERE id = 1",
        (text, url, datetime.datetime.now().isoformat()),
    )
    conn.commit()


def clear_draft_button(conn: Connection) -> None:
    conn.execute("UPDATE drafts SET button_text = NULL, button_url = NULL WHERE id = 1")
    conn.commit()


def get_draft(conn: Connection) -> Optional[Row]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drafts WHERE id = 1")
    return cursor.fetchone()