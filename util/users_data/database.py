import aiosqlite
import os

DB_PATH = "users.db"
START_BALANCE = 500


async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                balance INTEGER DEFAULT 500,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def add_user(user_id: int, username: str = None):
    """Добавить пользователя в БД"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)",
                (user_id, username, START_BALANCE)
            )
            await db.commit()
            return True
    except aiosqlite.IntegrityError:
        return False


async def get_user(user_id: int):
    """Получить пользователя по ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT user_id, username, balance FROM users WHERE user_id = ?",
            (user_id,)
        )
        return await cursor.fetchone()


async def get_balance(user_id: int):
    """Получить баланс пользователя"""
    user = await get_user(user_id)
    return user[2] if user else 0


async def update_balance(user_id: int, amount: int):
    """Обновить баланс (может быть отрицательным)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()


async def set_balance(user_id: int, balance: int):
    """Установить новый баланс"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = ? WHERE user_id = ?",
            (balance, user_id)
        )
        await db.commit()


async def get_all_users():
    """Получить всех пользователей"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id, username, balance FROM users")
        return await cursor.fetchall()
