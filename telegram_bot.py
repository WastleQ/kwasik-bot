#!/usr/bin/env python3
import datetime
import logging
import os

from dotenv import load_dotenv
from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
    WebAppInfo,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

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

load_dotenv()
TOKEN = os.getenv("TG_BOT_TOKEN", "8610234867:AAEONuZCm6arZ4mImXmj_SkKH7swo0i2P10")
WEB_APP_URL = os.getenv("WEB_APP_URL", "")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("TelegramBot")

db = DBManager("solo_leveling.db")
engine = RPGEngine()


def _get_default_quest_loc(lvl: int) -> str:
    if lvl < 10:
        return "1"
    elif lvl < 20:
        return "2"
    elif lvl < 30:
        return "3"
    elif lvl < 40:
        return "4"
    elif lvl < 50:
        return "5"
    else:
        return "6"

reply_keyboard = [
    ["⚔️ Охота", "📊 Профиль"],
    ["🚪 Врата", "🎒 Инвентарь"],
    ["🛍️ Магазин", "📜 Квест"],
    ["🏕️ Отдых", "✨ Магия (Хил/Щит)"],
]
main_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)


async def get_telegram_player(update: Update) -> Player:
    user = update.effective_user
    username = (user.username or user.first_name or "hunter").lower().replace("@", "")
    p = await db.load(username)
    if not p:
        p = Player(username=username)
        await db.save(p)
    else:
        engine.clamp_resources(p)
    return p


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = (user.username or user.first_name or "hunter").lower().replace("@", "")
    await get_telegram_player(update)

    keyboard = []
    if (
        WEB_APP_URL
        and WEB_APP_URL.startswith("https://")
        and "localhost" not in WEB_APP_URL
    ):
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🎮 Открыть Mini App",
                    web_app=WebAppInfo(url=f"{WEB_APP_URL}?user={username}"),
                )
            ]
        )

    text = (
        f"🔥 Привет, Охотник **{user.first_name}**!\n\n"
        "Добро пожаловать в **Kwasik RPG** (Solo Leveling).\n"
        "Используй удобные кнопки внизу экрана или команды:\n\n"
        "📊 `/stats` — профиль и характеристики\n"
        "🚪 `/gates` — список врат / локаций\n"
        "🚀 `/travel <id>` — войти в подземелье\n"
        "⚔️ `/hunt` или `/hunt cast шар` — охота\n"
        "✨ `/cast хил` или `/cast щит` — магия\n"
        "💪 `/upgrade <сила/vit/agi/int/sen> <кол-во>` — кач статов\n"
        "🛍️ `/shop` и `/buy <товар>` — магазин\n"
        "⚔️ `/equip <предмет>` и `/unequip <слот>` — экипировка\n"
        "⚒️ `/crafts` и `/craft <предмет>` — крафт\n"
        "📜 `/quest` и `/claim` — ежедневный квест\n"
        "🏆 `/top` — таблица лидеров\n"
        "🏕️ `/rest` — отдых и восстановление\n"
        "🎒 `/inventory` — инвентарь\n"
    )

    await update.message.reply_text(
        text, reply_markup=main_markup, parse_mode="Markdown"
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await get_telegram_player(update)
    st = engine.get_stats(p)
    rank = engine.get_rank(p.lvl)
    max_hp = engine.get_max_hp(p)
    max_mp = engine.get_max_mp(p)
    shield_str = f"(+{p.shield})" if p.shield > 0 else ""
    hp_display = f"{p.hp}{shield_str}"

    w_name = (
        ITEMS[p.weapon_id]["name"] if p.weapon_id and p.weapon_id in ITEMS else "Пусто"
    )
    a_name = (
        ITEMS[p.armor_id]["name"] if p.armor_id and p.armor_id in ITEMS else "Пусто"
    )
    acc_name = (
        ITEMS[p.accessory_id]["name"]
        if p.accessory_id and p.accessory_id in ITEMS
        else "Пусто"
    )
    loc_name = DUNGEONS.get(p.location_id, {}).get("name", "Город")

    msg = (
        f"👤 **@{p.username}** [{rank}] | Ур. {p.lvl}\n"
        f"📍 Локация: {loc_name}\n"
        f"❤️ HP: {hp_display}/{max_hp} | 🔮 MP: {p.mp}/{max_mp}\n"
        f"💰 Золото: {p.gold} | 💎 Свободно AP: {p.stat_points}\n\n"
        f"⚔️ Оружие: {w_name}\n🛡️ Броня: {a_name}\n💍 Аксессуар: {acc_name}\n\n"
        f"📊 Характеристики:\n"
        f"• Сила (STR): {st['str']}\n"
        f"• Ловкость (AGI): {st['agi']}\n"
        f"• Выносливость (VIT): {st['vit']}\n"
        f"• Интеллект (INT): {st['int']}\n"
        f"• Восприятие (SEN): {st['sen']}"
    )
    await update.message.reply_text(
        msg, parse_mode="Markdown", reply_markup=main_markup
    )


async def gates_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = [f"[{i}] {d['name']}" for i, d in DUNGEONS.items()]
    await update.message.reply_text(
        "🚪 **Доступные врата:**\n" + "\n".join(info),
        parse_mode="Markdown",
        reply_markup=main_markup,
    )


async def travel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    if not args or args[0] not in DUNGEONS:
        await update.message.reply_text(
            "❌ Укажите верный ID врат. Пример: `/travel 1` (используй `/gates`)",
            parse_mode="Markdown",
            reply_markup=main_markup,
        )
        return
    loc_id = args[0]
    p = await get_telegram_player(update)
    p.location_id = loc_id
    await db.save(p)
    await update.message.reply_text(
        f"🚀 @{p.username} вошел в: **{DUNGEONS[loc_id]['name']}**",
        parse_mode="Markdown",
        reply_markup=main_markup,
    )


async def hunt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await get_telegram_player(update)
    if p.location_id == "0":
        await update.message.reply_text(
            "🏘️ Ты в городе. Используй `/travel [ID]` чтобы войти во врата!",
            parse_mode="Markdown",
            reply_markup=main_markup,
        )
        return

    args = context.args or []
    is_magic = len(args) > 0 and args[0].lower() == "каст"
    spell_key = args[1].lower() if is_magic and len(args) > 1 else "шар"
    spell = SPELLS.get(spell_key) if is_magic else None

    if is_magic:
        if not spell:
            await update.message.reply_text(
                f"❌ Нет такого заклинания. Доступны: {', '.join(SPELLS.keys())}",
                reply_markup=main_markup,
            )
            return
        if p.mp < spell["mp_cost"]:
            await update.message.reply_text(
                f"❌ Мало маны! Нужно {spell['mp_cost']} MP (у тебя {p.mp}).",
                reply_markup=main_markup,
            )
            return
        p.mp -= spell["mp_cost"]

    msg, drops = engine.fight(p, DUNGEONS[p.location_id], is_magic, spell)
    msg = f"@{p.username} {msg}"

    if drops:
        drop_names = []
        for drop in drops:
            await db.add_to_inventory(p.username, drop)
            if drop in ITEMS:
                drop_names.append(ITEMS[drop]["name"])
        if len(drop_names) == 1:
            msg += f" 💎 Находка: {drop_names[0]}!"
        elif len(drop_names) > 1:
            msg += f" 💎 Находки: {', '.join(drop_names)}!"

    today = str(datetime.date.today())
    if p.last_daily != today:
        loc = _get_default_quest_loc(p.lvl)
        if not p.daily_quest_loc:
            p.daily_quest_loc = loc
            p.daily_quest_target = 3

        if (
            p.location_id == p.daily_quest_loc
            and p.daily_quest_progress < p.daily_quest_target
        ):
            p.daily_quest_progress += 1
            msg += f" 🎯 [Квест Системы: {p.daily_quest_progress}/{p.daily_quest_target}]"
            if p.daily_quest_progress >= p.daily_quest_target:
                msg += " ✨ Квест выполнен! Введите /claim чтобы забрать бонус!"

    await db.save(p)
    await update.message.reply_text(msg, reply_markup=main_markup)


async def cast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    if not args:
        await update.message.reply_text(
            f"❌ Укажи заклинание. Доступны: {', '.join(SPELLS.keys())}",
            reply_markup=main_markup,
        )
        return
    spell_key = args[0].lower().strip()
    spell = SPELLS.get(spell_key)
    if not spell:
        await update.message.reply_text(
            "❌ Нет такого заклинания.", reply_markup=main_markup
        )
        return

    p = await get_telegram_player(update)
    if p.mp < spell["mp_cost"]:
        await update.message.reply_text(
            f"❌ Мало маны! Нужно {spell['mp_cost']} MP (у тебя {p.mp}).",
            reply_markup=main_markup,
        )
        return

    p.mp -= spell["mp_cost"]
    st = engine.get_stats(p)
    s_type = spell.get("type", "attack")
    max_hp = engine.get_max_hp(p)

    if s_type == "heal":
        heal_val = spell.get("heal", 250) + int(st["int"] * 1.5)
        p.hp = min(max_hp, p.hp + heal_val)
        await db.save(p)
        await update.message.reply_text(
            f"✨ @{p.username} кастует [{spell['name']}] и восстанавливает {heal_val} HP! (❤️ {p.hp}/{max_hp} HP, 🔮 {p.mp}/{engine.get_max_mp(p)} MP)",
            reply_markup=main_markup,
        )
    elif s_type == "shield":
        shield_val = spell.get("shield", 150) + int(st["int"] * 1.5)
        p.shield += shield_val
        shield_str = f" (+{p.shield} щит)" if p.shield > 0 else ""
        await db.save(p)
        await update.message.reply_text(
            f"🛡️ @{p.username} создает Магический щит (+{shield_val} прочности)! (❤️ {p.hp}{shield_str}/{max_hp} HP, 🔮 {p.mp}/{engine.get_max_mp(p)} MP)",
            reply_markup=main_markup,
        )
    else:
        p.mp += spell["mp_cost"]
        await update.message.reply_text(
            "❌ Боевые заклинания нужно использовать через `/hunt cast [spell]` во время охоты.",
            parse_mode="Markdown",
            reply_markup=main_markup,
        )


async def upgrade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    if not args:
        await update.message.reply_text(
            "❓ Использование: `/upgrade <сила/agi/vit/int/sen> [кол-во]`",
            parse_mode="Markdown",
            reply_markup=main_markup,
        )
        return

    stat = args[0].lower()
    count = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1

    p = await get_telegram_player(update)
    if p.stat_points < count or count <= 0:
        await update.message.reply_text(
            f"❌ Недостаточно AP. У тебя: {p.stat_points}", reply_markup=main_markup
        )
        return

    mapping = {
        "сила": "str_stat",
        "str": "str_stat",
        "силу": "str_stat",
        "ловкость": "agi",
        "agi": "agi",
        "ловку": "agi",
        "живучесть": "vit",
        "vit": "vit",
        "хп": "vit",
        "живка": "vit",
        "инт": "int_stat",
        "int": "int_stat",
        "интеллект": "int_stat",
        "восприятие": "sen",
        "sen": "sen",
        "сен": "sen",
    }
    attr = mapping.get(stat)
    if not attr:
        await update.message.reply_text(
            "❓ Выбери: сила (str), ловкость (agi), живучесть (vit), инт (int), восприятие (sen)",
            reply_markup=main_markup,
        )
        return

    setattr(p, attr, getattr(p, attr) + count)
    p.stat_points -= count
    engine.clamp_resources(p)
    await db.save(p)

    await update.message.reply_text(
        f"✅ @{p.username}, характеристика `{stat.upper()}` увеличена на {count}! Осталось AP: {p.stat_points}",
        parse_mode="Markdown",
        reply_markup=main_markup,
    )


async def rest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await get_telegram_player(update)
    max_hp = engine.get_max_hp(p)
    max_mp = engine.get_max_mp(p)
    p.hp = max_hp
    p.mp = max_mp
    await db.save(p)
    await update.message.reply_text(
        f"🏕️ @{p.username} отдохнул и полностью восстановил HP ({max_hp}) и MP ({max_mp})!",
        reply_markup=main_markup,
    )


async def inventory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await get_telegram_player(update)
    inv = await db.get_inventory(p.username)
    if not inv:
        await update.message.reply_text(
            "🎒 Твой инвентарь пуст.", reply_markup=main_markup
        )
        return

    items_named = []
    for item_id in inv:
        if item_id in ITEMS:
            items_named.append(ITEMS[item_id]["name"])
        else:
            items_named.append(item_id)

    max_len = 460
    text = ", ".join(items_named)
    if len(text) > max_len:
        text = text[:max_len] + "... (и др.)"

    await update.message.reply_text(
        f"🎒 **Инвентарь @{p.username}:**\n{text}",
        parse_mode="Markdown",
        reply_markup=main_markup,
    )


async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    potions = []
    gear = []
    crystals = []
    for k, i in ITEMS.items():
        if i.get("price", 0) <= 0:
            continue
        if i.get("type") == "use":
            potions.append(f"{i['name']} ({i['price']}💰)")
        elif i.get("type") == "material":
            rank = k.split("_")[1].upper() if "_" in k else "E"
            crystals.append(f"{rank} ({i['price']}💰)")
        else:
            gear.append(f"{i['name']} ({i['price']}💰)")

    lines = ["🏪 **Магазин:**"]
    if potions:
        lines.append("🧪 Расходники: " + " | ".join(potions))
    if gear:
        lines.append("⚔️ Экипировка: " + " | ".join(gear))
    if crystals:
        lines.append("💎 Кристаллы: " + " | ".join(crystals))
    lines.append("\n🛒 Купить: `/buy <название>`")
    await update.message.reply_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=main_markup
    )


