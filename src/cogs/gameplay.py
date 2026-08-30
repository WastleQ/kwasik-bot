import datetime

from twitchio.ext import commands

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

        lvl_up_msg = ""
        while p.exp >= p.lvl * 100:
            p.exp -= p.lvl * 100
            p.lvl += 1
            p.stat_points += 5
            p.hp = self.bot.engine.get_max_hp(p)
            p.mp = self.bot.engine.get_max_mp(p)
            lvl_up_msg = f" 🎉 УРОВЕНЬ ПОВЫШЕН ДО {p.lvl}!"

        await self.bot.db.save(p)
        await ctx.send(
            f"🎁 @{p.username} выполнил ежедневный квест Системы! Награда: +3 AP, +50 EXP, {gold_reward}💰, полное восстановление сил!{lvl_up_msg}"
        )

    @commands.command(name="отдых")
    async def cmd_rest(self, ctx):
        p = await self.bot.get_player(ctx.author.name)
        max_hp = self.bot.engine.get_max_hp(p)
        max_mp = self.bot.engine.get_max_mp(p)
        if p.hp >= max_hp and p.mp >= max_mp:
            await ctx.send(f"🏕️ @{p.username}, ты и так полностью полон сил!")
            return
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
        }
        attr = m.get(stat.lower())
        if not attr:
            await ctx.send("❓ Выбери: сила, ловкость, живучесть, инт")
            return

        setattr(p, attr, getattr(p, attr) + count)
        p.stat_points -= count
        if attr in ["vit", "int_stat"]:
            p.hp = self.bot.engine.get_max_hp(p)
            p.mp = self.bot.engine.get_max_mp(p)

        await self.bot.db.save(p)
        await ctx.send(f"✅ Характеристика {stat} увеличена на {count}!")
