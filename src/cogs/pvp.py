import random

from twitchio.ext import commands


class PvPCog(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command(name="дуэль")
    async def cmd_duel(self, ctx, target: str):
        t = target.strip("@").lower()
        if t == ctx.author.name.lower(): return
        self.bot.active_duels[t] = ctx.author.name.lower()
        await ctx.send(f"⚔️ @{t}, вызов от @{ctx.author.name}! !принять")

    @commands.command(name="принять")
    async def cmd_accept(self, ctx):
        def_n = ctx.author.name.lower()
        if def_n not in self.bot.active_duels:
            await ctx.send("❌ У тебя нет активных вызовов."); return
            
        atk_n = self.bot.active_duels.pop(def_n)
        p1 = await self.bot.get_player(atk_n)
        p2 = await self.bot.get_player(def_n)
        s1, s2 = self.bot.engine.get_stats(p1), self.bot.engine.get_stats(p2)
        
        # Формула атаки и защиты
        atk_power1 = s1["str"] * 2 + s1["agi"]
        atk_power2 = s2["str"] * 2 + s2["agi"]
        
        def_power1 = s1["vit"] * 1.2
        def_power2 = s2["vit"] * 1.2
        
        dmg_to_p2 = max(5, int((atk_power1 * random.uniform(0.9, 1.1)) - def_power2))
        dmg_to_p1 = max(5, int((atk_power2 * random.uniform(0.9, 1.1)) - def_power1))
        
        p1.hp -= dmg_to_p1
        p2.hp -= dmg_to_p2
        
        res = f"⚔️ Дуэль: @{atk_n} нанес {dmg_to_p2} урона, а @{def_n} нанес {dmg_to_p1} урона. "
        
        winner_p = None
        if p2.hp <= 0 and p1.hp > 0:
            winner_p = p1
            res += f"🏆 @{atk_n} победил!"
        elif p1.hp <= 0 and p2.hp > 0:
            winner_p = p2
            res += f"🏆 @{def_n} победил!"
        elif p1.hp <= 0 and p2.hp <= 0:
            res += "Ничья! Оба упали без сил."
        else:
            winner_name = atk_n if p1.hp > p2.hp else def_n
            winner_p = p1 if p1.hp > p2.hp else p2
            res += f"По очкам здоровья лидирует @{winner_name}!"

        if winner_p:
            ach = self.bot.engine.unlock_achievement(winner_p, "pvp_winner")
            if ach:
                res += f" 🏆 Достижение: [{ach['name']}] (+{ach['reward_gold']}💰)!"

        await self.bot.db.save(p1)
        await self.bot.db.save(p2)
        await ctx.send(res)
