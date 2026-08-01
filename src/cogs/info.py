from twitchio.ext import commands

from src.data import ACHIEVEMENTS, ITEMS, SPELLS, TITLES


class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="команды")
    async def cmd_help(self, ctx):
        await ctx.send(
            "📜 Доступные команды: !профиль !статы !кач !квест !охота !отдых !заклинания !достижения !титулы !титул !инвентарь !надеть !снять !пить !магазин !купить !продать !передать !пати !врата !переход !дуэль !принять !отклонить !рейд !атака !топ"
        )

    @commands.command(name="помощь")
    async def cmd_help_alias(self, ctx):
        await self.cmd_help(ctx)

    @commands.command(name="статы")
    async def cmd_stats(self, ctx):
        p = await self.bot.get_player(ctx.author.name)
        st = self.bot.engine.get_stats(p)
        rank = self.bot.engine.get_rank(p.lvl)
        title_name = TITLES.get(p.title, {}).get("name", "Новичок")
        w_name = (
            ITEMS[p.weapon_id]["name"]
            if p.weapon_id and p.weapon_id in ITEMS
            else "Пусто"
        )
        a_name = (
            ITEMS[p.armor_id]["name"] if p.armor_id and p.armor_id in ITEMS else "Пусто"
        )
        acc_name = (
            ITEMS[p.accessory_id]["name"]
            if p.accessory_id and p.accessory_id in ITEMS
            else "Пусто"
        )
        await ctx.send(
            f"@{p.username} [{rank}] | Ур. {p.lvl} | Титул: {title_name} | HP: {p.hp}/{self.bot.engine.get_max_hp(p)} | MP: {p.mp}/{self.bot.engine.get_max_mp(p)} | {p.gold} 💰 | AP: {p.stat_points}\n"
            f"⚔️ Оружие: {w_name} | 🛡️ Броня: {a_name} | 💍 Аксессуар: {acc_name}\n"
            f"📊 Характеристики: STR {st['str']} AGI {st['agi']} VIT {st['vit']} INT {st['int']} SEN {st['sen']}"
        )

    @commands.command(name="профиль")
    async def cmd_profile_alias(self, ctx):
        await self.cmd_stats(ctx)

    @commands.command(name="достижения")
    async def cmd_achievements(self, ctx):
        p = await self.bot.get_player(ctx.author.name)
        unlocked = [a.strip() for a in p.achievements.split(",") if a.strip()]
        if not unlocked:
            await ctx.send(
                f"🏆 @{p.username}, у тебя пока нет разблокированных достижений."
            )
            return

        ach_names = [ACHIEVEMENTS[a]["name"] for a in unlocked if a in ACHIEVEMENTS]
        await ctx.send(f"🏆 Достижения @{p.username}: " + ", ".join(ach_names))

    @commands.command(name="титулы")
    async def cmd_titles(self, ctx):
        p = await self.bot.get_player(ctx.author.name)
        unlocked_ach = [a.strip() for a in p.achievements.split(",") if a.strip()]

        lines = []
        for key, t in TITLES.items():
            req = t.get("req")
            is_unlocked = req is None or req in unlocked_ach
            status = (
                "🔓 Доступен"
                if is_unlocked
                else f"🔒 Требуется: {ACHIEVEMENTS.get(req, {}).get('name', req)}"
            )
            active_mark = " (Активен)" if p.title == key else ""
            lines.append(f"{t['name']} [{key}]{active_mark}: {status}")

        await ctx.send("👑 Доступные титулы: " + " | ".join(lines))

    @commands.command(name="титул")
    async def cmd_set_title(self, ctx, title_key: str = ""):
        title_key = title_key.lower().strip()
        if not title_key or title_key not in TITLES:
            await ctx.send("❌ Укажите корректный ключ титула. Посмотрите !титулы")
            return

        p = await self.bot.get_player(ctx.author.name)
        t_data = TITLES[title_key]
        req = t_data.get("req")
        unlocked_ach = [a.strip() for a in p.achievements.split(",") if a.strip()]

        if req is not None and req not in unlocked_ach:
            await ctx.send(
                f"❌ Этот титул заблокирован! Требуется достижение: {ACHIEVEMENTS.get(req, {}).get('name', req)}"
            )
            return

        p.title = title_key
        await self.bot.db.save(p)
        await ctx.send(f"👑 @{p.username} сменил титул на: {t_data['name']}!")

    @commands.command(name="заклинания")
    async def cmd_spells(self, ctx):
        """Выводит список всех доступных магических способностей."""
        if not SPELLS:
            await ctx.send("🔮 Список заклинаний пуст.")
            return

        msg = "🔮 Доступные заклинания: "
        spells_info = []
        for key, s in SPELLS.items():
            spells_info.append(
                f"{s['name']} [{key}]: {s['mp_cost']}MP (x{s['damage_mult']})"
            )

        msg += " | ".join(spells_info)
        msg += " — Используй: !охота каст [ключ]"
        await ctx.send(msg)

    @commands.command(name="топ")
    async def cmd_top(self, ctx):
        top_players = await self.bot.db.get_top_players(5)
        if not top_players:
            await ctx.send("🏆 Таблица лидеров пока пуста.")
            return

        res = "🏆 ТОП ОХОТНИКОВ: "
        lines = []
        for i, p in enumerate(top_players, 1):
            rank = self.bot.engine.get_rank(p.lvl)
            lines.append(f"{i}. @{p.username} (ур. {p.lvl}, [{rank}])")

        await ctx.send(res + " | ".join(lines))
