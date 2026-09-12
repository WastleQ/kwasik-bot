# src/models.py
from dataclasses import dataclass
from typing import ClassVar

from sqlalchemy import Column, Float, Integer, String, Text, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from src.config import DATABASE_URL

Base = declarative_base()


class PlayerModel(Base):
    __tablename__ = "players"

    username = Column(String, primary_key=True, index=True)
    lvl = Column(Integer, default=1)
    exp = Column(Integer, default=0)
    stat_points = Column(Integer, default=0)
    str_stat = Column(Integer, default=10)
    agi = Column(Integer, default=10)
    vit = Column(Integer, default=10)
    int_stat = Column(Integer, default=10)
    sen = Column(Integer, default=10)
    hp = Column(Integer, default=250)
    mp = Column(Integer, default=150)
    gold = Column(Integer, default=100)
    location_id = Column(String, default="0")
    weapon_id = Column(String, nullable=True)
    armor_id = Column(String, nullable=True)
    accessory_id = Column(String, nullable=True)
    last_daily = Column(String, default="2000-01-01")
    title = Column(String, default="novice")
    achievements = Column(Text, default="")
    pvp_wins = Column(Integer, default=0)
    daily_quest_loc = Column(String, default="1")
    daily_quest_target = Column(Integer, default=3)
    daily_quest_progress = Column(Integer, default=0)
    shield = Column(Integer, default=0)
    bonus_stat_points = Column(Integer, default=0)
    daily_quests_completed = Column(Integer, default=0)
    linked_twitch = Column(String, nullable=True, index=True)


class InventoryModel(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, index=True)
    item_id = Column(String)

class BotActionModel(Base):
    __tablename__ = "bot_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_type = Column(String)
    payload = Column(Text)
    status = Column(String, default="pending")


class SyncCodeModel(Base):
    __tablename__ = "sync_codes"

    code = Column(String, primary_key=True, index=True)
    telegram_username = Column(String)
    expires_at = Column(Float)


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
    daily_quest_loc: str = "1"
    daily_quest_target: int = 3
    daily_quest_progress: int = 0
    shield: int = 0
    bonus_stat_points: int = 0
    daily_quests_completed: int = 0
    linked_twitch: str | None = None

    STAT_FIELDS: ClassVar[dict[str, str]] = {
        "str": "str_stat",
        "agi": "agi",
        "vit": "vit",
        "int": "int_stat",
        "sen": "sen",
    }

    @staticmethod
    def resolve_stat_field(short: str) -> str | None:
        return Player.STAT_FIELDS.get(short.lower().strip())

    def upgrade_stat(self, short: str, count: int = 1) -> str:
        field = self.resolve_stat_field(short)
        if not field:
            raise ValueError(f"Unknown stat: {short!r}")
        if count <= 0:
            raise ValueError("count must be positive")
        if self.stat_points < count:
            raise ValueError(
                f"Not enough AP: need {count}, have {self.stat_points}"
            )
        setattr(self, field, getattr(self, field) + count)
        self.stat_points -= count
        return field

    @classmethod
    def from_orm(cls, model: PlayerModel) -> "Player":
        return cls(
            username=model.username,
            lvl=model.lvl,
            exp=model.exp,
            stat_points=model.stat_points,
            str_stat=model.str_stat,
            agi=model.agi,
            vit=model.vit,
            int_stat=model.int_stat,
            sen=model.sen,
            hp=model.hp,
            mp=model.mp,
            gold=model.gold,
            location_id=model.location_id,
            weapon_id=model.weapon_id,
            armor_id=model.armor_id,
            accessory_id=model.accessory_id,
            last_daily=model.last_daily,
            title=model.title,
            achievements=model.achievements,
            pvp_wins=model.pvp_wins,
            daily_quest_loc=model.daily_quest_loc,
            daily_quest_target=model.daily_quest_target,
            daily_quest_progress=model.daily_quest_progress,
            shield=model.shield,
            bonus_stat_points=model.bonus_stat_points,
            daily_quests_completed=model.daily_quests_completed,
            linked_twitch=model.linked_twitch,
        )

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "lvl": self.lvl,
            "exp": self.exp,
            "stat_points": self.stat_points,
            "str_stat": self.str_stat,
            "agi": self.agi,
            "vit": self.vit,
            "int_stat": self.int_stat,
            "sen": self.sen,
            "hp": self.hp,
            "mp": self.mp,
            "gold": self.gold,
            "location_id": self.location_id,
            "weapon_id": self.weapon_id,
            "armor_id": self.armor_id,
            "accessory_id": self.accessory_id,
            "last_daily": self.last_daily,
            "title": self.title,
            "achievements": self.achievements,
            "pvp_wins": self.pvp_wins,
            "daily_quest_loc": self.daily_quest_loc,
            "daily_quest_target": self.daily_quest_target,
            "daily_quest_progress": self.daily_quest_progress,
            "shield": self.shield,
            "bonus_stat_points": self.bonus_stat_points,
            "daily_quests_completed": self.daily_quests_completed,
            "linked_twitch": self.linked_twitch,
        }