async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    name = " ".join(args).strip()
    if not name:
        await update.message.reply_text(
            "❌ Укажите товар. Пример: `/buy зелье здоровья`",
            parse_mode="Markdown",
            reply_markup=main_markup,
        )
        return
    p = await get_telegram_player(update)
    tid = next(
        (
            k
            for k, v in ITEMS.items()
            if name.lower() in v["name"].lower() and v.get("price", 0) > 0
        ),
        None,
    )
    if not tid:
        await update.message.reply_text(
            "❌ Товар не найден.", reply_markup=main_markup
        )
        return
    price = ITEMS[tid]["price"]
    if p.gold < price:
        await update.message.reply_text(
            "❌ Недостаточно золота.", reply_markup=main_markup
        )
        return
    p.gold -= price
    await db.add_to_inventory(p.username, tid)
    await db.save(p)
    await update.message.reply_text(
        f"✅ Куплено: **{ITEMS[tid]['name']}**!",
        parse_mode="Markdown",
        reply_markup=main_markup,
    )


async def equip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    name = " ".join(args).strip()
    if not name:
        await update.message.reply_text(
            "❌ Укажите предмет для экипировки. Пример: `/equip меч`",
            parse_mode="Markdown",
            reply_markup=main_markup,
        )
        return
    p = await get_telegram_player(update)
    inv = await db.get_inventory(p.username)
    tid = next((k for k in inv if name.lower() in ITEMS[k]["name"].lower()), None)
    if not tid:
        await update.message.reply_text(
            "❌ Предмет не найден в вашем инвентаре.", reply_markup=main_markup
        )
        return

    slot = ITEMS[tid].get("slot")
    if slot == "weapon":
        p.weapon_id = tid
    elif slot == "armor":
        p.armor_id = tid
    elif slot == "accessory":
        p.accessory_id = tid
    else:
        await update.message.reply_text(
            "❌ Этот предмет нельзя надеть.", reply_markup=main_markup
        )
        return

    p.hp = min(p.hp, engine.get_max_hp(p))
    p.mp = min(p.mp, engine.get_max_mp(p))
    await db.save(p)
    await update.message.reply_text(
        f"✅ Экипировано: **{ITEMS[tid]['name']}** ({slot})",
        parse_mode="Markdown",
        reply_markup=main_markup,
    )


