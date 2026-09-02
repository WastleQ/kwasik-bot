# src/api/server.py

import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.data import DUNGEONS, ITEMS, SPELLS
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
