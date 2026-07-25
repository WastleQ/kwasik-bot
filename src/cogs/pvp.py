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
        p1, p2 = self.bot.get_player(atk_n), self.bot.get_player(def_n)
        s1, s2 = self.bot.engine.get_stats(p1), self.bot.engine.get_stats(p2)
        
        # Формула атаки и защиты
        # Атака: STR и немного AGI
        atk_power1 = s1["str"] * 2 + s1["agi"]
        atk_power2 = s2["str"] * 2 + s2["agi"]
        
        # Защита: VIT дает прямой вычет урона
        def_power1 = s1["vit"] * 1.2
        def_power2 = s2["vit"] * 1.2
        
        # Чистый урон (минимум 5, чтобы бой не был бесконечным)
        dmg_to_p2 = max(5, int((atk_power1 * random.uniform(0.9, 1.1)) - def_power2))
        dmg_to_p1 = max(5, int((atk_power2 * random.uniform(0.9, 1.1)) - def_power1))
        
        p1.hp -= dmg_to_p1
        p2.hp -= dmg_to_p2
        
        self.bot.db.save(p1)
        self.bot.db.save(p2)
        
        res = f"⚔️ Дуэль: @{atk_n} нанес {dmg_to_p2} урона, а @{def_n} нанес {dmg_to_p1} урона. "
        
        if p1.hp <= 0 and p2.hp <= 0:
            res += "Ничья! Оба упали без сил."
        elif p2.hp <= 0:
            res += f"🏆 @{atk_n} победил!"
        elif p1.hp <= 0:
            res += f"🏆 @{def_n} победил!"
        else:
            winner = atk_n if p1.hp > p2.hp else def_n
            res += f"По очкам здоровья лидирует @{winner}!"
            
        await ctx.send(res)