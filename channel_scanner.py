# channel_scanner.py - Сканер каналу для автоматичного додавання фільмів
import asyncio
import re
import logging
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import FloodWait, AuthKeyUnregistered
import config
import database

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChannelScanner:
    """
    Клас для сканування каналу та автоматичного додавання фільмів
    """
    
    def __init__(self):
        self.client = None
        self.is_running = False
        self.waiting_for_code = False
        self.auth_state = None
        
    async def start(self):
        """Запуск Pyrogram клієнта"""
        try:
            # Перевіряємо чи налаштовано API
            if config.API_ID == 'YOUR_API_ID' or config.API_HASH == 'YOUR_API_HASH':
                logger.error("❌ API_ID або API_HASH не налаштовано!")
                return False
            
            # 🔍 ДЕТАЛЬНА ДІАГНОСТИКА API КЛЮЧІВ
            logger.info("🔧 Ініціалізую Pyrogram клієнт...")
            logger.info(f"📊 API_ID: {config.API_ID}")
            logger.info(f"📊 API_HASH: {config.API_HASH[:10]}...")
            logger.info(f"📊 PHONE_NUMBER: {config.PHONE_NUMBER}")
            
            # Перевіряємо чи API_ID є числом
            try:
                api_id_int = int(config.API_ID)
                logger.info(f"✅ API_ID валідний: {api_id_int}")
            except ValueError:
                logger.error(f"❌ API_ID не є числом: {config.API_ID}")
                return False
            
            self.client = Client(
                "film_scanner",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                phone_number=config.PHONE_NUMBER,
                in_memory=True  # Використовуємо пам'ять замість файлів
            )
            
            # Запускаємо клієнт без авторизації
            await self.client.connect()
            
            # Перевіряємо чи потрібна авторизація
            if not await self.client.is_user_authorized():
                logger.info("📱 Потрібна авторизація. Очікую код підтвердження...")
                self.waiting_for_code = True
                return "waiting_for_code"
            
            logger.info("✅ Pyrogram клієнт успішно запущено!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Помилка запуску Pyrogram: {e}")
            
            # 🔧 АВТОМАТИЧНЕ ВИДАЛЕННЯ SESSION ФАЙЛІВ ПРИ ПОМИЛЦІ АВТОРИЗАЦІЇ
            if "AUTH_KEY_UNREGISTERED" in str(e):
                logger.info("🧹 Видаляю невалідні session файли...")
                try:
                    import os
                    session_files = ["film_scanner.session", "film_scanner.session-journal"]
                    for file in session_files:
                        if os.path.exists(file):
                            os.remove(file)
                            logger.info(f"✅ Видалено: {file}")
                except Exception as cleanup_error:
                    logger.error(f"❌ Не вдалося видалити session файли: {cleanup_error}")
            
            self.client = None  # Скидаємо клієнт при помилці
            return False
    
    async def complete_auth(self, code):
        """Завершення авторизації з кодом"""
        try:
            if not self.client or not self.waiting_for_code:
                return False, "Клієнт не готовий до авторизації"
            
            # Відправляємо код підтвердження
            await self.client.sign_in(code)
            
            self.waiting_for_code = False
            logger.info("✅ Авторизація успішна!")
            return True, "Авторизація завершена"
            
        except Exception as e:
            logger.error(f"❌ Помилка авторизації: {e}")
            return False, str(e)
    
    async def stop(self):
        """Зупинка Pyrogram клієнта"""
        if self.client:
            await self.client.stop()
            logger.info("STOP Pyrogram клієнт зупинено!")
    
    def parse_movie_info(self, text: str) -> dict:
        """
        Парсить інформацію про фільм з тексту поста
        
        Очікуваний формат:
        Код: 002
        Назва: Голови держав
        Рік: 2025
        Опис: Опис фільму...
        """
        movie_info = {
            'code': None,
            'title': None,
            'year': None,
            'description': None
        }
        
        if not text:
            return movie_info
        
        # Шукаємо код
        code_match = re.search(r'[Кк][Оо][Дд]:\s*([A-Za-z0-9]+)', text)
        if code_match:
            movie_info['code'] = code_match.group(1).upper()
        
        # Шукаємо назву
        title_match = re.search(r'[Нн][Аа][Зз][Вв][Аа]:\s*(.+)', text)
        if title_match:
            movie_info['title'] = title_match.group(1).strip()
        
        # Шукаємо рік
        year_match = re.search(r'[Рр][Іі][Кк]:\s*(\d{4})', text)
        if year_match:
            movie_info['year'] = year_match.group(1)
        
        # Шукаємо опис
        desc_match = re.search(r'[Оо][Пп][Ии][Сс]:\s*(.+)', text, re.DOTALL)
        if desc_match:
            movie_info['description'] = desc_match.group(1).strip()
        
        return movie_info
    
    async def scan_channel_history(self):
        """
        Сканує всю історію каналу та додає фільми в базу
        """
        try:
            logger.info("SCAN Починаю сканування каналу...")
            
            # Перевіряємо чи клієнт ініціалізовано
            if not self.client:
                logger.error("❌ Pyrogram клієнт не ініціалізовано!")
                return 0
            
            # Отримуємо інформацію про канал
            channel_username = config.CHANNEL_USERNAME.lstrip('@')
            channel = await self.client.get_chat(f"@{channel_username}")
            
            logger.info(f"CHANNEL Сканування каналу: {channel.title} (ID: {channel.id})")
            
            movies_added = 0
            messages_processed = 0
            
            # Отримуємо всі повідомлення з каналу
            async for message in self.client.get_chat_history(channel.id):
                messages_processed += 1
                
                # Перевіряємо чи це пост з фільмом
                if message.text or message.caption:
                    text = message.text or message.caption
                    movie_info = self.parse_movie_info(text)
                    
                    # Якщо знайшли код фільму
                    if movie_info['code']:
                        # Додаємо в базу даних
                        success = database.add_movie(
                            code=movie_info['code'],
                            message_id=message.id,
                            chat_id=channel.id,
                            link=None  # Можна додати пошук посилань
                        )
                        
                        if success:
                            movies_added += 1
                            logger.info(f"OK Додано фільм: {movie_info['code']} - {movie_info['title']}")
                        else:
                            logger.warning(f"WARN Фільм {movie_info['code']} вже існує в базі")
                
                # Логуємо прогрес кожні 10 повідомлень
                if messages_processed % 10 == 0:
                    logger.info(f"PROGRESS Оброблено: {messages_processed} повідомлень, додано: {movies_added} фільмів")
            
            logger.info(f"DONE Сканування завершено!")
            logger.info(f"SUMMARY Підсумок: оброблено {messages_processed} повідомлень, додано {movies_added} фільмів")
            
            return movies_added
            
        except Exception as e:
            logger.error(f"❌ Помилка сканування каналу: {e}")
            return 0
    
    async def monitor_new_posts(self):
        """
        Моніторинг нових постів в реальному часі
        """
        try:
            logger.info("MONITOR Починаю моніторинг нових постів...")
            
            # Перевіряємо чи клієнт ініціалізовано
            if not self.client:
                logger.error("❌ Pyrogram клієнт не ініціалізовано для моніторингу!")
                return
            
            channel_username = config.CHANNEL_USERNAME.lstrip('@')
            channel = await self.client.get_chat(f"@{channel_username}")
            
            # Слухаємо нові повідомлення в каналі
            async for message in self.client.get_chat_history(channel.id, limit=1):
                # Це буде останнє повідомлення
                pass
            
            # Тепер слухаємо нові повідомлення
            @self.client.on_message()
            async def handle_new_message(client, message: Message):
                # Перевіряємо чи це наш канал
                if message.chat.id == channel.id:
                    # Перевіряємо чи це пост з фільмом
                    if message.text or message.caption:
                        text = message.text or message.caption
                        movie_info = self.parse_movie_info(text)
                        
                        # Якщо знайшли код фільму
                        if movie_info['code']:
                            # Додаємо в базу даних
                            success = database.add_movie(
                                code=movie_info['code'],
                                message_id=message.id,
                                chat_id=channel.id,
                                link=None
                            )
                            
                            if success:
                                logger.info(f"NEW Новий фільм додано: {movie_info['code']} - {movie_info['title']}")
                            else:
                                logger.warning(f"WARN Фільм {movie_info['code']} вже існує в базі")
            
            # Запускаємо моніторинг
            # await self.client.idle()  # Цей метод не існує в новій версії Pyrogram
            # Замість цього використовуємо нескінченний цикл
            while True:
                await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ Помилка моніторингу: {e}")
    
    async def run_full_scan(self):
        """
        Повне сканування: історія + моніторинг нових постів
        """
        try:
            # Спочатку скануємо історію
            movies_count = await self.scan_channel_history()
            
            if movies_count > 0:
                logger.info(f"✅ Сканування завершено! Додано {movies_count} фільмів")
            else:
                logger.info("ℹ️ Нові фільми не знайдено")
            
            # Потім запускаємо моніторинг
            logger.info("👂 Запускаю моніторинг нових постів...")
            await self.monitor_new_posts()
            
        except Exception as e:
            logger.error(f"❌ Помилка повного сканування: {e}")

# Глобальний екземпляр сканера
scanner = ChannelScanner()

async def start_scanner():
    """Запуск сканера"""
    success = await scanner.start()
    if success:
        await scanner.run_full_scan()
    else:
        logger.error("❌ Не вдалося запустити сканер")

async def stop_scanner():
    """Зупинка сканера"""
    await scanner.stop()

if __name__ == "__main__":
    # Тестовий запуск
    asyncio.run(start_scanner())
