"""Database modellari"""
import aiosqlite
from datetime import datetime
from config import DATABASE_PATH


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT, first_name TEXT, language TEXT DEFAULT 'uz',
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            invited_by INTEGER, premium INTEGER DEFAULT 0,
            banned INTEGER DEFAULT 0,
            daily_processed INTEGER DEFAULT 0,
            total_processed INTEGER DEFAULT 0,
            last_process_date DATE)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY DEFAULT 1,
            total_users INTEGER DEFAULT 0,
            total_processed INTEGER DEFAULT 0,
            total_premium INTEGER DEFAULT 0,
            CHECK (id = 1))""")
        await db.execute("INSERT OR IGNORE INTO stats (id) VALUES (1)")
        await db.commit()


async def add_user(telegram_id, username=None, first_name=None, invited_by=None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("INSERT INTO users (telegram_id, username, first_name, invited_by) VALUES (?, ?, ?, ?)", (telegram_id, username, first_name, invited_by))
            await db.execute("UPDATE stats SET total_users = total_users + 1 WHERE id = 1")
            await db.commit(); return True
        except: return False


async def get_user(telegram_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as c:
            return await c.fetchone()


async def update_last_active(telegram_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE telegram_id = ?", (telegram_id,))
        await db.commit()


async def increment_processed(telegram_id):
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""UPDATE users SET daily_processed = CASE WHEN last_process_date = ? THEN daily_processed + 1 ELSE 1 END, last_process_date = ?, total_processed = total_processed + 1 WHERE telegram_id = ?""", (today, today, telegram_id))
        await db.execute("UPDATE stats SET total_processed = total_processed + 1 WHERE id = 1")
        await db.commit()


async def check_daily_limit(telegram_id, limit):
    user = await get_user(telegram_id)
    if not user: return True
    today = datetime.now().strftime("%Y-%m-%d")
    if user["last_process_date"] != today: return True
    return user["daily_processed"] < limit


async def get_user_count():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c: return (await c.fetchone())[0]


async def get_today_users():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE DATE(join_date) = DATE('now')") as c: return (await c.fetchone())[0]


async def get_active_users(days=7):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(f"SELECT COUNT(*) FROM users WHERE last_active > datetime('now', '-{days} days')") as c: return (await c.fetchone())[0]


async def get_all_users():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT telegram_id FROM users WHERE banned = 0") as c: return [r[0] for r in await c.fetchall()]


async def set_premium(telegram_id, days=30):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET premium = 1 WHERE telegram_id = ?", (telegram_id,))
        await db.execute("UPDATE stats SET total_premium = total_premium + 1 WHERE id = 1")
        await db.commit()


async def ban_user(telegram_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET banned = 1 WHERE telegram_id = ?", (telegram_id,))
        await db.commit()


async def unban_user(telegram_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET banned = 0 WHERE telegram_id = ?", (telegram_id,))
        await db.commit()


async def get_referral_count(telegram_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE invited_by = ?", (telegram_id,)) as c: return (await c.fetchone())[0]


async def get_referral_leaderboard(limit=10):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT telegram_id, first_name, username, (SELECT COUNT(*) FROM users u2 WHERE u2.invited_by = u.telegram_id) as ref_count FROM users u ORDER BY ref_count DESC LIMIT ?", (limit,)) as c:
            return await c.fetchall()