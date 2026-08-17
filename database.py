import sqlite3
import datetime
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Создаёт таблицы, если их ещё нет."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            subscribed_until TEXT,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS gifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gift_id TEXT,
            owner_id INTEGER,
            owner_username TEXT,
            gift_name TEXT,
            collectible_number INTEGER,
            first_seen_at TEXT,
            last_seen_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS gift_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gift_id TEXT,
            previous_owner_id INTEGER,
            new_owner_id INTEGER,
            changed_at TEXT
        )
    """)

    conn.commit()
    conn.close()


# ---------- Пользователи и подписки ----------

def add_user_if_not_exists(user_id: int, username: str | None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO users (user_id, username, subscribed_until, created_at) VALUES (?, ?, ?, ?)",
            (user_id, username, None, datetime.datetime.utcnow().isoformat()),
        )
        conn.commit()
    conn.close()


def is_subscribed(user_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT subscribed_until FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row is None or row["subscribed_until"] is None:
        return False
    until = datetime.datetime.fromisoformat(row["subscribed_until"])
    return until > datetime.datetime.utcnow()


def extend_subscription(user_id: int, days: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT subscribed_until FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    now = datetime.datetime.utcnow()
    if row and row["subscribed_until"]:
        current_until = datetime.datetime.fromisoformat(row["subscribed_until"])
        base = current_until if current_until > now else now
    else:
        base = now

    new_until = base + datetime.timedelta(days=days)
    cur.execute(
        "UPDATE users SET subscribed_until = ? WHERE user_id = ?",
        (new_until.isoformat(), user_id),
    )
    conn.commit()
    conn.close()
    return new_until


# ---------- Подарки ----------

def upsert_gift(gift_id: str, owner_id: int, owner_username: str, gift_name: str, collectible_number: int):
    """Добавляет подарок или обновляет владельца, если он изменился (пишет историю)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT owner_id FROM gifts WHERE gift_id = ?", (gift_id,))
    row = cur.fetchone()
    now = datetime.datetime.utcnow().isoformat()

    if row is None:
        cur.execute(
            """INSERT INTO gifts (gift_id, owner_id, owner_username, gift_name, collectible_number, first_seen_at, last_seen_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (gift_id, owner_id, owner_username, gift_name, collectible_number, now, now),
        )
    else:
        old_owner = row["owner_id"]
        if old_owner != owner_id:
            cur.execute(
                "INSERT INTO gift_history (gift_id, previous_owner_id, new_owner_id, changed_at) VALUES (?, ?, ?, ?)",
                (gift_id, old_owner, owner_id, now),
            )
        cur.execute(
            "UPDATE gifts SET owner_id = ?, owner_username = ?, last_seen_at = ? WHERE gift_id = ?",
            (owner_id, owner_username, now, gift_id),
        )

    conn.commit()
    conn.close()


def get_gifts_by_owner(owner_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM gifts WHERE owner_id = ?", (owner_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def search_gift_by_name(name_query: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM gifts WHERE gift_name LIKE ? LIMIT 20", (f"%{name_query}%",))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_gift_history(gift_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM gift_history WHERE gift_id = ? ORDER BY changed_at DESC", (gift_id,))
    rows = cur.fetchall()
    conn.close()
    return rows