async def unequip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    if not args:
        await update.message.reply_text(
            "❌ Укажите слот: `/unequip оружие`, `/unequip броня`, `/unequip аксессуар`",
            parse_mode="Markdown",
            reply_markup=main_markup,
        )
        return
    slot = args[0].lower()
    p = await get_telegram_player(update)
    if slot in ["оружие", "weapon"]:
        p.weapon_id = None
    elif slot in ["броня", "armor"]:
        p.armor_id = None
    elif slot in ["аксессуар", "сфера", "accessory"]:
        p.accessory_id = None
    else:
        await update.message.reply_text(
            "❌ Неверный слот.", reply_markup=main_markup
        )
        return
    p.hp = min(p.hp, engine.get_max_hp(p))
    p.mp = min(p.mp, engine.get_max_mp(p))
    await db.save(p)
    await update.message.reply_text(
        f"✅ Слот `{slot}` теперь пуст.",
        parse_mode="Markdown",
        reply_markup=main_markup,
    )


async def crafts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    recipes_info = []
    for r in CRAFTING_RECIPES.values():
        reqs = ", ".join(
            [f"{count}x {ITEMS[mat]['name']}" for mat, count in r["req"].items()]
        )
        recipes_info.append(f"• **{r['name']}**: [{reqs}] ({r['desc']})")
    await update.message.reply_text(
        "⚒️ **Рецепты крафта:**\n"
        + "\n".join(recipes_info)
        + "\n\n🛠️ Скрафтить: `/craft <название>`",
        parse_mode="Markdown",
        reply_markup=main_markup,
    )


