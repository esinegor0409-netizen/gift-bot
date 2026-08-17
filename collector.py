"""
Сборщик данных о NFT-подарках через MTProto (Pyrogram).

Важно:
- Это работает через userbot-аккаунт (обычный номер телефона), а не через Bot API —
  у ботов нет доступа к этим данным.
- Используй с разумными задержками между запросами (см. SLEEP_BETWEEN_REQUESTS),
  чтобы не получить ограничения на аккаунте.
- Точные названия raw-методов (GetSavedStarGifts и т.п.) могут отличаться в
  зависимости от версии Pyrogram/Telegram API — на момент написания это актуальные
  методы для работы с подарками (star gifts). Если Pyrogram выдаст ошибку об
  отсутствии метода, проверь актуальную схему API на https://core.telegram.org/methods
  и обнови вызов ниже.
"""

import asyncio
import logging

from pyrogram import Client
from pyrogram.raw import functions

import config
import database as db

logging.basicConfig(level=logging.INFO)

SLEEP_BETWEEN_REQUESTS = 2  # секунды между запросами, чтобы не спамить API
SLEEP_BETWEEN_USERS = 5     # секунды между обработкой разных пользователей

app = Client(
    "gift_collector",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    phone_number=config.PHONE_NUMBER,
)


async def collect_gifts_for_user(client: Client, user_id: int, username: str | None):
    """Забирает список подарков конкретного пользователя и сохраняет в БД."""
    try:
        peer = await client.resolve_peer(user_id)
        result = await client.invoke(
            functions.payments.GetSavedStarGifts(
                peer=peer,
                offset="",
                limit=100,
            )
        )

        for entry in getattr(result, "gifts", []):
            gift = entry.gift
            gift_id = str(getattr(gift, "id", ""))
            gift_name = getattr(gift, "title", "Unknown Gift")
            collectible_number = getattr(gift, "num", 0)

            db.upsert_gift(
                gift_id=gift_id,
                owner_id=user_id,
                owner_username=username,
                gift_name=gift_name,
                collectible_number=collectible_number,
            )

        logging.info(f"Собрано подарков для пользователя {user_id}: {len(getattr(result, 'gifts', []))}")

    except Exception as e:
        logging.error(f"Ошибка при сборе подарков для {user_id}: {e}")

    await asyncio.sleep(SLEEP_BETWEEN_REQUESTS)


async def collect_for_user_list(user_ids: list[int]):
    """Проходит по списку user_id и собирает данные о подарках каждого."""
    async with app:
        for user_id in user_ids:
            try:
                user = await app.get_users(user_id)
                username = user.username
            except Exception:
                username = None

            await collect_gifts_for_user(app, user_id, username)
            await asyncio.sleep(SLEEP_BETWEEN_USERS)


if __name__ == "__main__":
    db.init_db()

    # Список пользователей, чьи подарки нужно отслеживать.
    # Например, можно подгружать этот список из своей таблицы users в базе.
    USER_IDS_TO_TRACK: list[int] = [
        # 123456789,
        # 987654321,
    ]

    if not USER_IDS_TO_TRACK:
        logging.warning(
            "Список USER_IDS_TO_TRACK пуст — добавь user_id пользователей, "
            "чьи подарки нужно отслеживать."
        )
    else:
        asyncio.run(collect_for_user_list(USER_IDS_TO_TRACK))
