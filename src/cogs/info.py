from twitchio.ext import commands
from src.data import SPELLS  # Импортируем справочник заклинаний

class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="команды")
    async def cmd_help(self, ctx):
        # Добавил !заклинания в список
        await ctx.send("📜 Доступные команды: !статы !кач !квест !охота !заклинания !инвентарь !надеть !снять !пить !магазин !купить !врата !переход !дуэль !принять !рейд !топ")

    @commands.command(name="статы")
    async def cmd_stats(self, ctx):
        p = self.bot.get_player(ctx.author.name)
        st = self.bot.engine.get_stats(p)
        rank = self.bot.engine.get_rank(p.lvl)
        await ctx.send(f"@{p.username} [{rank}] | HP: {p.hp}/{self.bot.engine.get_max_hp(p)} | MP: {p.mp}/{self.bot.engine.get_max_mp(p)} | {p.gold} 💰 | AP: {p.stat_points} | STR {st['str']} AGI {st['agi']} VIT {st['vit']} INT {st['int']}")

    @commands.command(name="заклинания")
    async def cmd_spells(self, ctx):
        """Выводит список всех доступных магических способностей."""
        if not SPELLS:
            await ctx.send("🔮 Список заклинаний пуст."); return
        
        msg = "🔮 Доступные заклинания: "
        spells_info = []
        for key, s in SPELLS.items():
            # Показываем название, ключ для ввода, стоимость и множитель
            spells_info.append(f"{s['name']} [{key}]: {s['mp_cost']}MP (x{s['damage_mult']})")
        
        msg += " | ".join(spells_info)
        msg += " — Используй: !охота каст [ключ]"
        await ctx.send(msg)

    @commands.command(name="топ")
    async def cmd_top(self, ctx):
        top_players = self.bot.db.get_top_players(5)
        if not top_players:
            await ctx.send("🏆 Таблица лидеров пока пуста.")
            return

        res = "🏆 ТОП ОХОТНИКОВ: "
        lines = []
        for i, p in enumerate(top_players, 1):
            rank = self.bot.engine.get_rank(p.lvl)
            lines.append(f"{i}. @{p.username} (ур. {p.lvl}, [{rank}])")
        
        await ctx.send(res + " | ".join(lines))