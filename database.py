# database.py - Робота з базою даних фільмів

import os
import psycopg2  # Бібліотека для роботи з PostgreSQL
from psycopg2.extras import RealDictCursor

# Налаштування бази даних
# На Railway буде використовуватись PostgreSQL
# Локально - SQLite для розробки

def get_database_url():
    """
    Отримує URL бази даних з змінних середовища або використовує SQLite локально
    """
    # На Railway буде змінна DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Використовуємо PostgreSQL на Railway
        return database_url
    else:
        # Локальна розробка - SQLite
        return None

def get_connection():
    """
    Створює з'єднання з базою даних (PostgreSQL або SQLite)
    """
    database_url = get_database_url()
    
    if database_url:
        # PostgreSQL на Railway
        return psycopg2.connect(database_url)
    else:
        # SQLite локально
        import sqlite3
        return sqlite3.connect("movies.db")


def init_database():
    """
    Функція для створення бази даних (таблиці).
    Викликається один раз при першому запуску бота.
    
    Автоматично визначає тип бази:
    - PostgreSQL на Railway (DATABASE_URL є)
    - SQLite локально (DATABASE_URL немає)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Перевіряємо тип бази даних
    database_url = get_database_url()
    
    if database_url:
        # PostgreSQL на Railway
        print("Використовуємо PostgreSQL на Railway...")
        
        # SQL для PostgreSQL
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id SERIAL PRIMARY KEY,
                code VARCHAR(50) UNIQUE NOT NULL,
                message_id BIGINT NOT NULL,
                chat_id BIGINT NOT NULL,
                link TEXT
            )
        ''')
        
    else:
        # SQLite локально
        print("Використовуємо SQLite локально...")
        
        # Видаляємо стару таблицю (міграція)
        cursor.execute('DROP TABLE IF EXISTS movies')
        
        # SQL для SQLite
        cursor.execute('''
            CREATE TABLE movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                message_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                link TEXT
            )
        ''')
    
    # Зберігаємо зміни
    conn.commit()
    
    # Закриваємо з'єднання
    conn.close()
    
    print("База даних створена з новою структурою!")


def add_movie(code, message_id, chat_id, link=None):
    """
    Функція для додавання фільму в базу даних.
    
    НОВА ЛОГІКА: зберігаємо посилання на пост в каналі + посилання на фільм!
    
    Параметри:
    - code: код фільму (наприклад "001")
    - message_id: ID повідомлення в каналі
    - chat_id: ID каналу
    - link: посилання на фільм (необов'язково)
    
    Повертає:
    - True якщо фільм додано успішно
    - False якщо виникла помилка (наприклад, код вже існує)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # SQL команда для вставки даних (працює для обох баз)
        database_url = get_database_url()
        if database_url:
            # PostgreSQL
            cursor.execute('''
                INSERT INTO movies (code, message_id, chat_id, link)
                VALUES (%s, %s, %s, %s)
            ''', (code, message_id, chat_id, link))
        else:
            # SQLite
            cursor.execute('''
                INSERT INTO movies (code, message_id, chat_id, link)
                VALUES (?, ?, ?, ?)
            ''', (code, message_id, chat_id, link))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        # Помилка (наприклад, код вже існує)
        print(f"Помилка при додаванні фільму: {e}")
        return False


def find_movie(code):
    """
    Функція для пошуку фільму за кодом.
    
    НОВА ЛОГІКА: повертає message_id і chat_id для пересилання!
    
    Параметри:
    - code: код фільму для пошуку
    
    Повертає:
    - Словник з message_id і chat_id, якщо знайдено
    - None, якщо фільм не знайдено
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # SQL команда для пошуку
    database_url = get_database_url()
    if database_url:
        # PostgreSQL
        cursor.execute('''
            SELECT code, message_id, chat_id, link
            FROM movies
            WHERE code = %s
        ''', (code,))
    else:
        # SQLite
        cursor.execute('''
            SELECT code, message_id, chat_id, link
            FROM movies
            WHERE code = ?
        ''', (code,))
    
    # Отримуємо результат
    result = cursor.fetchone()  # fetchone() - отримати один рядок
    
    conn.close()
    
    # Якщо фільм знайдено
    if result:
        return {
            'code': result[0],
            'message_id': result[1],
            'chat_id': result[2],
            'link': result[3]
        }
    else:
        return None


def get_all_movies():
    """
    Функція для отримання всіх фільмів з бази.
    
    Повертає:
    - Список словників з усіма фільмами
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Отримуємо всі фільми
    cursor.execute('SELECT code, message_id, chat_id, link FROM movies')
    
    results = cursor.fetchall()  # fetchall() - отримати всі рядки
    
    conn.close()
    
    # Перетворюємо результат в список словників
    movies = []
    for row in results:
        movies.append({
            'code': row[0],
            'message_id': row[1],
            'chat_id': row[2],
            'link': row[3]
        })
    
    return movies


def delete_movie(code):
    """
    Функція для видалення фільму з бази.
    
    Параметри:
    - code: код фільму для видалення
    
    Повертає:
    - True якщо фільм видалено
    - False якщо фільм не знайдено
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    database_url = get_database_url()
    if database_url:
        # PostgreSQL
        cursor.execute('DELETE FROM movies WHERE code = %s', (code,))
    else:
        # SQLite
        cursor.execute('DELETE FROM movies WHERE code = ?', (code,))
    
    # Перевіряємо, чи був видалений хоч один рядок
    deleted = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    return deleted


# Тестовий код (викликається тільки якщо запустити цей файл напряму)
if __name__ == "__main__":
    print("Тестування бази даних...")
    
    # Створюємо базу
    init_database()
    
    # Додаємо тестовий фільм (приклад)
    # Параметри: код, message_id (ID поста в каналі), chat_id (ID каналу)
    add_movie("001", 123456, -1001234567890)
    
    # Шукаємо фільм
    movie = find_movie("001")
    if movie:
        print(f"Знайдено код: {movie['code']}, message_id: {movie['message_id']}")
    
    # Показуємо всі фільми
    all_movies = get_all_movies()
    print(f"\nВсього фільмів в базі: {len(all_movies)}")