async def craft_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    name = " ".join(args).strip()
    if not name:
        await update.message.reply_text(
            "❌ Укажите рецепт. Посмотрите `/crafts`",
            parse_mode="Markdown",
            reply_markup=main_markup,
        )
        return

    norm_input = name.lower().replace(" ", "").replace("-", "").replace("_", "")
    recipe = None
    for r_key, r_data in CRAFTING_RECIPES.items():
        norm_key = r_key.lower().replace("_", "")
        norm_name = (
            r_data["name"]
            .lower()
            .replace(" ", "")
            .replace("-", "")
            .replace("_", "")
        )
        if (
            norm_input == norm_key
            or norm_input in norm_name
            or norm_name in norm_input
        ):
            recipe = r_data
            break

    if not recipe:
        await update.message.reply_text(
            "❌ Рецепт не найден.", reply_markup=main_markup
        )
        return

    p = await get_telegram_player(update)
    inv = await db.get_inventory(p.username)
    inv_counts = {i: inv.count(i) for i in set(inv)}

    for mat, count in recipe["req"].items():
        if inv_counts.get(mat, 0) < count:
            await update.message.reply_text(
                f"❌ Недостаточно материалов! Нужно {count}x {ITEMS[mat]['name']}",
                reply_markup=main_markup,
            )
            return

    for mat, count in recipe["req"].items():
        for _ in range(count):
            await db.remove_from_inventory(p.username, mat)

    await db.add_to_inventory(p.username, recipe["key"])
    await db.save(p)
    await update.message.reply_text(
        f"✨ Успешно скрафчено: **{recipe['name']}**!",
        parse_mode="Markdown",
        reply_markup=main_markup,
    )


