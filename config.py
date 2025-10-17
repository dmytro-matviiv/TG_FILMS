# Налаштування Telegram бота для пошуку фільмів
import os

# Читаємо змінні середовища (для Railway) або використовуємо значення за замовчуванням (для локальної розробки)

# TOKEN від BotFather - ключ для керування ботом
BOT_TOKEN = os.getenv('BOT_TOKEN', '8301432144:AAEbEU80888MnxTFwQDzrNsq12u_O18Hmn8')

# Username каналу, на який треба підписатись
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', '@film_by_code')

# ID адміністратора (ваш Telegram ID)
ADMIN_ID = int(os.getenv('ADMIN_ID', '7028095858'))

# Pyrogram API credentials (отримайте на https://my.telegram.org/)
try:
    API_ID = int(os.getenv('API_ID', '20156012'))
except ValueError:
    API_ID = '20156012'

API_HASH = os.getenv('API_HASH', '2c8ade68fd2d202a3553e503a5e8125b')

# Номер телефону для Pyrogram (з кодом країни, наприклад: +380123456789)
PHONE_NUMBER = os.getenv('PHONE_NUMBER', '+380931082506')  # Ваш номер телефону