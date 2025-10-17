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
    API_ID = int(os.getenv('API_ID', 'YOUR_API_ID'))
except ValueError:
    API_ID = 'YOUR_API_ID'

API_HASH = os.getenv('API_HASH', 'YOUR_API_HASH')

# Номер телефону для Pyrogram (з кодом країни, наприклад: +380123456789)
PHONE_NUMBER = os.getenv('PHONE_NUMBER', '+380931082506')  # Ваш номер телефону