async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    if not args:
        await update.message.reply_text(
            "❌ Пример продажи: `/sell кристалл e 3`",
            parse_mode="Markdown",
            reply_markup=main_markup,
        )
        return
    count = 1
    item_query = " ".join(args)
    if len(args) > 1 and args[-1].isdigit():
        count = int(args[-1])
        item_query = " ".join(args[:-1])

    p = await get_telegram_player(update)
    inv = await db.get_inventory(p.username)
    tid = next(
        (k for k in inv if item_query.lower() in ITEMS[k]["name"].lower()), None
    )
    if not tid:
        await update.message.reply_text(
            "❌ Предмет не найден в инвентаре.", reply_markup=main_markup
        )
        return

    item = ITEMS[tid]
    available_count = inv.count(tid)
    sell_count = min(count, available_count)
    if sell_count <= 0:
        await update.message.reply_text(
            "❌ Недостаточно предметов для продажи.", reply_markup=main_markup
        )
        return

    base_price = item.get("price", 0)
    unit_price = base_price // 2 if base_price > 0 else 250
    sell_price = unit_price * sell_count
    p.gold += sell_price

    for _ in range(sell_count):
        await db.remove_from_inventory(p.username, tid)

    remaining_inv = await db.get_inventory(p.username)
    if tid not in remaining_inv:
        if p.weapon_id == tid:
            p.weapon_id = None
        if p.armor_id == tid:
            p.armor_id = None
        if p.accessory_id == tid:
            p.accessory_id = None

    p.hp = min(p.hp, engine.get_max_hp(p))
    p.mp = min(p.mp, engine.get_max_mp(p))
    await db.save(p)
    await update.message.reply_text(
        f"✅ Продано {sell_count}x {item['name']} за {sell_price}💰!",
        reply_markup=main_markup,
    )


async def quest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await get_telegram_player(update)
    today = str(datetime.date.today())
    if p.last_daily != today:
        loc = _get_default_quest_loc(p.lvl)
        p.daily_quest_loc = loc
        p.daily_quest_target = 3
        p.daily_quest_progress = 0
        await db.save(p)

    if p.last_daily == today:
        await update.message.reply_text(
            f"📜 @{p.username}, ежедневный квест на сегодня уже выполнен!",
            reply_markup=main_markup,
        )
        return

    loc_name = DUNGEONS.get(p.daily_quest_loc, {}).get("name", "Врата")
    await update.message.reply_text(
        f"📜 **Ежедневный квест Системы:**\n"
        f"• Цель: Совершить 3 охоты в локации **{loc_name}**\n"
        f"• Прогресс: {p.daily_quest_progress}/{p.daily_quest_target}\n\n"
        f"После выполнения введите `/claim`, чтобы забрать награду!",
        parse_mode="Markdown",
        reply_markup=main_markup,
    )


