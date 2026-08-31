import asyncio
import os

import aiosqlite
import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def fix_titles():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        print("Подключение к PostgreSQL...")
        conn = await asyncpg.connect(database_url)
        try:
            result = await conn.execute(
                "UPDATE players SET title = 'novice' WHERE title = 'shadow_monarch' AND lvl < 30"
            )
            print(f"✅ База PostgreSQL обновлена: {result}")
        finally:
            await conn.close()
    else:
        db_path = "solo_leveling.db"
        if not os.path.exists(db_path):
            print(f"❌ База данных {db_path} не найдена.")
            return
        print(f"Подключение к SQLite ({db_path})...")
        async with aiosqlite.connect(db_path) as conn:
            await conn.execute(
                "UPDATE players SET title = 'novice' WHERE title = 'shadow_monarch' AND lvl < 30"
            )
            await conn.commit()
            print(
                "✅ База SQLite успешно обновлена (титул Теневого Монарха снят у игроков ниже 30 уровня)."
            )


if __name__ == "__main__":
    asyncio.run(fix_titles())
