#!/usr/bin/env python3
import logging
import os

from dotenv import load_dotenv
from telegram import (
    BotCommand,
    InlineKeyboardButton,
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

from src.data import DUNGEONS, ITEMS, SPELLS
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

reply_keyboard = [
    ["⚔️ Охота", "📊 Профиль"],
    ["🚪 Врата", "🎒 Инвентарь"],
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

    # If web app is available, we can attach inline markup below text, and reply_markup is main_markup for bottom keyboard
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
        "🏕️ `/rest` — отдых и восстановление HP/MP\n"
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
    args = context.args or [] or []
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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
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
    application.add_handler(CommandHandler("rest", rest_command))
    application.add_handler(CommandHandler("inventory", inventory_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("🤖 Telegram Bot started with ReplyKeyboardMarkup static buttons...")
    application.run_polling()


if __name__ == "__main__":
    main()