async def claim_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await get_telegram_player(update)
    today = str(datetime.date.today())
    if p.last_daily == today:
        await update.message.reply_text(
            "❌ Вы уже забрали награду за квест сегодня.", reply_markup=main_markup
        )
        return
    if p.daily_quest_progress < p.daily_quest_target:
        await update.message.reply_text(
            f"❌ Квест еще не выполнен ({p.daily_quest_progress}/{p.daily_quest_target}).",
            reply_markup=main_markup,
        )
        return

    p.stat_points += 3
    p.exp += 50
    gold_reward = p.lvl * 100
    p.gold += gold_reward
    p.last_daily = today
    p.hp = engine.get_max_hp(p)
    p.mp = engine.get_max_mp(p)

    leveled_up = engine.check_level_up(p)
    lvl_up_msg = f" 🎉 УРОВЕНЬ ПОВЫШЕН ДО {p.lvl}!" if leveled_up else ""

    await db.save(p)
    await update.message.reply_text(
        f"🎁 Квест Системы выполнен! Награда: +3 AP, +50 EXP, {gold_reward}💰, полное восстановление сил!{lvl_up_msg}",
        reply_markup=main_markup,
    )


async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    players = await db.get_all_players()
    players.sort(key=lambda x: (x.lvl, x.exp, x.gold), reverse=True)
    top10 = players[:10]
    lines = ["🏆 **Топ Охотников Kwasik RPG:**"]
    for idx, pl in enumerate(top10, 1):
        rk = engine.get_rank(pl.lvl)
        lines.append(f"{idx}. @{pl.username} — Ур. {pl.lvl} [{rk}] (💰 {pl.gold})")
    await update.message.reply_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=main_markup
    )


async def achievements_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await get_telegram_player(update)
    unlocked = [a.strip() for a in p.achievements.split(",") if a.strip()]
    if not unlocked:
        await update.message.reply_text(
            f"🏆 @{p.username}, у тебя пока нет разблокированных достижений.",
            reply_markup=main_markup,
        )
        return
    ach_names = [ACHIEVEMENTS[a]["name"] for a in unlocked if a in ACHIEVEMENTS]
    await update.message.reply_text(
        f"🏆 Достижения @{p.username}: " + ", ".join(ach_names),
        reply_markup=main_markup,
    )


async def titles_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await get_telegram_player(update)
    unlocked_ach = [a.strip() for a in p.achievements.split(",") if a.strip()]
    lines = []
    for key, t in TITLES.items():
        req = t.get("req")
        is_unlocked = req is None or req in unlocked_ach
        active_mark = " (Активен)" if p.title == key else ""
        if is_unlocked:
            lines.append(f"{t['name']}{active_mark}: 🔓 Доступен")
        else:
            lines.append(f"{t['name']}{active_mark}")
    await update.message.reply_text(
        "👑 Титулы: " + " | ".join(lines), reply_markup=main_markup
    )


async def title_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    title_input = " ".join(args).strip()
    if not title_input:
        await update.message.reply_text(
            "❌ Укажите название титула. Посмотрите `/titles`",
            parse_mode="Markdown",
            reply_markup=main_markup,
        )
        return

    norm_input = title_input.lower().replace(" ", "").replace("-", "").replace("_", "")
    matched_key = None
    for key, t_data in TITLES.items():
        norm_key = key.lower().replace("_", "")
        norm_name = (
            t_data["name"]
            .lower()
            .replace(" ", "")
            .replace("-", "")
            .replace("_", "")
        )
        if norm_input == norm_key or norm_input == norm_name:
            matched_key = key
            break

    if not matched_key:
        await update.message.reply_text(
            "❌ Такой титул не найден. Посмотрите `/titles`",
            reply_markup=main_markup,
        )
        return

    p = await get_telegram_player(update)
    t_data = TITLES[matched_key]
    req = t_data.get("req")
    unlocked_ach = [a.strip() for a in p.achievements.split(",") if a.strip()]

    if req is not None and req not in unlocked_ach:
        await update.message.reply_text(
            f"❌ Этот титул заблокирован! Требуется достижение: {ACHIEVEMENTS.get(req, {}).get('name', req)}",
            reply_markup=main_markup,
        )
        return

    p.title = matched_key
    await db.save(p)
    await update.message.reply_text(
        f"👑 @{p.username} сменил титул на: **{t_data['name']}**!",
        parse_mode="Markdown",
        reply_markup=main_markup,
    )


async def spells_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not SPELLS:
        await update.message.reply_text("🔮 Список заклинаний пуст.", reply_markup=main_markup)
        return
    msg = "🔮 **Доступные заклинания:**\n"
    spells_info = []
    for key, s in SPELLS.items():
        if s.get("type") == "attack":
            info = f"• **{s['name']}** (`{key}`): {s['mp_cost']} MP (мн. x{s['damage_mult']})"
        elif s.get("type") == "heal":
            info = f"• **{s['name']}** (`{key}`): {s['mp_cost']} MP (+{s['heal']} HP)"
        elif s.get("type") == "shield":
            info = f"• **{s['name']}** (`{key}`): {s['mp_cost']} MP (+{s['shield']} Щит)"
        else:
            info = f"• **{s['name']}** (`{key}`): {s['mp_cost']} MP"
        spells_info.append(info)
    msg += "\n".join(spells_info) + "\n\n✨ Использование: `/hunt cast <ключ>` или `/cast <хил/щит>`"
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_markup)


