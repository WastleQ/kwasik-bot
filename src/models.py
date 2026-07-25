import sqlite3
from dataclasses import dataclass, asdict

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
    weapon_id: str = None
    armor_id: str = None
    accessory_id: str = None  # Новый слот для артефактов
    last_daily: str = "2000-01-01"

class DBManager:
    def __init__(self, db_path="solo_leveling.db"):
        self.path = db_path
        with sqlite3.connect(self.path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS players 
                (username TEXT PRIMARY KEY, lvl INT, exp INT, stat_points INT, 
                 str_stat INT, agi INT, vit INT, int_stat INT, sen INT, 
                 hp INT, mp INT, gold INT, location_id TEXT,
                 weapon_id TEXT, armor_id TEXT, accessory_id TEXT, last_daily TEXT)''')
            conn.execute("CREATE TABLE IF NOT EXISTS inventory (username TEXT, item_id TEXT)")

    def load(self, name: str):
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM players WHERE username=?", (name.lower(),)).fetchone()
            return Player(**dict(row)) if row else None

    def save(self, p: Player):
        with sqlite3.connect(self.path) as conn:
            d = asdict(p)
            cols = ', '.join(d.keys())
            ques = ', '.join(['?'] * len(d))
            conn.execute(f"INSERT OR REPLACE INTO players ({cols}) VALUES ({ques})", list(d.values()))

    def get_all_players(self):
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM players").fetchall()
            return [Player(**dict(r)) for r in rows]

    def add_to_inventory(self, u, i):
        with sqlite3.connect(self.path) as conn:
            conn.execute("INSERT INTO inventory VALUES (?, ?)", (u.lower(), i))

    def remove_from_inventory(self, u, i):
        with sqlite3.connect(self.path) as conn:
            conn.execute("DELETE FROM inventory WHERE rowid = (SELECT rowid FROM inventory WHERE username=? AND item_id=? LIMIT 1)", (u.lower(), i))

    def get_inventory(self, u):
        with sqlite3.connect(self.path) as conn:
            return [r[0] for r in conn.execute("SELECT item_id FROM inventory WHERE username=?", (u.lower(),)).fetchall()]

    def get_top_players(self, limit=5):
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            # Сортируем по уровню (lvl), а затем по опыту (exp)
            rows = conn.execute(
                "SELECT * FROM players ORDER BY lvl DESC, exp DESC LIMIT ?", 
                (limit,)
            ).fetchall()
            return [Player(**dict(r)) for r in rows]