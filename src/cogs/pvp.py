import random

from twitchio.ext import commands


class PvPCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="дуэль")
    async def cmd_duel(self, ctx, target: str):
        t = target.strip("@").lower()
        if t == ctx.author.name.lower():
            await ctx.send(f"❌ @{ctx.author.name}, нельзя вызывать самого себя на дуэль.")
            return
        self.bot.active_duels[t] = ctx.author.name.lower()
        await ctx.send(f"⚔️ @{t}, брошен вызов на дуэль от @{ctx.author.name}! Напиши !принять для начала боя.")

    @commands.command(name="принять")
    async def cmd_accept(self, ctx):
        def_n = ctx.author.name.lower()
        if def_n not in self.bot.active_duels:
            await ctx.send("❌ У тебя нет активных вызовов на дуэль.")
            return
            
        atk_n = self.bot.active_duels.pop(def_n)
        p1 = await self.bot.get_player(atk_n)
        p2 = await self.bot.get_player(def_n)
        if not p1 or not p2:
            await ctx.send("❌ Ошибка при загрузке участников дуэли.")
            return

        # Сбрасываем HP на максимум для честного боя
        p1.hp = self.bot.engine.get_max_hp(p1)
        p2.hp = self.bot.engine.get_max_hp(p2)

        s1 = self.bot.engine.get_stats(p1)
        s2 = self.bot.engine.get_stats(p2)

        rounds_played = 0
        combat_log = []

        for round_num in range(1, 10):
            rounds_played = round_num
            # 1. P1 атака на P2
            dodge2 = max(0.02, (s2["agi"] * 0.005) - (s1["sen"] * 0.004))
            if random.random() < dodge2:
                combat_log.append(f"Р{round_num}: @{p2.username} увернулся от атаки @{p1.username}!")
            else:
                crit1 = random.random() < min(0.35, s1["agi"] * 0.005)
                base1 = s1["str"] * 2.0 + s1["agi"] * 0.3
                red2 = s2["vit"] * 0.6
                dmg1 = max(1, int((base1 * (1.5 if crit1 else 1.0) * random.uniform(0.9, 1.1)) - red2))
                p2.hp -= dmg1
                crit_str = " (КРИТ!)" if crit1 else ""
                combat_log.append(f"Р{round_num}: @{p1.username} нанес {dmg1}{crit_str} урона @{p2.username}")

            if p2.hp <= 0:
                break

            # 2. P2 атака на P1
            dodge1 = max(0.02, (s1["agi"] * 0.005) - (s2["sen"] * 0.004))
            if random.random() < dodge1:
                combat_log.append(f"@{p1.username} увернулся!")
            else:
                crit2 = random.random() < min(0.35, s2["agi"] * 0.005)
                base2 = s2["str"] * 2.0 + s2["agi"] * 0.3
                red1 = s1["vit"] * 0.6
                dmg2 = max(1, int((base2 * (1.5 if crit2 else 1.0) * random.uniform(0.9, 1.1)) - red1))
                p1.hp -= dmg2
                crit_str2 = " (КРИТ!)" if crit2 else ""
                combat_log.append(f"@{p2.username} ответил {dmg2}{crit_str2} урона")

            if p1.hp <= 0:
                break

        # Определение победителя
        winner_p = None
        if p1.hp > 0 and (p2.hp <= 0 or p1.hp > p2.hp):
            winner_p = p1
        elif p2.hp > 0 and (p1.hp <= 0 or p2.hp > p1.hp):
            winner_p = p2

        res = f"⚔️ Дуэль между @{p1.username} и @{p2.username} завершилась за {rounds_played} раунд(ов)! "
        if winner_p:
            winner_p.pvp_wins += 1
            res += f"🏆 Победитель: @{winner_p.username} (осталось {max(0, winner_p.hp)} HP)! "
            ach = self.bot.engine.unlock_achievement(winner_p, "pvp_winner")
            if ach:
                res += f"🏆 Достижение: [{ach['name']}] (+{ach['reward_gold']}💰)!"
        else:
            res += "🤝 Ничья! Оба бойца пали без сил."

        await self.bot.db.save(p1)
        await self.bot.db.save(p2)
        await ctx.send(res)

    @commands.command(name="топ_пвп", aliases=["топпвп"])
    async def cmd_top_pvp(self, ctx):
        top_players = await self.bot.db.get_top_pvp_players(5)
        if not top_players or all(p.pvp_wins == 0 for p in top_players):
            await ctx.send("🏆 Таблица лидеров PvP пока пуста.")
            return

        res = "🏆 ТОП ДУЭЛЯНТОВ (ПВП): "
        lines = []
        for i, p in enumerate(top_players, 1):
            if p.pvp_wins > 0:
                lines.append(f"{i}. @{p.username} ({p.pvp_wins} побед)")
        
        await ctx.send(res + " | ".join(lines))