async def top_gold_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    players = await db.get_all_players()
    players.sort(key=lambda x: x.gold, reverse=True)
    top10 = players[:10]
    lines = ["💰 **Топ Богачей Kwasik RPG:**"]
    for idx, pl in enumerate(top10, 1):
        lines.append(f"{idx}. @{pl.username} — {pl.gold} 💰")
    await update.message.reply_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=main_markup
    )


async def top_pvp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    players = await db.get_all_players()
    players.sort(key=lambda x: getattr(x, "pvp_wins", 0), reverse=True)
    top10 = players[:10]
    lines = ["⚔️ **Топ Дуэлянтов (PvP):**"]
    for idx, pl in enumerate(top10, 1):
        wins = getattr(pl, "pvp_wins", 0)
        lines.append(f"{idx}. @{pl.username} — {wins} побед")
    await update.message.reply_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=main_markup
    )


async def drink_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    name = " ".join(args).strip()
    p = await get_telegram_player(update)
    inv = await db.get_inventory(p.username)
    tid = next(
        (
            k
            for k in inv
            if (not name or name.lower() in ITEMS[k]["name"].lower())
            and ITEMS[k]["type"] == "use"
        ),
        None,
    )
    if not tid:
        await update.message.reply_text(
            "❌ Зелье не найдено в инвентаре. Используйте `/drink <зелье>`",
            parse_mode="Markdown",
            reply_markup=main_markup,
        )
        return
    item = ITEMS[tid]
    if "heal" in item:
        p.hp = min(engine.get_max_hp(p), p.hp + item["heal"])
    if "restore_mp" in item:
        p.mp = min(engine.get_max_mp(p), p.mp + item["restore_mp"])
    await db.remove_from_inventory(p.username, tid)
    await db.save(p)
    await update.message.reply_text(
        f"🧪 @{p.username} использовал **{item['name']}**! (❤️ {p.hp}/{engine.get_max_hp(p)}, 🔮 {p.mp}/{engine.get_max_mp(p)})",
        parse_mode="Markdown",
        reply_markup=main_markup,
    )


async def transfer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    if len(args) < 3:
        await update.message.reply_text(
            "❌ Формат:\n`/transfer gold @юзер <сумма>`\n`/transfer item @юзер <название>`",
            parse_mode="Markdown",
            reply_markup=main_markup,
        )
        return
    cat = args[0].lower()
    target_name = args[1].strip("@").lower()
    arg_val = " ".join(args[2:])
    user = update.effective_user
    sender_name = (user.username or user.first_name).lower().replace("@", "")

    if target_name == sender_name:
        await update.message.reply_text("❌ Нельзя передавать предметы самому себе.", reply_markup=main_markup)
        return

    sender_p = await get_telegram_player(update)
    target_p = await db.load(target_name)
    if not target_p:
        await update.message.reply_text(f"❌ Игрок '@{target_name}' не найден в базе.", reply_markup=main_markup)
        return

    if cat in ["gold", "золото"]:
        try:
            amount = int(arg_val)
        except ValueError:
            await update.message.reply_text("❌ Укажите корректную сумму золота.", reply_markup=main_markup)
            return
        if amount <= 0 or sender_p.gold < amount:
            await update.message.reply_text(f"❌ Недостаточно золота (в наличии: {sender_p.gold}💰).", reply_markup=main_markup)
            return
        sender_p.gold -= amount
        target_p.gold += amount
        await db.save(sender_p)
        await db.save(target_p)
        await update.message.reply_text(f"🤝 @{sender_p.username} передал @{target_p.username} {amount}💰!", reply_markup=main_markup)
    elif cat in ["item", "предмет"]:
        inv = await db.get_inventory(sender_p.username)
        tid = next((k for k in inv if arg_val.lower() in ITEMS[k]["name"].lower()), None)
        if not tid:
            await update.message.reply_text("❌ У тебя нет такого предмета в инвентаре.", reply_markup=main_markup)
            return
        await db.remove_from_inventory(sender_p.username, tid)
        await db.add_to_inventory(target_p.username, tid)
        await update.message.reply_text(f"🎁 @{sender_p.username} передал @{target_p.username} предмет: **{ITEMS[tid]['name']}**!", parse_mode="Markdown", reply_markup=main_markup)
    else:
        await update.message.reply_text("❌ Использование: `/transfer gold` или `/transfer item`", parse_mode="Markdown", reply_markup=main_markup)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.args = []
    if text == "⚔️ Охота":
        await hunt_command(update, context)
    elif text == "📊 Профиль":
        await stats_command(update, context)
    elif text == "🚪 Врата":
        await gates_command(update, context)
    elif text == "🎒 Инвентарь":
        await inventory_command(update, context)
    elif text == "🏕️ Отдых":
        await rest_command(update, context)
    elif text == "🛍️ Магазин":
        await shop_command(update, context)
    elif text == "📜 Квест":
        await quest_command(update, context)
    elif text == "✨ Магия (Хил/Щит)":
        await update.message.reply_text(
            "✨ Используй команды магии:\n• `/cast хил` — восстановить HP\n• `/cast щит` — создать щит\n• `/hunt cast шар` — огненный шар на охоте",
            parse_mode="Markdown",
            reply_markup=main_markup,
        )


