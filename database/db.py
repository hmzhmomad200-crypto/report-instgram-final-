import aiosqlite
from config import DATABASE_PATH

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                session_id TEXT,
                target_username TEXT,
                target_id TEXT,
                report_types TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                report_type TEXT,
                success BOOLEAN,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def save_session(user_id: int, session_id: str, username: str = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO users (user_id, username, session_id)
            VALUES (?, ?, ?)
        """, (user_id, username, session_id))
        await db.commit()

async def get_session(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT session_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def save_target(user_id: int, target_username: str, target_id: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE users SET target_username = ?, target_id = ? WHERE user_id = ?
        """, (target_username, target_id, user_id))
        await db.commit()

async def save_report_types(user_id: int, report_types: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE users SET report_types = ? WHERE user_id = ?
        """, (report_types, user_id))
        await db.commit()

async def get_user_data(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "user_id": row[0],
                    "username": row[1],
                    "session_id": row[2],
                    "target_username": row[3],
                    "target_id": row[4],
                    "report_types": row[5],
                }
            return None

async def get_all_user_ids():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def log_report(user_id: int, report_type: str, success: bool):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO reports (user_id, report_type, success) VALUES (?, ?, ?)
        """, (user_id, report_type, success))
        await db.commit()

async def get_stats():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        total_users = await db.execute_fetchall("SELECT COUNT(*) FROM users")
        total_reports = await db.execute_fetchall("SELECT COUNT(*) FROM reports")
        success_reports = await db.execute_fetchall("SELECT COUNT(*) FROM reports WHERE success = 1")
        return {
            "users": total_users[0][0],
            "total_reports": total_reports[0][0],
            "success_reports": success_reports[0][0],
        }
