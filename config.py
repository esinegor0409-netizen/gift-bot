import os

# --- Настройки бота (Bot API) ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВЬ_СЮДА_ТОКЕН_ОТ_BOTFATHER")

# --- Настройки userbot-клиента (MTProto / Pyrogram) для сбора данных ---
# Получить api_id и api_hash на https://my.telegram.org
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "ВСТАВЬ_СЮДА_API_HASH")
# Номер телефона аккаунта, который будет собирать данные (не бот, а обычный юзер)
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "+79990000000")

# --- База данных ---
DB_PATH = os.getenv("DB_PATH", "gifts.db")

# --- Подписка (цена в Telegram Stars) ---
SUBSCRIPTION_STARS_PRICE = int(os.getenv("SUBSCRIPTION_STARS_PRICE", "0"))  # цена подписки в звёздах
SUBSCRIPTION_DAYS = int(os.getenv("SUBSCRIPTION_DAYS", "30"))  # срок действия подписки в днях

# Название твоего бота, отображается в текстах
BOT_NAME = os.getenv("BOT_NAME", "Gift Analytics Bot")