class DBManager:
    def __init__(self, db_path="solo_leveling.db"):
        self.db_path = db_path
        self.database_url = DATABASE_URL
        if self.database_url:
            url = self.database_url
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://") and "+asyncpg" not in url:
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            self.async_engine = create_async_engine(url, echo=False)
        else:
            self.async_engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)

        self.session_maker = async_sessionmaker(self.async_engine, expire_on_commit=False, class_=AsyncSession)

    async def init_db(self):
        async with self.async_engine.begin() as conn:
            if self.database_url:
                await conn.run_sync(Base.metadata.create_all)
                from sqlalchemy import text as _text
                await conn.execute(_text("""
                    UPDATE players 
                    SET bonus_stat_points = GREATEST(0, ((str_stat - 10) + (agi - 10) + (vit - 10) + (int_stat - 10) + (sen - 10) + stat_points) - (lvl - 1) * 5)
                    WHERE ((str_stat - 10) + (agi - 10) + (vit - 10) + (int_stat - 10) + (sen - 10) + stat_points) > (lvl - 1) * 5
                """))
                return
            # SQLite: проверяем старую схему inventory и мигрируем при необходимости
            from sqlalchemy import text as _text
            result = await conn.execute(_text("PRAGMA table_info(inventory)"))
            inv_columns = [row[1] for row in result.fetchall()]
            if inv_columns and "id" not in inv_columns:
                # Старая схема: пересоздаём с id и переносим данные
                await conn.execute(_text(
                    "ALTER TABLE inventory RENAME TO inventory_old"
                ))
                await conn.run_sync(Base.metadata.create_all)
                await conn.execute(_text(
                    "INSERT INTO inventory (username, item_id) SELECT username, item_id FROM inventory_old"
                ))
                await conn.execute(_text("DROP TABLE inventory_old"))

            p_result = await conn.execute(_text("PRAGMA table_info(players)"))
            p_columns = [row[1] for row in p_result.fetchall()]
            if p_columns and "linked_twitch" not in p_columns:
                await conn.execute(_text("ALTER TABLE players ADD COLUMN linked_twitch TEXT"))
            if p_columns and "daily_quests_completed" not in p_columns:
                await conn.execute(_text("ALTER TABLE players ADD COLUMN daily_quests_completed INT DEFAULT 0"))

            await conn.run_sync(Base.metadata.create_all)

            await conn.execute(_text("""
                UPDATE players 
                SET bonus_stat_points = MAX(0, ((str_stat - 10) + (agi - 10) + (vit - 10) + (int_stat - 10) + (sen - 10) + stat_points) - (lvl - 1) * 5)
                WHERE ((str_stat - 10) + (agi - 10) + (vit - 10) + (int_stat - 10) + (sen - 10) + stat_points) > (lvl - 1) * 5
            """))

    async def load(self, username: str) -> Player | None:
        username = username.lower().strip()
        async with self.session_maker() as session:
            result = await session.execute(
                select(PlayerModel).where(
                    (PlayerModel.username == username) | (PlayerModel.linked_twitch == username)
                )
            )
            model = result.scalars().first()
            if not model:
                return None
            return Player.from_orm(model)

    async def save(self, player: Player):
        username = player.username.lower().strip()
        async with self.session_maker() as session:
            async with session.begin():
                result = await session.execute(
                    select(PlayerModel).where(
                        (PlayerModel.username == username) | (PlayerModel.username == player.username.lower().strip())
                    )
                )
                model = result.scalars().first()
                if not model:
                    model = PlayerModel(username=username)
                    session.add(model)
                
                model.lvl = player.lvl
                model.exp = player.exp
                model.stat_points = player.stat_points
                model.str_stat = player.str_stat
                model.agi = player.agi
                model.vit = player.vit
                model.int_stat = player.int_stat
                model.sen = player.sen
                model.hp = player.hp
                model.mp = player.mp
                model.gold = player.gold
                model.location_id = player.location_id
                model.weapon_id = player.weapon_id
                model.armor_id = player.armor_id
                model.accessory_id = player.accessory_id
                model.last_daily = player.last_daily
                model.title = player.title
                model.achievements = player.achievements
                model.pvp_wins = player.pvp_wins
                model.daily_quest_loc = player.daily_quest_loc
                model.daily_quest_target = player.daily_quest_target
                model.daily_quest_progress = player.daily_quest_progress
                model.shield = player.shield
                model.bonus_stat_points = player.bonus_stat_points
                model.daily_quests_completed = player.daily_quests_completed
                model.linked_twitch = player.linked_twitch

    async def get_inventory(self, username: str) -> list[str]:
        username = username.lower().strip()
        async with self.session_maker() as session:
            result = await session.execute(select(InventoryModel.item_id).where(InventoryModel.username == username))
            return [row[0] for row in result.all()]

    async def add_to_inventory(self, username: str, item_id: str):
        username = username.lower().strip()
        async with self.session_maker() as session, session.begin():
            inv = InventoryModel(username=username, item_id=item_id)
            session.add(inv)

    async def remove_from_inventory(self, username: str, item_id: str, count: int = 1):
        if count <= 0:
            return 0
        username = username.lower().strip()
        async with self.session_maker() as session, session.begin():
            result = await session.execute(
                select(InventoryModel).where(
                    InventoryModel.username == username,
                    InventoryModel.item_id == item_id,
                )
            )
            rows = result.scalars().all()
            to_remove = min(len(rows), count)
            for row in rows[:to_remove]:
                await session.delete(row)
            await session.flush()
            return to_remove

    async def get_all_players(self) -> list[Player]:
        async with self.session_maker() as session:
            result = await session.execute(select(PlayerModel))
            models = result.scalars().all()
            return [Player.from_orm(m) for m in models]

    async def get_top_players(self, limit: int = 10) -> list[Player]:
        players = await self.get_all_players()
        players.sort(key=lambda x: (x.lvl, x.exp, x.gold), reverse=True)
        return players[:limit]

    async def get_top_gold_players(self, limit: int = 10) -> list[Player]:
        players = await self.get_all_players()
        players.sort(key=lambda x: x.gold, reverse=True)
        return players[:limit]

    async def get_top_pvp_players(self, limit: int = 10) -> list[Player]:
        players = await self.get_all_players()
        players.sort(key=lambda x: x.pvp_wins, reverse=True)
        return players[:limit]

    async def add_bot_action(self, action_type: str, payload: str) -> int:
        async with self.session_maker() as session:
            async with session.begin():
                action = BotActionModel(action_type=action_type, payload=payload, status="pending")
                session.add(action)
                await session.flush()
                return action.id

    async def poll_bot_actions(self) -> list[dict]:
        async with self.session_maker() as session:
            result = await session.execute(select(BotActionModel).where(BotActionModel.status == "pending"))
            actions = result.scalars().all()
            return [{"id": a.id, "action_type": a.action_type, "payload": a.payload} for a in actions]

    async def get_pending_bot_actions(self) -> list[dict]:
        return await self.poll_bot_actions()

    async def update_bot_action_status(self, action_id: int, status: str):
        async with self.session_maker() as session:
            async with session.begin():
                await session.execute(
                    update(BotActionModel).where(BotActionModel.id == action_id).values(status=status)
                )

    async def create_sync_code(self, code: str, telegram_username: str, expires_at: float):
        import time
        now = time.time()
        async with self.session_maker() as session:
            async with session.begin():
                await session.execute(delete(SyncCodeModel).where((SyncCodeModel.expires_at < now) | (SyncCodeModel.code == code)))
                sc = SyncCodeModel(code=code, telegram_username=telegram_username, expires_at=expires_at)
                session.add(sc)
                await session.flush()

    async def verify_sync_code(self, code: str) -> str | None:
        import time
        now = time.time()
        async with self.session_maker() as session:
            async with session.begin():
                result = await session.execute(
                    select(SyncCodeModel).where(SyncCodeModel.code == code)
                )
                sc = result.scalars().first()
                if not sc:
                    return None
                if sc.expires_at < now:
                    await session.delete(sc)
                    await session.flush()
                    return None
                tg_username = sc.telegram_username
                await session.delete(sc)
                await session.flush()
                return tg_username
