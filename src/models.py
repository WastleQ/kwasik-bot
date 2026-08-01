from dataclasses import asdict, dataclass

import aiosqlite


@dataclass
class Player:
    username: str
    lvl: int = 1
    exp: int = 0
    stat_points: int = 0
    str_stat: int = 10
    agi: int = 10
    vit: int = 10
    int_stat: int = 10
    sen: int = 10
    hp: int = 250
    mp: int = 150
    gold: int = 100
    location_id: str = "0"
    weapon_id: str | None = None
    armor_id: str | None = None
    accessory_id: str | None = None
    last_daily: str = "2000-01-01"
    title: str = "novice"
    achievements: str = ""
    pvp_wins: int = 0


class DBManager:
    def __init__(self, db_path="solo_leveling.db"):
        self.path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.path) as conn:
            await conn.execute("""CREATE TABLE IF NOT EXISTS players 
                (username TEXT PRIMARY KEY, lvl INT, exp INT, stat_points INT, 
                 str_stat INT, agi INT, vit INT, int_stat INT, sen INT, 
                 hp INT, mp INT, gold INT, location_id TEXT,
                 weapon_id TEXT, armor_id TEXT, accessory_id TEXT, last_daily TEXT,
                 title TEXT DEFAULT 'novice', achievements TEXT DEFAULT '', pvp_wins INT DEFAULT 0)""")
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS inventory (username TEXT, item_id TEXT)"
            )

            # Migration check for existing databases
            async with conn.execute("PRAGMA table_info(players)") as cursor:
                columns = [row[1] for row in await cursor.fetchall()]
                if "title" not in columns:
                    await conn.execute(
                        "ALTER TABLE players ADD COLUMN title TEXT DEFAULT 'novice'"
                    )
                if "achievements" not in columns:
                    await conn.execute(
                        "ALTER TABLE players ADD COLUMN achievements TEXT DEFAULT ''"
                    )
                if "pvp_wins" not in columns:
                    await conn.execute(
                        "ALTER TABLE players ADD COLUMN pvp_wins INT DEFAULT 0"
                    )

            await conn.commit()

    async def load(self, name: str) -> Player | None:
        async with aiosqlite.connect(self.path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM players WHERE username=?", (name.lower(),)
            ) as cursor:
                row = await cursor.fetchone()
                return Player(**dict(row)) if row else None

    async def save(self, p: Player):
        async with aiosqlite.connect(self.path) as conn:
            d = asdict(p)
            cols = ", ".join(d.keys())
            ques = ", ".join(["?"] * len(d))
            await conn.execute(
                f"INSERT OR REPLACE INTO players ({cols}) VALUES ({ques})",
                list(d.values()),
            )
            await conn.commit()

    async def get_all_players(self) -> list[Player]:
        async with aiosqlite.connect(self.path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("SELECT * FROM players") as cursor:
                rows = await cursor.fetchall()
                return [Player(**dict(r)) for r in rows]

    async def add_to_inventory(self, u: str, i: str):
        async with aiosqlite.connect(self.path) as conn:
            await conn.execute("INSERT INTO inventory VALUES (?, ?)", (u.lower(), i))
            await conn.commit()

    async def remove_from_inventory(self, u: str, i: str):
        async with aiosqlite.connect(self.path) as conn:
            await conn.execute(
                "DELETE FROM inventory WHERE rowid = (SELECT rowid FROM inventory WHERE username=? AND item_id=? LIMIT 1)",
                (u.lower(), i),
            )
            await conn.commit()

    async def get_inventory(self, u: str) -> list[str]:
        async with (
            aiosqlite.connect(self.path) as conn,
            conn.execute(
                "SELECT item_id FROM inventory WHERE username=?", (u.lower(),)
            ) as cursor,
        ):
            rows = await cursor.fetchall()
            return [r[0] for r in rows]

    async def get_top_players(self, limit=5) -> list[Player]:
        async with aiosqlite.connect(self.path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM players ORDER BY lvl DESC, exp DESC LIMIT ?", (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [Player(**dict(r)) for r in rows]

    async def get_top_pvp_players(self, limit=5) -> list[Player]:
        async with aiosqlite.connect(self.path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM players ORDER BY pvp_wins DESC LIMIT ?", (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [Player(**dict(r)) for r in rows]
