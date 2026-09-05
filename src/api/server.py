# src/api/server.py

import datetime
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.data import (
    ACHIEVEMENTS,
    CRAFTING_RECIPES,
    DUNGEONS,
    ITEMS,
    SPELLS,
    TITLES,
)
from src.engine import RPGEngine
from src.models import DBManager, Player

app = FastAPI(title="Kwasik Bot RPG API")

db = DBManager("solo_leveling.db")
engine = RPGEngine()

# Ensure static/web directory exists
os.makedirs("src/web", exist_ok=True)
app.mount("/static", StaticFiles(directory="src/web"), name="static")


@app.on_event("startup")
async def startup_event():
    await db.init_db()


class ActionRequest(BaseModel, extra="allow"):
    action: str = ""
    spell_key: str = "шар"


class UpgradeRequest(BaseModel):
    stat: str
    count: int = 1


@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = os.path.join("src", "web", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return "<h1>Kwasik RPG Mini App UI not found</h1>"


@app.get("/api/player/{username}")
async def get_player_profile(username: str):
    username = username.lower().replace("@", "")
    p = await db.load(username)
    if not p:
        p = Player(username=username)
        await db.save(p)
    else:
        engine.clamp_resources(p)

    inv = await db.get_inventory(username)
    rank = engine.get_rank(p.lvl)
    max_hp = engine.get_max_hp(p)
    max_mp = engine.get_max_mp(p)
    stats = engine.get_stats(p)

    return {
        "username": p.username,
        "lvl": p.lvl,
        "exp": p.exp,
        "stat_points": p.stat_points,
        "hp": p.hp,
        "max_hp": max_hp,
        "mp": p.mp,
        "max_mp": max_mp,
        "shield": p.shield,
        "gold": p.gold,
        "location_id": p.location_id,
        "location_name": DUNGEONS.get(p.location_id, {}).get("name", "Город"),
        "title": p.title,
        "rank": rank,
        "stats": stats,
        "inventory": inv,
        "dungeons": DUNGEONS,
        "spells": list(SPELLS.keys()),
    }


@app.post("/api/player/{username}/hunt")
async def player_hunt(username: str, req: ActionRequest):
    username = username.lower().replace("@", "")
    p = await db.load(username)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")

    engine.clamp_resources(p)
    if p.location_id == "0":
        return {"status": "error", "message": "Ты в городе. Выбери врата!"}

    is_magic = req.action.lower() == "каст"
    spell = SPELLS.get(req.spell_key.lower()) if is_magic else None

    if is_magic:
        if not spell:
            return {"status": "error", "message": "Нет такого заклинания."}
        if p.mp < spell["mp_cost"]:
            return {
                "status": "error",
                "message": f"Мало маны! Нужно {spell['mp_cost']} MP.",
            }
        p.mp -= spell["mp_cost"]

    msg, drops = engine.fight(p, DUNGEONS[p.location_id], is_magic, spell)

    drop_names = []
    if drops:
        for drop in drops:
            await db.add_to_inventory(p.username, drop)
            if drop in ITEMS:
                drop_names.append(ITEMS[drop]["name"])

    await db.save(p)

    return {
        "status": "success",
        "message": msg,
        "drops": drop_names,
        "hp": p.hp,
        "max_hp": engine.get_max_hp(p),
        "mp": p.mp,
        "max_mp": engine.get_max_mp(p),
        "shield": p.shield,
        "exp": p.exp,
        "lvl": p.lvl,
        "gold": p.gold,
    }


@app.post("/api/player/{username}/travel/{loc_id}")
async def player_travel(username: str, loc_id: str):
    username = username.lower().replace("@", "")
    if loc_id not in DUNGEONS:
        raise HTTPException(status_code=400, detail="Invalid location ID")

    p = await db.load(username)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")

    p.location_id = loc_id
    await db.save(p)
    return {"status": "success", "location_name": DUNGEONS[loc_id]["name"]}


@app.post("/api/player/{username}/rest")
async def player_rest(username: str):
    username = username.lower().replace("@", "")
    p = await db.load(username)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")

    max_hp = engine.get_max_hp(p)
    max_mp = engine.get_max_mp(p)
    p.hp = max_hp
    p.mp = max_mp
    await db.save(p)
    return {
        "status": "success",
        "hp": p.hp,
        "mp": p.mp,
        "message": "Отдохнул и восстановил силы!",
    }


@app.post("/api/player/{username}/upgrade")
async def player_upgrade(username: str, req: UpgradeRequest):
    username = username.lower().replace("@", "")
    p = await db.load(username)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")

    if p.stat_points < req.count or req.count <= 0:
        return {
            "status": "error",
            "message": f"Недостаточно AP. У тебя: {p.stat_points}",
        }

    mapping = {
        "str": "str_stat",
        "agi": "agi",
        "vit": "vit",
        "int": "int_stat",
        "sen": "sen",
    }
    attr = mapping.get(req.stat.lower())
    if not attr:
        return {"status": "error", "message": "Неверная характеристика"}

    setattr(p, attr, getattr(p, attr) + req.count)
    p.stat_points -= req.count
    engine.clamp_resources(p)
    await db.save(p)

    return {
        "status": "success",
        "message": f"Характеристика {req.stat.upper()} увеличена на {req.count}!",
        "stat_points": p.stat_points,
        "stats": engine.get_stats(p),
    }


@app.get("/api/shop")
async def get_shop():
    return {k: v for k, v in ITEMS.items() if v.get("price", 0) > 0}


@app.post("/api/player/{username}/buy")
async def player_buy(username: str, req: ActionRequest):
    username = username.lower().replace("@", "")
    p = await db.load(username)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")
    tid = req.spell_key
    if tid not in ITEMS or ITEMS[tid].get("price", 0) <= 0:
        return {"status": "error", "message": "Товар не найден"}
    price = ITEMS[tid]["price"]
    if p.gold < price:
        return {"status": "error", "message": "Недостаточно золота"}
    p.gold -= price
    await db.add_to_inventory(p.username, tid)
    await db.save(p)
    return {"status": "success", "message": f"Куплено: {ITEMS[tid]['name']}!"}


@app.post("/api/player/{username}/sell")
async def player_sell(username: str, req: ActionRequest):
    username = username.lower().replace("@", "")
    p = await db.load(username)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")
    tid = req.spell_key
    inv = await db.get_inventory(p.username)
    if tid not in inv:
        return {"status": "error", "message": "Предмет не найден в инвентаре"}
    item = ITEMS[tid]
    base_price = item.get("price", 0)
    sell_price = (base_price // 2) if base_price > 0 else 250
    p.gold += sell_price
    await db.remove_from_inventory(p.username, tid)
    remaining = await db.get_inventory(p.username)
    if tid not in remaining:
        if p.weapon_id == tid:
            p.weapon_id = None
        if p.armor_id == tid:
            p.armor_id = None
        if p.accessory_id == tid:
            p.accessory_id = None
    p.hp = min(p.hp, engine.get_max_hp(p))
    p.mp = min(p.mp, engine.get_max_mp(p))
    await db.save(p)
    return {"status": "success", "message": f"Продано {item['name']} за {sell_price}💰!"}


@app.post("/api/player/{username}/equip")
async def player_equip(username: str, req: ActionRequest):
    username = username.lower().replace("@", "")
    p = await db.load(username)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")
    tid = req.spell_key
    inv = await db.get_inventory(p.username)
    if tid not in inv:
        return {"status": "error", "message": "Предмет не найден в инвентаре"}
    item = ITEMS.get(tid)
    if not item:
        return {"status": "error", "message": "Предмет не существует"}
    slot = item.get("slot")
    if slot == "weapon":
        p.weapon_id = tid
    elif slot == "armor":
        p.armor_id = tid
    elif slot == "accessory":
        p.accessory_id = tid
    else:
        return {"status": "error", "message": "Этот предмет нельзя надеть"}
    p.hp = min(p.hp, engine.get_max_hp(p))
    p.mp = min(p.mp, engine.get_max_mp(p))
    await db.save(p)
    return {"status": "success", "message": f"Экипировано: {item['name']}!"}


@app.post("/api/player/{username}/unequip")
async def player_unequip(username: str, req: ActionRequest):
    username = username.lower().replace("@", "")
    p = await db.load(username)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")
    slot = req.spell_key.lower()
    if slot in ["weapon", "оружие"]:
        p.weapon_id = None
    elif slot in ["armor", "броня"]:
        p.armor_id = None
    elif slot in ["accessory", "аксессуар"]:
        p.accessory_id = None
    else:
        return {"status": "error", "message": "Неверный слот"}
    p.hp = min(p.hp, engine.get_max_hp(p))
    p.mp = min(p.mp, engine.get_max_mp(p))
    await db.save(p)
    return {"status": "success", "message": f"Слот {slot} очищен!"}


@app.post("/api/player/{username}/drink")
async def player_drink(username: str, req: ActionRequest):
    username = username.lower().replace("@", "")
    p = await db.load(username)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")
    tid = req.spell_key
    inv = await db.get_inventory(p.username)
    if tid not in inv or ITEMS[tid].get("type") != "use":
        return {"status": "error", "message": "Зелье не найдено"}
    item = ITEMS[tid]
    if "heal" in item:
        p.hp = min(engine.get_max_hp(p), p.hp + item["heal"])
    if "restore_mp" in item:
        p.mp = min(engine.get_max_mp(p), p.mp + item["restore_mp"])
    await db.remove_from_inventory(p.username, tid)
    await db.save(p)
    return {"status": "success", "message": f"Использовано: {item['name']}!"}


@app.get("/api/crafts")
async def get_crafts():
    return CRAFTING_RECIPES


@app.post("/api/player/{username}/craft")
async def player_craft(username: str, req: ActionRequest):
    username = username.lower().replace("@", "")
    p = await db.load(username)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")
    r_key = req.spell_key
    recipe = CRAFTING_RECIPES.get(r_key)
    if not recipe:
        return {"status": "error", "message": "Рецепт не найден"}
    inv = await db.get_inventory(p.username)
    inv_counts = {i: inv.count(i) for i in set(inv)}
    for mat, count in recipe["req"].items():
        if inv_counts.get(mat, 0) < count:
            return {
                "status": "error",
                "message": f"Недостаточно материалов ({ITEMS[mat]['name']})",
            }
    for mat, count in recipe["req"].items():
        for _ in range(count):
            await db.remove_from_inventory(p.username, mat)
    await db.add_to_inventory(p.username, recipe["key"])
    await db.save(p)
    return {"status": "success", "message": f"Скрафчено: {recipe['name']}!"}


@app.get("/api/player/{username}/quest")
async def get_quest(username: str):
    username = username.lower().replace("@", "")
    p = await db.load(username)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")
    today = str(datetime.date.today())
    if p.last_daily != today and not p.daily_quest_loc:
        p.daily_quest_loc = "1"
        p.daily_quest_target = 3
        p.daily_quest_progress = 0
        await db.save(p)
    loc_name = DUNGEONS.get(p.daily_quest_loc, {}).get("name", "Врата")
    return {
        "completed": p.last_daily == today,
        "loc_name": loc_name,
        "progress": p.daily_quest_progress,
        "target": p.daily_quest_target,
    }


@app.post("/api/player/{username}/claim")
async def claim_quest(username: str):
    username = username.lower().replace("@", "")
    p = await db.load(username)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")
    today = str(datetime.date.today())
    if p.last_daily == today:
        return {"status": "error", "message": "Награда уже получена сегодня"}
    if p.daily_quest_progress < p.daily_quest_target:
        return {"status": "error", "message": "Квест еще не выполнен"}
    p.stat_points += 3
    p.exp += 50
    gold_reward = p.lvl * 100
    p.gold += gold_reward
    p.last_daily = today
    p.hp = engine.get_max_hp(p)
    p.mp = engine.get_max_mp(p)
    engine.check_level_up(p)
    await db.save(p)
    return {
        "status": "success",
        "message": f"Квест выполнен! Награда: +3 AP, {gold_reward}💰!",
    }


@app.get("/api/player/{username}/titles")
async def get_titles(username: str):
    username = username.lower().replace("@", "")
    p = await db.load(username)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")
    unlocked_ach = [a.strip() for a in p.achievements.split(",") if a.strip()]
    return {
        "titles": TITLES,
        "achievements": ACHIEVEMENTS,
        "unlocked_achievements": unlocked_ach,
        "current_title": p.title,
    }


@app.post("/api/player/{username}/title")
async def set_title(username: str, req: ActionRequest):
    username = username.lower().replace("@", "")
    p = await db.load(username)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")
    t_key = req.spell_key
    t_data = TITLES.get(t_key)
    if not t_data:
        return {"status": "error", "message": "Титул не найден"}
    req_ach = t_data.get("req")
    unlocked_ach = [a.strip() for a in p.achievements.split(",") if a.strip()]
    if req_ach and req_ach not in unlocked_ach:
        return {
            "status": "error",
            "message": "Титул заблокирован (требуется достижение)",
        }
    p.title = t_key
    await db.save(p)
    return {"status": "success", "message": f"Титул изменен на {t_data['name']}!"}


@app.get("/api/leaderboard")
async def leaderboard():
    players = await db.get_all_players()
    players.sort(key=lambda x: (x.lvl, x.exp, x.gold), reverse=True)
    return [
        {
            "username": pl.username,
            "lvl": pl.lvl,
            "rank": engine.get_rank(pl.lvl),
            "gold": pl.gold,
            "pvp_wins": getattr(pl, "pvp_wins", 0),
        }
        for pl in players[:10]
    ]
