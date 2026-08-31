from twitchio.ext import commands

from src.data import ACHIEVEMENTS, ITEMS, SPELLS, TITLES


class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="команды")
    async def cmd_help(self, ctx):
        await ctx.send(
            "📜 Доступные команды: !профиль !статы !кач !квест !награда !охота !отдых !войти !крафты !крафт !заклинания !достижения !титулы !титул !инвентарь !надеть !снять !пить !магазин !купить !продать !передать !пати !врата !переход !дуэль !принять !отклонить !рейд !атака !топ !топ_золото !гит"
        )

    @commands.command(name="помощь")
    async def cmd_help_alias(self, ctx):
        await self.cmd_help(ctx)

    @commands.command(name="гит")
    async def cmd_git(self, ctx):
        await ctx.send(
            "📂 Исходный код Kwasik Bot (Solo Leveling RPG): https://github.com/WastleQ/kwasik-bot/tree/main"
        )

    @commands.command(name="git")
    async def cmd_git_alias(self, ctx):
        await self.cmd_git(ctx)

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
            active_mark = " (Активен)" if p.title == key else ""
            if is_unlocked:
                lines.append(f"{t['name']}{active_mark}: 🔓 Доступен")
            else:
                lines.append(f"{t['name']}{active_mark}")

        await ctx.send("👑 Титулы: " + " | ".join(lines))

    @commands.command(name="титул")
    async def cmd_set_title(self, ctx, *, title_input: str = ""):
        title_input = title_input.strip()
        if not title_input:
            await ctx.send("❌ Укажите название титула. Посмотрите !титулы")
            return

        norm_input = (
            title_input.lower().replace(" ", "").replace("-", "").replace("_", "")
        )

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
            await ctx.send("❌ Такой титул не найден. Посмотрите !титулы")
            return

        p = await self.bot.get_player(ctx.author.name)
        t_data = TITLES[matched_key]
        req = t_data.get("req")
        unlocked_ach = [a.strip() for a in p.achievements.split(",") if a.strip()]

        if req is not None and req not in unlocked_ach:
            await ctx.send(
                f"❌ Этот титул заблокирован! Требуется достижение: {ACHIEVEMENTS.get(req, {}).get('name', req)}"
            )
            return

        p.title = matched_key
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
            if s.get("type") == "attack":
                info = f"{s['name']} [{key}]: {s['mp_cost']}MP (x{s['damage_mult']})"
            elif s.get("type") == "heal":
                info = f"{s['name']} [{key}]: {s['mp_cost']}MP (+{s['heal']} HP)"
            elif s.get("type") == "shield":
                info = f"{s['name']} [{key}]: {s['mp_cost']}MP (+{s['shield']} Щит)"
            else:
                info = f"{s['name']} [{key}]: {s['mp_cost']}MP"
            spells_info.append(info)

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

    @commands.command(name="топ_золото")
    async def cmd_top_gold(self, ctx):
        top_players = await self.bot.db.get_top_gold_players(5)
        if not top_players:
            await ctx.send("💰 Таблица богачей пока пуста.")
            return

        res = "💰 ТОП БОГАЧЕЙ: "
        lines = []
        for i, p in enumerate(top_players, 1):
            lines.append(f"{i}. @{p.username} ({p.gold} 💰)")

        await ctx.send(res + " | ".join(lines))
