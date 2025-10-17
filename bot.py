# bot.py - Головний файл Telegram бота для пошуку фільмів

# Імпортуємо необхідні бібліотеки
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import logging
import re  # Для пошуку коду в тексті

# Імпортуємо наші власні файли
import config
import database
from channel_scanner import scanner

# Налаштування логування (щоб бачити що відбувається)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ========== ФУНКЦІЯ ПЕРЕВІРКИ ПІДПИСКИ ==========

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Перевіряє, чи користувач підписаний на канал.
    
    Параметри:
    - user_id: Telegram ID користувача
    - context: контекст бота (для доступу до API)
    
    Повертає:
    - True: якщо підписаний
    - False: якщо НЕ підписаний
    """
    try:
        # Отримуємо інформацію про користувача в каналі
        member = await context.bot.get_chat_member(
            chat_id=config.CHANNEL_USERNAME,
            user_id=user_id
        )
        
        # Перевіряємо статус користувача
        # Статуси: 'creator' (власник), 'administrator' (адмін), 'member' (учасник)
        # 'left' (вийшов), 'kicked' (забанений)
        
        if member.status in ['creator', 'administrator', 'member']:
            return True  # Користувач підписаний
        else:
            return False  # Користувач НЕ підписаний
            
    except Exception as e:
        # Якщо виникла помилка (наприклад, канал не знайдено)
        logger.error(f"Помилка при перевірці підписки: {e}")
        return False


# ========== КОМАНДА /START ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник команди /start
    Це перше, що бачить користувач при запуску бота
    """
    user = update.effective_user  # Отримуємо дані користувача
    
    # Перевіряємо підписку
    is_subscribed = await check_subscription(user.id, context)
    
    if is_subscribed:
        # Якщо підписаний - показуємо привітання
        welcome_text = f"""
Привіт, {user.first_name}! 👋

Ласкаво просимо до бота пошуку фільмів!

Як користуватись:
1. Знайдіть код фільму в TikTok відео
2. Надішліть мені цей код (наприклад: F001)
3. Я знайду назву та опис фільму

Просто надішліть код фільму!
"""
        await update.message.reply_text(welcome_text)
    else:
        # Якщо НЕ підписаний - просимо підписатись
        # Створюємо кнопку з посиланням на канал
        keyboard = [
            [InlineKeyboardButton("Підписатись на канал", url=f"https://t.me/{config.CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("Я підписався ✓", callback_data="check_subscription")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        subscribe_text = f"""
Щоб користуватисьботом, потрібно підписатись на наш канал!

Канал: {config.CHANNEL_USERNAME}

Там ви знайдете:
- Коди фільмів з TikTok
- Цікаві підбірки
- Новинки кіно

Після підписки натисніть "Я підписався ✓"
"""
        await update.message.reply_text(subscribe_text, reply_markup=reply_markup)


# ========== ОБРОБКА НАТИСКАННЯ КНОПКИ "Я ПІДПИСАВСЯ" ==========

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляє натискання на кнопки (callback queries)
    """
    query = update.callback_query
    await query.answer()  # Підтверджуємо натискання
    
    if query.data == "check_subscription":
        # Користувач натиснув "Я підписався"
        user = query.from_user
        
        # Перевіряємо підписку ще раз
        is_subscribed = await check_subscription(user.id, context)
        
        if is_subscribed:
            # Підписка підтверджена!
            success_text = f"""
Дякую за підписку, {user.first_name}! ✓

Тепер ви можете користуватись ботом!

Надішліть мені код фільму (наприклад: F001)
"""
            await query.edit_message_text(success_text)
        else:
            # Все ще не підписаний - показуємо помилку АЛЕ зберігаємо кнопки
            error_text = """
Здається, ви ще не підписались на канал 😔

Будь ласка:
1. Натисніть кнопку "Підписатись на канал"
2. Підпишіться на канал
3. Поверніться сюди та натисніть "Я підписався ✓"
"""
            
            # Зберігаємо кнопки для повторної спроби
            keyboard = [
                [InlineKeyboardButton("Підписатись на канал", url=f"https://t.me/{config.CHANNEL_USERNAME[1:]}")],
                [InlineKeyboardButton("Я підписався ✓", callback_data="check_subscription")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(error_text, reply_markup=reply_markup)
    
    elif query.data == "refresh_database":
        # Користувач натиснув "Оновити" в панелі бази даних
        user = query.from_user
        
        if user.id != config.ADMIN_ID:
            await query.edit_message_text("Ця функція доступна тільки адміністратору!")
            return
        
        # Оновлюємо список фільмів
        movies = database.get_all_movies()
        
        if not movies:
            await query.edit_message_text(
                "База даних порожня!\n\n"
                "Публікуйте пости в канал з текстом 'Код: 001'"
            )
            return
        
        # Формуємо новий список
        text = f"📊 База даних фільмів ({len(movies)} фільмів)\n\n"
        
        # Словник з назвами фільмів
        movie_titles = {
            '001': 'Ніхто2',
            '002': 'Голови держав'
        }
        
        for i, movie in enumerate(movies, 1):
            # Отримуємо назву з нашого словника
            title = movie_titles.get(movie['code'], 'Невідома назва')
            text += f"{i}. **{movie['code']}** - {title}\n"
        
        # Створюємо кнопки
        keyboard = []
        for i in range(0, len(movies), 2):
            row = []
            for j in range(2):
                if i + j < len(movies):
                    movie = movies[i + j]
                    row.append(InlineKeyboardButton(
                        f"🗑️ {movie['code']}", 
                        callback_data=f"delete_{movie['code']}"
                    ))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔄 Оновити", callback_data="refresh_database")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif query.data.startswith("delete_"):
        # Користувач натиснув кнопку видалення фільму
        user = query.from_user
        
        if user.id != config.ADMIN_ID:
            await query.edit_message_text("Ця функція доступна тільки адміністратору!")
            return
        
        # Отримуємо код фільму
        code = query.data.replace("delete_", "")
        
        # Видаляємо фільм
        success = database.delete_movie(code)
        
        if success:
            await query.edit_message_text(f"✅ Фільм з кодом {code} видалено!")
        else:
            await query.edit_message_text(f"❌ Фільм з кодом {code} не знайдено!")


# ========== АВТОМАТИЧНЕ ЗЧИТУВАННЯ ПОСТІВ З КАНАЛУ ==========

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ОПТИМІЗОВАНА ФУНКЦІЯ! Автоматично зчитує пости з каналу.
    
    Очікуваний формат поста:
    ---
    [ФОТО]
    Код: F001
    Назва: Inception
    Рік: 2010
    
    Опис:
    Фільм про сни в снах
    ---
    
    Бот автоматично:
    1. Читає пост з каналу
    2. Знаходить "Код: F001"
    3. Зберігає в базу даних
    4. Надсилає підтвердження адміну
    """
    # Отримуємо інформацію про пост
    post = update.channel_post
    
    if not post:
        return
    
    # Перевіряємо чи це наш канал
    if post.chat.username != config.CHANNEL_USERNAME.replace("@", ""):
        logger.info(f"Пост з іншого каналу (@{post.chat.username}), ігноруємо")
        return
    
    # Отримуємо текст з поста
    # Якщо є фото - текст буде в caption, якщо тільки текст - в text
    text = post.caption or post.text or ""
    
    if not text:
        logger.info("⚠️ Пост без тексту, пропускаємо")
        return
    
    # Шукаємо код в тексті: "Код: F001" (регістр не важливий)
    match = re.search(r'[Кк][Оо][Дд]:\s*([A-Za-z0-9]+)', text)
    
    if match:
        code = match.group(1).upper()  # F001
        message_id = post.message_id
        chat_id = post.chat_id
        
        # Додатково шукаємо назву (опціонально, для логів)
        title_match = re.search(r'[Нн][Аа][Зз][Вв][Аа]:\s*(.+)', text)
        title = title_match.group(1).strip() if title_match else "Невідома"
        
        # Шукаємо посилання в тексті
        # Формати: "Посилання: https://...", "Link: https://...", "Ссылка: https://..."
        link_match = re.search(r'(?:[Пп][Оо][Сс][Ии][Лл][Аа][Нн][Нн][Яя]|[Лл][Ии][Нн][Кк]|[Сс][Сс][Ыы][Лл][Кк][Аа]):\s*(https?://[^\s]+)', text)
        link = link_match.group(1) if link_match else None
        
        # Зберігаємо в базу
        success = database.add_movie(code, message_id, chat_id, link)
        
        if success:
            # Формуємо повідомлення для логу
            log_message = f"Автоматично додано: {code} - {title} (msg_id: {message_id})"
            logger.info(log_message)
            
            # 🔔 НАДСИЛАЄМО ПІДТВЕРДЖЕННЯ АДМІНУ
            try:
                confirmation_text = f"""
Фільм успішно додано в базу!

Код: {code}
Назва: {title}
Message ID: {message_id}
Посилання: {link if link else 'Не вказано'}

Користувачі тепер можуть знайти його за кодом {code}
"""
                await context.bot.send_message(
                    chat_id=config.ADMIN_ID,
                    text=confirmation_text
                )
            except Exception as e:
                logger.error(f"Не вдалося надіслати підтвердження адміну: {e}")
                
        else:
            # Код вже існує
            logger.warning(f"Код {code} вже існує в базі! Пост НЕ додано.")
            
            # Повідомляємо адміну про дублікат
            try:
                await context.bot.send_message(
                    chat_id=config.ADMIN_ID,
                    text=f"Помилка! Код {code} вже існує в базі.\n\nВиберіть інший код або видаліть старий: /delete {code}"
                )
            except Exception as e:
                logger.error(f"Не вдалося надіслати попередження адміну: {e}")
    else:
        logger.info("Код не знайдено в пості (не має 'Код: ...')")


# ========== ПОШУК ФІЛЬМУ ЗА КОДОМ ==========

async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляє текстові повідомлення від користувача
    Якщо це код фільму - шукає його в базі
    """
    user = update.effective_user
    message_text = update.message.text.strip().upper()  # Отримуємо текст і переводимо в великі літери
    
    # Перевіряємо підписку
    is_subscribed = await check_subscription(user.id, context)
    
    if not is_subscribed:
        # Якщо не підписаний - показуємо повідомлення про підписку
        subscribe_text = f"""
Щоб користуватись ботом, потрібно підписатись на наш канал!

Канал: {config.CHANNEL_USERNAME}

Там ви знайдете:
- Коди фільмів з TikTok
- Цікаві підбірки  
- Новинки кіно

Після підписки натисніть "Я підписався ✓"
"""
        keyboard = [
            [InlineKeyboardButton("Підписатись на канал", url=f"https://t.me/{config.CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("Я підписався ✓", callback_data="check_subscription")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(subscribe_text, reply_markup=reply_markup)
        return
    
    # Шукаємо фільм в базі даних
    movie = database.find_movie(message_text)
    
    if movie:
        # Фільм знайдено! Пересилаємо пост з каналу
        try:
            # Копіюємо повідомлення з каналу (з фото, текстом, всім!)
            await context.bot.copy_message(
                chat_id=update.effective_chat.id,
                from_chat_id=movie['chat_id'],
                message_id=movie['message_id']
            )
            
            # Якщо є посилання - додаємо кнопку
            if movie.get('link'):
                keyboard = [
                    [InlineKeyboardButton("🔗 Дивитись фільм", url=movie['link'])]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "Натисніть кнопку щоб перейти до фільму:",
                    reply_markup=reply_markup
                )
            
            logger.info(f"Користувач {user.id} знайшов фільм {message_text}")
            
        except Exception as e:
            # Якщо виникла помилка (наприклад, пост видалено або неправильний message_id)
            logger.error(f"Помилка при копіюванні поста: {e}")
            
            # Видаляємо фільм з бази даних, бо він невалідний
            database.delete_movie(message_text)
            
            await update.message.reply_text(
                f"❌ Помилка! Пост для фільму {message_text} не знайдено в каналі.\n\n"
                f"Фільм видалено з бази даних.\n\n"
                f"Адміністратор має опублікувати його заново в канал {config.CHANNEL_USERNAME}"
            )
            
            # Повідомляємо адміну
            try:
                await context.bot.send_message(
                    chat_id=config.ADMIN_ID,
                    text=f"⚠️ Користувач спробував знайти фільм {message_text}, але пост не знайдено!\n\n"
                         f"Фільм видалено з бази. Опублікуйте його заново в канал."
                )
            except:
                pass
    else:
        # Фільм не знайдено
        not_found_text = f"""
Фільм з кодом "{message_text}" не знайдено 😔

Можливі причини:
- Код введено неправильно
- Фільм ще не додано в базу

Перевірте код та спробуйте ще раз!
"""
        await update.message.reply_text(not_found_text)


# ========== АДМІНІСТРАТИВНІ КОМАНДИ ==========

async def add_movie_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /add - ручне додавання фільму (тільки для адміністратора)
    Формат: /add КОД MESSAGE_ID
    Приклад: /add 001 123
    
    Щоб знайти MESSAGE_ID:
    1. Відкрийте пост в каналі через браузер
    2. Подивіться на URL: t.me/channel_name/123 (де 123 - це MESSAGE_ID)
    """
    user = update.effective_user
    
    if user.id != config.ADMIN_ID:
        await update.message.reply_text("Ця команда доступна тільки адміністратору!")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Неправильний формат!\n\n"
            "Формат: /add КОД MESSAGE_ID\n"
            "Приклад: /add 001 123\n\n"
            "Щоб знайти MESSAGE_ID:\n"
            "1. Відкрийте пост в каналі через браузер\n"
            "2. URL буде: t.me/channel_name/123\n"
            "3. Число 123 - це MESSAGE_ID"
        )
        return
    
    code = context.args[0].upper()
    
    try:
        message_id = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ MESSAGE_ID має бути числом!")
        return
    
    # Отримуємо ID каналу
    try:
        channel_info = await context.bot.get_chat(config.CHANNEL_USERNAME)
        chat_id = channel_info.id
    except Exception as e:
        await update.message.reply_text(f"❌ Помилка отримання інформації про канал: {e}")
        return
    
    # Перевіряємо чи існує повідомлення
    try:
        await context.bot.copy_message(
            chat_id=user.id,
            from_chat_id=chat_id,
            message_id=message_id
        )
        await update.message.reply_text("✅ Пост знайдено! Зараз додам в базу...")
    except Exception as e:
        await update.message.reply_text(
            f"❌ Помилка! Повідомлення з ID {message_id} не знайдено в каналі.\n\n"
            f"Перевірте MESSAGE_ID та спробуйте ще раз."
        )
        return
    
    # Додаємо фільм в базу
    success = database.add_movie(code, message_id, chat_id, link=None)
    
    if success:
        await update.message.reply_text(
            f"✅ Фільм {code} успішно додано!\n\n"
            f"Message ID: {message_id}\n"
            f"Chat ID: {chat_id}\n\n"
            f"Користувачі тепер можуть знайти його за кодом {code}"
        )
    else:
        await update.message.reply_text(
            f"❌ Фільм з кодом {code} вже існує в базі!\n\n"
            f"Видаліть старий: /delete {code}"
        )


async def list_movies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /list - показує всі коди фільмів (тільки для адміністратора)
    """
    user = update.effective_user
    
    if user.id != config.ADMIN_ID:
        await update.message.reply_text("Ця команда доступна тільки адміністратору!")
        return
    
    movies = database.get_all_movies()
    
    if not movies:
        await update.message.reply_text("База даних порожня!\n\nПублікуйте пости в канал з текстом 'Код: F001'")
        return
    
    # Формуємо список кодів
    movies_text = f"📊 Всього фільмів в базі: {len(movies)}\n\n"
    movies_text += "Коди:\n"
    
    for movie in movies:
        movies_text += f"• {movie['code']} (message_id: {movie['message_id']})\n"
    
    # Telegram має ліміт на довжину повідомлення (4096 символів)
    if len(movies_text) > 4000:
        await update.message.reply_text("Занадто багато фільмів! Показую перші...")
        movies_text = movies_text[:4000]
    
    await update.message.reply_text(movies_text)


async def delete_movie_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /delete - видаляє фільм (тільки для адміністратора)
    Формат: /delete КОД
    Приклад: /delete F001
    """
    user = update.effective_user
    
    if user.id != config.ADMIN_ID:
        await update.message.reply_text("Ця команда доступна тільки адміністратору!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Вкажіть код фільму!\n\n"
            "Приклад: /delete F001"
        )
        return
    
    code = context.args[0].upper()
    
    # Видаляємо фільм
    success = database.delete_movie(code)
    
    if success:
        await update.message.reply_text(f"Фільм з кодом {code} видалено!")
    else:
        await update.message.reply_text(f"Фільм з кодом {code} не знайдено!")


# ========== АДМІНІСТРАТИВНА ПАНЕЛЬ БАЗИ ДАНИХ ==========

async def database_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /database - адміністративна панель для керування базою даних
    Показує всі фільми з кнопками для редагування/видалення
    """
    user = update.effective_user
    
    if user.id != config.ADMIN_ID:
        await update.message.reply_text("Ця команда доступна тільки адміністратору!")
        return
    
    movies = database.get_all_movies()
    
    if not movies:
        await update.message.reply_text(
            "База даних порожня!\n\n"
            "Публікуйте пости в канал з текстом 'Код: F001'"
        )
        return
    
    # Формуємо повідомлення зі списком фільмів
    text = f"📊 База даних фільмів ({len(movies)} фільмів)\n\n"
    
    # Словник з назвами фільмів
    movie_titles = {
        '001': 'Ніхто2',
        '002': 'Голови держав'
    }
    
    for i, movie in enumerate(movies, 1):
        # Отримуємо назву з нашого словника
        title = movie_titles.get(movie['code'], 'Невідома назва')
        text += f"{i}. **{movie['code']}** - {title}\n"
    
    # Створюємо кнопки для кожного фільму
    keyboard = []
    
    # Групуємо кнопки по 2 в ряд
    for i in range(0, len(movies), 2):
        row = []
        for j in range(2):
            if i + j < len(movies):
                movie = movies[i + j]
                row.append(InlineKeyboardButton(
                    f"🗑️ {movie['code']}", 
                    callback_data=f"delete_{movie['code']}"
                ))
        keyboard.append(row)
    
    # Додаємо кнопку "Оновити"
    keyboard.append([InlineKeyboardButton("🔄 Оновити", callback_data="refresh_database")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


# ========== КОМАНДА СКАНУВАННЯ ==========

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /scan - сканує канал і відновлює базу даних
    """
    user = update.effective_user
    
    if user.id != config.ADMIN_ID:
        await update.message.reply_text("Ця команда доступна тільки адміністратору!")
        return
    
    await update.message.reply_text("🔄 Сканування каналу... Це може зайняти кілька хвилин.")
    
    try:
        # Запускаємо Pyrogram сканер
        movies_count = await scanner.scan_channel_history()
        
        # Показуємо результат
        movies = database.get_all_movies()
        result_text = f"OK Сканування завершено!\n\n"
        result_text += f"DB Додано нових фільмів: {movies_count}\n"
        result_text += f"DB Всього в базі: {len(movies)}\n\n"
        
        if movies:
            result_text += "Фільми в базі:\n"
            for movie in movies:
                result_text += f"• {movie['code']} (ID: {movie['message_id']})\n"
        else:
            result_text += "База даних порожня"
        
        await update.message.reply_text(result_text)
        
    except Exception as e:
        logger.error(f"Помилка сканування: {e}")
        await update.message.reply_text(
            f"❌ Помилка сканування: {e}\n\n"
            f"Перевірте налаштування API_ID та API_HASH в config.py"
        )


# ========== СКАНУВАННЯ КАНАЛУ ==========

async def scan_channel_for_movies(context: ContextTypes.DEFAULT_TYPE):
    """
    Сканує канал і відновлює базу даних з усіх постів
    
    ВАЖЛИВО: Ця функція НЕ МОЖЕ отримати старі повідомлення через обмеження Bot API!
    
    Рекомендації:
    1. Видаліть базу даних (movies.db)
    2. Перезапустіть бота
    3. Опублікуйте заново всі пости в канал
    4. Бот автоматично їх додасть (функція handle_channel_post)
    
    АБО використовуйте Pyrogram для реального сканування
    """
    try:
        print("⚠️ УВАГА: Сканування каналу через Bot API неможливе!")
        print("")
        print("Telegram Bot API не дозволяє отримувати історію повідомлень з каналу.")
        print("")
        print("Рішення:")
        print("1. АВТОМАТИЧНЕ (рекомендовано):")
        print("   - Опублікуйте заново всі пости в канал")
        print("   - Бот автоматично їх додасть")
        print("")
        print("2. РУЧНЕ:")
        print("   - Використовуйте /add для кожного фільму окремо")
        print("")
        print("3. ЧЕРЕЗ PYROGRAM:")
        print("   - Встановіть pyrogram: pip install pyrogram")
        print("   - Створіть окремий скрипт для сканування")
        print("")
        
        # Не очищаємо базу даних!
        movies = database.get_all_movies()
        print(f"📊 Поточна база даних: {len(movies)} фільмів")
        
        return
        
    except Exception as e:
        print(f"Помилка: {e}")

# ========== ГОЛОВНА ФУНКЦІЯ ==========

async def start_scanner_background():
    """Запуск сканера в фоновому режимі"""
    try:
        await scanner.start()
        logger.info("✅ Pyrogram сканер запущено!")
        
        # Запускаємо моніторинг нових постів
        await scanner.monitor_new_posts()
    except Exception as e:
        logger.error(f"❌ Помилка запуску сканера: {e}")

def main():
    """
    Головна функція - запускає бота
    """
    print("Запуск бота...")
    
    # Ініціалізуємо базу даних
    database.init_database()
    print("База даних готова!")
    
    # Показуємо стан бази даних
    movies = database.get_all_movies()
    print(f"DB База даних: {len(movies)} фільмів")
    if movies:
        print("Фільми в базі:")
        for movie in movies:
            print(f"  - {movie['code']} (ID: {movie['message_id']})")
    else:
        print("База даних порожня")
    
    # Створюємо додаток бота (вимикаємо job_queue, бо він нам не потрібен)
    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .job_queue(None)  # Вимикаємо планувальник завдань
        .build()
    )
    
    # Реєструємо обробники команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))  # /help працює так само як /start
    application.add_handler(CommandHandler("add", add_movie_command))  # Ручне додавання фільму
    application.add_handler(CommandHandler("list", list_movies_command))
    application.add_handler(CommandHandler("delete", delete_movie_command))
    application.add_handler(CommandHandler("database", database_command))  # Нова команда!
    application.add_handler(CommandHandler("scan", scan_command))  # Команда сканування каналу
    
    # Реєструємо обробник кнопок
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # ⭐ НОВИЙ ОБРОБНИК! Автоматично зчитує пости з каналу
    application.add_handler(MessageHandler(filters.ChatType.CHANNEL, handle_channel_post))
    
    # Реєструємо обробник текстових повідомлень від користувачів
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_movie))
    
    # Запускаємо бота
    print("Бот запущено! Натисніть Ctrl+C для зупинки.")
    print("Використовуйте /scan для відновлення бази даних з каналу.")
    
    # Запускаємо сканер в фоновому режимі (тільки якщо налаштовано API)
    if config.API_ID != 'YOUR_API_ID' and config.API_HASH != 'YOUR_API_HASH':
        import asyncio
        import threading
        
        def run_scanner():
            asyncio.run(start_scanner_background())
        
        scanner_thread = threading.Thread(target=run_scanner, daemon=True)
        scanner_thread.start()
        print("OK Pyrogram сканер запущено!")
    else:
        print("WARN Pyrogram не налаштовано. Використовуйте /add для ручного додавання фільмів.")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


# Якщо файл запущено напряму - запускаємо бота
if __name__ == '__main__':
    main()

