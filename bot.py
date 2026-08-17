import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    LabeledPrice,
    PreCheckoutQuery,
)

import config
import database as db

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()


# ---------- Команды ----------

@dp.message(CommandStart())
async def cmd_start(message: Message):
    db.add_user_if_not_exists(message.from_user.id, message.from_user.username)
    await message.answer(
        f"Привет! Это {config.BOT_NAME} 🎁\n\n"
        "Я показываю аналитику по NFT-подаркам в Telegram: кто чем владеет, "
        "историю передачи подарков и поиск по коллекциям.\n\n"
        "Команды:\n"
        "/mygifts — мои подарки\n"
        "/find <название> — поиск подарка по названию\n"
        "/subscribe — оформить платную подписку\n"
        "/status — статус моей подписки"
    )


@dp.message(Command("status"))
async def cmd_status(message: Message):
    if db.is_subscribed(message.from_user.id):
        await message.answer("✅ У вас активна платная подписка.")
    else:
        await message.answer("❌ Подписка не активна. Оформить: /subscribe")


@dp.message(Command("mygifts"))
async def cmd_mygifts(message: Message):
    if not db.is_subscribed(message.from_user.id):
        await message.answer(
            "🔒 Эта функция доступна только по подписке.\n"
            "Оформите подписку: /subscribe"
        )
        return

    gifts = db.get_gifts_by_owner(message.from_user.id)
    if not gifts:
        await message.answer("У вас пока нет отслеженных подарков в базе.")
        return

    lines = [f"🎁 {g['gift_name']} #{g['collectible_number']}" for g in gifts]
    await message.answer("Ваши подарки:\n\n" + "\n".join(lines))


@dp.message(Command("find"))
async def cmd_find(message: Message):
    if not db.is_subscribed(message.from_user.id):
        await message.answer(
            "🔒 Поиск доступен только по подписке.\n"
            "Оформите подписку: /subscribe"
        )
        return

    query = message.text.replace("/find", "").strip()
    if not query:
        await message.answer("Использование: /find <название подарка>")
        return

    results = db.search_gift_by_name(query)
    if not results:
        await message.answer("Ничего не найдено.")
        return

    lines = [
        f"🎁 {g['gift_name']} #{g['collectible_number']} — владелец: @{g['owner_username'] or g['owner_id']}"
        for g in results
    ]
    await message.answer("Найдено:\n\n" + "\n".join(lines))


# ---------- Оплата через Telegram Stars ----------

@dp.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    prices = [LabeledPrice(label="Подписка на 30 дней", amount=config.SUBSCRIPTION_STARS_PRICE)]
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Подписка на аналитику подарков",
        description=f"Доступ ко всем функциям бота на {config.SUBSCRIPTION_DAYS} дней",
        payload="subscription_30_days",
        currency="XTR",  # XTR = Telegram Stars
        prices=prices,
        provider_token="",  # для Stars provider_token не нужен, оставить пустым
    )


@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    # Тут можно добавить свою валидацию перед подтверждением оплаты
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message(F.successful_payment)
async def process_successful_payment(message: Message):
    new_until = db.extend_subscription(message.from_user.id, config.SUBSCRIPTION_DAYS)
    await message.answer(
        f"✅ Оплата прошла успешно! Подписка активна до {new_until.strftime('%d.%m.%Y')}."
    )


# ---------- Запуск ----------

async def main():
    db.init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
