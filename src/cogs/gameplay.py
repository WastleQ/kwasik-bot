import datetime
import time

from twitchio.ext import commands

from src.config import ADMINS
from src.data import DUNGEONS, ITEMS, SPELLS


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


class GameplayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rest_cooldowns = {}
        self.hunt_cooldowns = {}

    @commands.command(name="квест")
    async def cmd_quest(self, ctx):
        p = await self.bot.get_player(ctx.author.name)
        today = str(datetime.date.today())  # noqa: DTZ011
        if p.last_daily != today:
            loc = _get_default_quest_loc(p.lvl)
            p.daily_quest_loc = loc
            p.daily_quest_target = 3
            p.daily_quest_progress = 0
            await self.bot.db.save(p)

        if p.last_daily == today:
            await ctx.send(
                f"📜 @{p.username}, ежедневный квест на сегодня уже выполнен! Ждем сброса завтра."
            )
            return

        loc_name = DUNGEONS[p.daily_quest_loc]["name"]
        await ctx.send(
            f"📜 Ежедневный квест Системы: Уничтожьте {p.daily_quest_target} монстров в локации «{loc_name}»! Прогресс: {p.daily_quest_progress}/{p.daily_quest_target}. Введите !охота в этих вратах и !награда после завершения."
        )

    @commands.command(name="награда")
    async def cmd_reward(self, ctx):
        p = await self.bot.get_player(ctx.author.name)
        today = str(datetime.date.today())  # noqa: DTZ011
        if p.last_daily == today:
            await ctx.send(
                f"🚫 @{p.username}, ты уже забрал ежедневную награду сегодня!"
            )
            return

        loc = _get_default_quest_loc(p.lvl)
        if not p.daily_quest_loc:
            p.daily_quest_loc = loc
            p.daily_quest_target = 3

        if p.daily_quest_progress < p.daily_quest_target:
            loc_name = DUNGEONS[p.daily_quest_loc]["name"]
            await ctx.send(
                f"🚫 @{p.username}, ежедневный квест еще не выполнен! Прогресс: {p.daily_quest_progress}/{p.daily_quest_target} в локации «{loc_name}». Используйте !охота."
            )
            return

        p.stat_points += 3
        p.exp += 50
        gold_reward = p.lvl * 100
        p.gold += gold_reward
        p.last_daily = today
        p.hp = self.bot.engine.get_max_hp(p)
        p.mp = self.bot.engine.get_max_mp(p)

        leveled_up = self.bot.engine.check_level_up(p)
        lvl_up_msg = f" 🎉 УРОВЕНЬ ПОВЫШЕН ДО {p.lvl}!" if leveled_up else ""

        await self.bot.db.save(p)
        await ctx.send(
            f"🎁 @{p.username} выполнил ежедневный квест Системы! Награда: +3 AP, +50 EXP, {gold_reward}💰, полное восстановление сил!{lvl_up_msg}"
        )

    @commands.command(name="отдых")
    async def cmd_rest(self, ctx):
        p = await self.bot.get_player(ctx.author.name)
        now = time.time()
        last_rest = self.rest_cooldowns.get(p.username, 0)
        cooldown_duration = 600  # 10 minutes

        if now - last_rest < cooldown_duration:
            remaining = int(cooldown_duration - (now - last_rest))
            mins = remaining // 60
            secs = remaining % 60
            await ctx.send(f"❌ @{p.username}, подожди еще {mins} мин {secs} сек.")
            return

        max_hp = self.bot.engine.get_max_hp(p)
        max_mp = self.bot.engine.get_max_mp(p)
        if p.hp >= max_hp and p.mp >= max_mp:
            await ctx.send(f"🏕️ @{p.username}, ты и так полностью полон сил!")
            return

        self.rest_cooldowns[p.username] = now
        p.hp = max_hp
        p.mp = max_mp
        await self.bot.db.save(p)
        await ctx.send(
            f"🏕️ @{p.username} отдохнул и полностью восстановил HP ({max_hp}) и MP ({max_mp})!"
        )

    @commands.command(name="врата")
    async def cmd_gates(self, ctx):
        info = [f"[{i}] {d['name']}" for i, d in DUNGEONS.items()]
        await ctx.send("🚪 Доступные врата: " + " | ".join(info))

    @commands.command(name="переход")
    async def cmd_travel(self, ctx, loc_id: str = ""):
        if loc_id not in DUNGEONS:
            await ctx.send("❌ Неверный ID. Используй !врата")
            return
        p = await self.bot.get_player(ctx.author.name)
        p.location_id = loc_id
        await self.bot.db.save(p)
        await ctx.send(f"🚀 @{p.username} вошел в: {DUNGEONS[loc_id]['name']}")

    @commands.command(name="охота")
    async def cmd_hunt(self, ctx, action: str = "", spell_key: str = "шар"):
        p = await self.bot.get_player(ctx.author.name)
        now = time.time()
        is_admin = p.username.lower() in [a.lower() for a in ADMINS]
        last_hunt = self.hunt_cooldowns.get(p.username, 0)
        if not is_admin and now - last_hunt < 10:
            return
        self.hunt_cooldowns[p.username] = now

        if p.location_id == "0":
            await ctx.send("🏘️ Ты в городе. Используй !переход [ID]")
            return

        is_magic = action.lower() == "каст"
        spell = SPELLS.get(spell_key.lower()) if is_magic else None

        if is_magic:
            if not spell:
                await ctx.send(
                    f"❌ Нет такого заклинания. Доступны: {', '.join(SPELLS.keys())}"
                )
                return
            if p.mp < spell["mp_cost"]:
                await ctx.send(f"❌ Мало маны! Нужно {spell['mp_cost']}")
                return
            p.mp -= spell["mp_cost"]

        msg, drops = self.bot.engine.fight(p, DUNGEONS[p.location_id], is_magic, spell)
        msg = f"@{p.username} {msg}"
        if drops:
            drop_names = []
            for drop in drops:
                await self.bot.db.add_to_inventory(p.username, drop)
                if drop in ITEMS:
                    drop_names.append(ITEMS[drop]["name"])
            if len(drop_names) == 1:
                msg += f" 💎 Находка: {drop_names[0]}!"
            elif len(drop_names) > 1:
                msg += f" 💎 Находки: {', '.join(drop_names)}!"

        today = str(datetime.date.today())  # noqa: DTZ011
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
                    msg += " ✨ Квест выполнен! Введите !награда чтобы забрать бонус!"

        await self.bot.db.save(p)
        await ctx.send(msg)

    @commands.command(name="каст", aliases=["cast"])
    async def cmd_cast_spell(self, ctx, *, spell_key: str = ""):
        spell_key = spell_key.lower().strip()
        if not spell_key:
            await ctx.send(
                f"❌ Укажите заклинание. Доступны: {', '.join(SPELLS.keys())}"
            )
            return

        spell = SPELLS.get(spell_key) or next(
            (s for k, s in SPELLS.items() if spell_key in s["name"].lower()),
            None,
        )
        if not spell:
            await ctx.send(
                f"❌ Нет такого заклинания. Доступны: {', '.join(SPELLS.keys())}"
            )
            return

        p = await self.bot.get_player(ctx.author.name)
        if p.mp < spell["mp_cost"]:
            await ctx.send(
                f"❌ @{p.username}, мало маны! Нужно {spell['mp_cost']} MP (у тебя {p.mp})."
            )
            return

        p.mp -= spell["mp_cost"]
        st = self.bot.engine.get_stats(p)
        s_type = spell.get("type", "attack")

        if s_type == "heal":
            heal_val = spell.get("heal", 250) + int(st["int"] * 1.5)
            max_hp = self.bot.engine.get_max_hp(p)
            p.hp = min(max_hp, p.hp + heal_val)
            await self.bot.db.save(p)
            await ctx.send(
                f"✨ @{p.username} кастует [{spell['name']}] и восстанавливает {heal_val} HP! (❤️ {p.hp}/{max_hp} HP, 🔮 {p.mp}/{self.bot.engine.get_max_mp(p)} MP)"
            )
        elif s_type == "shield":
            shield_val = spell.get("shield", 150) + int(st["int"] * 1.5)
            p.shield += shield_val
            max_hp = self.bot.engine.get_max_hp(p)
            shield_str = f" (+{p.shield} щит)" if p.shield > 0 else ""
            await self.bot.db.save(p)
            await ctx.send(
                f"🛡️ @{p.username} создает Магический щит (+{shield_val} прочности)! (❤️ {p.hp}{shield_str}/{max_hp} HP, 🔮 {p.mp}/{self.bot.engine.get_max_mp(p)} MP)"
            )
        else:
            p.mp += spell["mp_cost"]
            await ctx.send(
                f"❌ @{p.username}, боевые заклинания можно использовать только во время охоты или дуэли."
            )

    @commands.command(name="войти")
    async def cmd_enter_gate(self, ctx):
        if not getattr(self.bot, "active_red_gate", None):
            await ctx.send("❌ Сейчас нет открытых Скрытых / Красных Врат!")
            return
        gate = self.bot.active_red_gate
        uname = ctx.author.name.lower()
        if uname in gate["participants"]:
            await ctx.send(f"🛡️ @{ctx.author.name}, ты уже вошел во врата!")
            return
        p = await self.bot.get_player(uname)
        gate["participants"][uname] = p
        await ctx.send(
            f"⚔️ @{ctx.author.name} вошел в Красные Врата! Участников: {len(gate['participants'])}"
        )

    @commands.command(name="кач")
    async def cmd_upgrade(self, ctx, stat: str = "", count: int = 1):
        p = await self.bot.get_player(ctx.author.name)
        if p.stat_points < count or count <= 0:
            await ctx.send(f"❌ Недостаточно AP. У тебя: {p.stat_points}")
            return

        m = {
            "сила": "str_stat",
            "str": "str_stat",
            "силу": "str_stat",
            "ловкость": "agi",
            "agi": "agi",
            "ловоксть": "agi",
            "ловку": "agi",
            "живучесть": "vit",
            "vit": "vit",
            "хп": "vit",
            "живка": "vit",
            "инт": "int_stat",
            "int": "int_stat",
            "интеллект": "int_stat",
            "ману": "int_stat",
            "восприятие": "sen",
            "sen": "sen",
            "сен": "sen",
            "сенсор": "sen",
        }
        attr = m.get(stat.lower())
        if not attr:
            await ctx.send("❓ Выбери: сила, ловкость, живучесть, инт, восприятие")
            return

        setattr(p, attr, getattr(p, attr) + count)
        p.stat_points -= count
        if attr in ["vit", "int_stat"]:
            p.hp = self.bot.engine.get_max_hp(p)
            p.mp = self.bot.engine.get_max_mp(p)

        await self.bot.db.save(p)
        await ctx.send(f"✅ @{p.username}, характеристика {stat} увеличена на {count}!")
