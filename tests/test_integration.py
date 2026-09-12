# tests/test_integration.py
import os
import time

import pytest

from src.container import AppContainer
from src.exceptions import NotEnoughAPError, PlayerNotFoundError


@pytest.mark.asyncio
async def test_container_and_db_flow():
    db_path = "test_integration.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    container = AppContainer(db_path=db_path)
    await container.init()

    # Get or create player via container
    p = await container.get_player("hero")
    assert p.username == "hero"
    assert p.lvl == 1
    assert p.gold == 100

    # Give AP and test leveling / upgrade
    p.stat_points += 5
    p.str_stat += 5
    p.stat_points -= 5
    await container.db.save(p)

    p_loaded = await container.db.load("hero")
    assert p_loaded.str_stat == 15

    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.mark.asyncio
async def test_sell_item_bulk_remove():
    db_path = "test_sell.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    container = AppContainer(db_path=db_path)
    await container.init()

    p = await container.get_player("seller")
    p.gold = 100
    await container.db.save(p)

    await container.db.add_to_inventory(p.username, "ring_of_power")
    await container.db.add_to_inventory(p.username, "ring_of_power")
    await container.db.add_to_inventory(p.username, "ring_of_power")
    inv_before = await container.db.get_inventory(p.username)
    assert inv_before.count("ring_of_power") == 3

    removed = await container.db.remove_from_inventory(
        p.username, "ring_of_power", count=2
    )
    assert removed == 2

    inv_after = await container.db.get_inventory(p.username)
    assert inv_after.count("ring_of_power") == 1

    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.mark.asyncio
async def test_custom_exceptions():
    with pytest.raises(NotEnoughAPError):
        raise NotEnoughAPError(required=5, current=2)

    with pytest.raises(PlayerNotFoundError):
        raise PlayerNotFoundError("unknown")


@pytest.mark.asyncio
async def test_inventory_migration_from_legacy_schema():
    import aiosqlite
    db_path = "test_migration.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    # Создаём старую таблицу inventory без колонки id (как было до ORM)
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("CREATE TABLE players (username TEXT PRIMARY KEY, lvl INT, exp INT, stat_points INT, str_stat INT, agi INT, vit INT, int_stat INT, sen INT, hp INT, mp INT, gold INT, location_id TEXT, weapon_id TEXT, armor_id TEXT, accessory_id TEXT, last_daily TEXT, title TEXT DEFAULT 'novice', achievements TEXT DEFAULT '', pvp_wins INT DEFAULT 0, daily_quest_loc TEXT DEFAULT '1', daily_quest_target INT DEFAULT 3, daily_quest_progress INT DEFAULT 0, shield INT DEFAULT 0, bonus_stat_points INT DEFAULT 0)")
        await conn.execute("CREATE TABLE inventory (username TEXT, item_id TEXT)")
        await conn.execute(
            "INSERT INTO inventory (username, item_id) VALUES (?, ?)",
            ("wastle_", "knight_spear"),
        )
        await conn.commit()

    # Инициализируем DBManager - должен смигрировать старую таблицу
    container = AppContainer(db_path=db_path)
    await container.init()

    inv = await container.db.get_inventory("wastle_")
    assert inv == ["knight_spear"]

    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.mark.asyncio
async def test_account_sync():
    db_path = "test_sync.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    container = AppContainer(db_path=db_path)
    await container.init()

    p_tg = await container.get_player("telegram_hero")
    p_tg.gold = 500
    await container.db.save(p_tg)

    code = "ABC123"
    await container.db.create_sync_code(code, "telegram_hero", time.time() + 300)

    twitch_user = "twitch_hero"
    tg_username = await container.db.verify_sync_code(code)
    assert tg_username == "telegram_hero"

    tg_player = await container.db.load(tg_username)
    assert tg_player is not None
    tg_player.linked_twitch = twitch_user
    await container.db.save(tg_player)

    loaded_by_twitch = await container.db.load(twitch_user)
    assert loaded_by_twitch is not None
    assert loaded_by_twitch.username == "telegram_hero"
    assert loaded_by_twitch.gold == 500

    if os.path.exists(db_path):
        os.remove(db_path)