async def post_init(application):
    commands = [
        BotCommand("stats", "📊 Профиль и характеристики"),
        BotCommand("gates", "🚪 Доступные врата"),
        BotCommand("travel", "🚀 Войти во врата (ID)"),
        BotCommand("hunt", "⚔️ Охота на монстров"),
        BotCommand("cast", "✨ Использовать магию"),
        BotCommand("upgrade", "💪 Прокачка статов (AP)"),
        BotCommand("shop", "🏪 Магазин"),
        BotCommand("buy", "🛒 Купить товар"),
        BotCommand("equip", "⚔️ Экипировать предмет"),
        BotCommand("unequip", "🛡️ Снять предмет"),
        BotCommand("crafts", "⚒️ Рецепты крафта"),
        BotCommand("craft", "✨ Скрафтить предмет"),
        BotCommand("sell", "💰 Продать предмет"),
        BotCommand("quest", "📜 Ежедневный квест"),
        BotCommand("claim", "🎁 Забрать награду квеста"),
        BotCommand("top", "🏆 Топ игроков"),
        BotCommand("top_gold", "💰 Топ богачей"),
        BotCommand("top_pvp", "⚔️ Топ дуэлянтов"),
        BotCommand("achievements", "🏆 Достижения"),
        BotCommand("titles", "👑 Список титулов"),
        BotCommand("title", "👑 Сменить титул"),
        BotCommand("spells", "🔮 Заклинания"),
        BotCommand("drink", "🧪 Выпить зелье"),
        BotCommand("transfer", "🤝 Передать золото/предмет"),
        BotCommand("rest", "🏕️ Отдых и восстановление HP/MP"),
        BotCommand("inventory", "🎒 Инвентарь"),
    ]
    await application.bot.set_my_commands(commands)


def main():
    if not TOKEN:
        logger.error("❌ Telegram Bot Token not found!")
        return

    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("profile", stats_command))
    application.add_handler(CommandHandler("gates", gates_command))
    application.add_handler(CommandHandler("travel", travel_command))
    application.add_handler(CommandHandler("hunt", hunt_command))
    application.add_handler(CommandHandler("cast", cast_command))
    application.add_handler(CommandHandler("upgrade", upgrade_command))
    application.add_handler(CommandHandler("shop", shop_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("equip", equip_command))
    application.add_handler(CommandHandler("unequip", unequip_command))
    application.add_handler(CommandHandler("crafts", crafts_command))
    application.add_handler(CommandHandler("craft", craft_command))
    application.add_handler(CommandHandler("sell", sell_command))
    application.add_handler(CommandHandler("quest", quest_command))
    application.add_handler(CommandHandler("claim", claim_command))
    application.add_handler(CommandHandler("top", top_command))
    application.add_handler(CommandHandler("top_gold", top_gold_command))
    application.add_handler(CommandHandler("top_pvp", top_pvp_command))
    application.add_handler(CommandHandler("achievements", achievements_command))
    application.add_handler(CommandHandler("titles", titles_command))
    application.add_handler(CommandHandler("title", title_command))
    application.add_handler(CommandHandler("spells", spells_command))
    application.add_handler(CommandHandler("drink", drink_command))
    application.add_handler(CommandHandler("transfer", transfer_command))
    application.add_handler(CommandHandler("rest", rest_command))
    application.add_handler(CommandHandler("inventory", inventory_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("🤖 Telegram Bot started with full feature parity and static buttons...")
    application.run_polling()


if __name__ == "__main__":
    main()
