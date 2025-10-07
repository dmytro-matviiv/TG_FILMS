# 📦 Як завантажити проект на GitHub

## Крок 1: Створення репозиторію на GitHub

1. Відкрийте [GitHub](https://github.com/)
2. Натисніть **"+"** вгорі справа → **"New repository"**
3. Заповніть форму:
   - **Repository name:** `TG_FILMS` (або інша назва)
   - **Description:** `Telegram бот для пошуку фільмів`
   - **Visibility:** `Public` або `Private` (на ваш вибір)
   - ❌ **НЕ** ставте галочки на "Add README" та "Add .gitignore"
4. Натисніть **"Create repository"**

## Крок 2: Підключення локального репозиторію

GitHub покаже вам команди. Використайте ці команди у вашому терміналі:

```bash
# Додайте віддалений репозиторій
git remote add origin https://github.com/YOUR_USERNAME/TG_FILMS.git

# Відправте код на GitHub
git branch -M main
git push -u origin main
```

**Замініть `YOUR_USERNAME` на ваш GitHub username!**

## Крок 3: Налаштування після завантаження

### Для інших користувачів (або для себе на новому комп'ютері):

```bash
# 1. Клонування репозиторію
git clone https://github.com/YOUR_USERNAME/TG_FILMS.git
cd TG_FILMS

# 2. Копіювання шаблону конфігурації
copy config.example.py config.py  # Windows
# або
cp config.example.py config.py    # Linux/Mac

# 3. Редагування config.py
# Відкрийте config.py та вставте свої дані:
# - BOT_TOKEN (від @BotFather)
# - CHANNEL_USERNAME (@your_channel)
# - ADMIN_ID (ваш Telegram ID)

# 4. Встановлення залежностей
pip install -r requirements.txt

# 5. Запуск бота
python bot.py
```

## Крок 4: Оновлення коду на GitHub

Коли ви змінюєте код локально:

```bash
# 1. Перевірте статус
git status

# 2. Додайте зміни
git add .

# 3. Створіть коміт
git commit -m "Опис ваших змін"

# 4. Відправте на GitHub
git push
```

## 🔒 ВАЖЛИВО: Безпека

### ❌ НІКОЛИ не завантажуйте на GitHub:

- `config.py` - містить токени і секрети
- `movies.db` - база даних
- `.env` - змінні середовища

### ✅ Завантажуйте:

- `config.example.py` - шаблон без секретів
- `bot.py` - код бота
- `database.py` - код бази даних
- `README.md` - документація
- Інші `.py`, `.md`, `.txt` файли

## 🚀 Деплой на Railway з GitHub

1. Відкрийте [Railway](https://railway.com/)
2. **"New Project"** → **"Deploy from GitHub repo"**
3. Виберіть репозиторій `TG_FILMS`
4. Railway автоматично:
   - Знайде `railway.json`
   - Встановить залежності з `requirements.txt`
   - Запустить `python bot.py`
5. Додайте змінні середовища в Railway:
   - `BOT_TOKEN`
   - `CHANNEL_USERNAME`
   - `ADMIN_ID`
   - `DATABASE_URL` (автоматично з PostgreSQL)

## 📊 Структура Git репозиторію

```
TG_FILMS/
├── .git/                  # Git папка (не редагувати)
├── .gitignore            # Ігноровані файли
├── bot.py                # ✅ На GitHub
├── database.py           # ✅ На GitHub
├── config.example.py     # ✅ На GitHub (шаблон)
├── config.py             # ❌ НЕ на GitHub (секрети)
├── movies.db             # ❌ НЕ на GitHub (база даних)
├── requirements.txt      # ✅ На GitHub
├── railway.json          # ✅ На GitHub
├── README.md             # ✅ На GitHub
├── RAILWAY_DEPLOY.md     # ✅ На GitHub
└── GITHUB_SETUP.md       # ✅ На GitHub
```

## 🎯 Корисні команди Git

```bash
# Перевірити статус
git status

# Подивитись історію комітів
git log

# Створити нову гілку
git checkout -b new-feature

# Перемкнутись між гілками
git checkout main
git checkout new-feature

# Відмінити зміни (до коміту)
git restore filename.py

# Оновити з GitHub
git pull

# Подивитись різницю
git diff
```

## 🤝 Співпраця

Якщо працюєте в команді:

```bash
# Перед початком роботи
git pull  # Отримати останні зміни

# Після завершення роботи
git add .
git commit -m "Опис змін"
git push
```

## 📞 Підтримка

Якщо виникли проблеми:

1. Перевірте `.gitignore` - чи правильно налаштований
2. Перевірте `config.py` - чи не завантажується на GitHub
3. Перевірте GitHub Issues для вашого репозиторію
4. Прочитайте документацію Git: https://git-scm.com/doc

---

**Ваш проект готовий до публікації на GitHub!** 🎉

