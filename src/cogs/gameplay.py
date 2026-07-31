import datetime

from twitchio.ext import commands

from src.data import DUNGEONS, ITEMS, SPELLS


class GameplayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="квест")
    async def cmd_quest(self, ctx):
        p = await self.bot.get_player(ctx.author.name)
        today = str(datetime.date.today())  # noqa: DTZ011
        if p.last_daily == today:
            await ctx.send(f"🚫 @{p.username}, тренировка на сегодня завершена!"); return
        
        p.stat_points += 3
        gold_reward = p.lvl * 50
        p.gold += gold_reward
        p.last_daily = today
        await self.bot.db.save(p)
        await ctx.send(f"🏋️‍♂️ @{p.username} завершил квест! Награда: +3 AP и {gold_reward}💰")

    @commands.command(name="врата")
    async def cmd_gates(self, ctx):
        info = [f"[{i}] {d['name']}" for i, d in DUNGEONS.items()]
        await ctx.send("🚪 Доступные врата: " + " | ".join(info))

    @commands.command(name="переход")
    async def cmd_travel(self, ctx, loc_id: str = ""):
        if loc_id not in DUNGEONS:
            await ctx.send("❌ Неверный ID. Используй !врата"); return
        p = await self.bot.get_player(ctx.author.name)
        p.location_id = loc_id
        await self.bot.db.save(p)
        await ctx.send(f"🚀 @{p.username} вошел в: {DUNGEONS[loc_id]['name']}")

    @commands.command(name="охота")
    async def cmd_hunt(self, ctx, action: str = "", spell_key: str = "шар"):
        p = await self.bot.get_player(ctx.author.name)
        if p.location_id == "0":
            await ctx.send("🏘️ Ты в городе. Используй !переход [ID]"); return
            
        is_magic = action.lower() == "каст"
        spell = SPELLS.get(spell_key.lower()) if is_magic else None
        
        if is_magic:
            if not spell:
                await ctx.send(f"❌ Нет такого заклинания. Доступны: {', '.join(SPELLS.keys())}"); return
            if p.mp < spell["mp_cost"]:
                await ctx.send(f"❌ Мало маны! Нужно {spell['mp_cost']}"); return
            p.mp -= spell["mp_cost"]

        msg, drop = self.bot.engine.fight(p, DUNGEONS[p.location_id], is_magic, spell)
        if drop:
            await self.bot.db.add_to_inventory(p.username, drop)
            msg += f" 💎 Находка: {ITEMS[drop]['name']}!"
            
        await self.bot.db.save(p)
        await ctx.send(msg)

    @commands.command(name="кач")
    async def cmd_upgrade(self, ctx, stat: str = "", count: int = 1):
        p = await self.bot.get_player(ctx.author.name)
        if p.stat_points < count or count <= 0:
            await ctx.send(f"❌ Недостаточно AP. У тебя: {p.stat_points}"); return
        
        m = {
            "сила": "str_stat", "str": "str_stat", "силу": "str_stat",
            "ловкость": "agi", "agi": "agi", "ловоксть": "agi", "ловку": "agi",
            "живучесть": "vit", "vit": "vit", "хп": "vit", "живка": "vit",
            "инт": "int_stat", "int": "int_stat", "интеллект": "int_stat", "ману": "int_stat"
        }
        attr = m.get(stat.lower())
        if not attr:
            await ctx.send("❓ Выбери: сила, ловкость, живучесть, инт"); return
            
        setattr(p, attr, getattr(p, attr) + count)
        p.stat_points -= count
        if attr in ["vit", "int_stat"]:
            p.hp = self.bot.engine.get_max_hp(p)
            p.mp = self.bot.engine.get_max_mp(p)
            
        await self.bot.db.save(p)
        await ctx.send(f"✅ Характеристика {stat} увеличена на {count}!")
