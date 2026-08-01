import random

from twitchio.ext import commands

from src.data import SPELLS


class PvPCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="дуэль")
    async def cmd_duel(self, ctx, target: str):
        t = target.strip("@").lower()
        if t == ctx.author.name.lower():
            await ctx.send(
                f"❌ @{ctx.author.name}, нельзя вызывать самого себя на дуэль."
            )
            return
        self.bot.active_duels[t] = ctx.author.name.lower()
        await ctx.send(
            f"⚔️ @{t}, брошен вызов на дуэль от @{ctx.author.name}! Напиши !принять для начала пошагового боя."
        )

    @commands.command(name="отклонить")
    async def cmd_decline(self, ctx):
        def_n = ctx.author.name.lower()
        if def_n not in self.bot.active_duels:
            await ctx.send("❌ У тебя нет активных вызовов на дуэль для отклонения.")
            return
        atk_n = self.bot.active_duels.pop(def_n)
        await ctx.send(f"🛡️ @{ctx.author.name} отклонил вызов на дуэль от @{atk_n}.")

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

        p1.hp = self.bot.engine.get_max_hp(p1)
        p2.hp = self.bot.engine.get_max_hp(p2)
        p1.mp = self.bot.engine.get_max_mp(p1)
        p2.mp = self.bot.engine.get_max_mp(p2)

        match_id = f"{atk_n}_vs_{def_n}"
        match_data = {
            "p1": atk_n,
            "p2": def_n,
            "round": 1,
            "p1_action": None,
            "p2_action": None,
            "p1_shield": 0,
            "p2_shield": 0,
        }
        self.bot.active_pvp_matches[match_id] = match_data
        self.bot.user_active_pvp[atk_n] = match_id
        self.bot.user_active_pvp[def_n] = match_id

        await ctx.send(
            f"⚔️ ПОШАГОВАЯ ДУЭЛЬ НАЧАЛАСЬ: @{p1.username} vs @{p2.username}!\n"
            f"🎯 Раунд 1. Введите действие в чат:\n"
            f"• !бой удар (физическая атака)\n"
            f"• !бой каст <шар/молния/метеор/хил/щит> (магия)"
        )

    @commands.command(name="бой")
    async def cmd_combat_action(self, ctx, action: str = "", arg: str = ""):
        uname = ctx.author.name.lower()
        match_id = self.bot.user_active_pvp.get(uname)
        if not match_id or match_id not in self.bot.active_pvp_matches:
            await ctx.send(f"❌ @{ctx.author.name}, вы не участвуете в активной дуэли.")
            return

        match = self.bot.active_pvp_matches[match_id]
        is_p1 = uname == match["p1"]

        action = action.lower()
        act_data = None

        if action == "удар":
            act_data = {"type": "physical"}
        elif action == "каст":
            spell_key = arg.lower()
            spell = SPELLS.get(spell_key)
            if not spell:
                await ctx.send(
                    f"❌ Нет такого заклинания. Доступны: {', '.join(SPELLS.keys())}"
                )
                return
            p = await self.bot.get_player(uname)
            if p.mp < spell["mp_cost"]:
                await ctx.send(
                    f"❌ Мало маны! Нужно {spell['mp_cost']} MP (у вас {p.mp} MP)"
                )
                return
            act_data = {"type": "magic", "spell": spell, "key": spell_key}
        else:
            await ctx.send(
                "❓ Неверное действие. Используйте: !бой удар ИЛИ !бой каст [скилл]"
            )
            return

        if is_p1:
            match["p1_action"] = act_data
        else:
            match["p2_action"] = act_data

        await ctx.send(f"🛡️ @{ctx.author.name} записал свое действие на этот раунд!")

        if match["p1_action"] and match["p2_action"]:
            await self._resolve_round(ctx, match_id)

    async def _resolve_round(self, ctx, match_id):
        match = self.bot.active_pvp_matches[match_id]
        p1 = await self.bot.get_player(match["p1"])
        p2 = await self.bot.get_player(match["p2"])
        s1 = self.bot.engine.get_stats(p1)
        s2 = self.bot.engine.get_stats(p2)

        log = [f"⚔️ --- РАУНД {match['round']} ---"]

        p1_shield = match["p1_shield"]
        p2_shield = match["p2_shield"]

        act1 = match["p1_action"]
        act2 = match["p2_action"]

        async def execute_action(attacker, defender, act, is_p1):
            nonlocal p1_shield, p2_shield
            ast = s1 if is_p1 else s2
            dst = s2 if is_p1 else s1

            if act["type"] == "physical":
                dodge = max(0.02, (dst["agi"] * 0.005) - (ast["sen"] * 0.004))
                if random.random() < dodge:
                    log.append(
                        f"@{defender.username} увернулся от удара @{attacker.username}!"
                    )
                else:
                    crit = random.random() < min(0.35, ast["agi"] * 0.005)
                    base = ast["str"] * 2.0 + ast["agi"] * 0.3
                    red = dst["vit"] * 0.6
                    dmg = max(
                        1,
                        int(
                            (base * (1.5 if crit else 1.0) * random.uniform(0.9, 1.1))
                            - red
                        ),
                    )

                    target_shield = p2_shield if is_p1 else p1_shield
                    if target_shield > 0:
                        if dmg >= target_shield:
                            dmg -= target_shield
                            if is_p1:
                                p2_shield = 0
                            else:
                                p1_shield = 0
                            defender.hp -= dmg
                        else:
                            if is_p1:
                                p2_shield -= dmg
                            else:
                                p1_shield -= dmg
                            dmg = 0
                    else:
                        defender.hp -= dmg

                    crit_str = " (КРИТ!)" if crit else ""
                    log.append(
                        f"@{attacker.username} ударил @{defender.username} на {dmg}{crit_str} урона"
                    )

            elif act["type"] == "magic":
                spell = act["spell"]
                attacker.mp -= spell["mp_cost"]
                stype = spell.get("type", "attack")

                if stype == "heal":
                    heal_val = spell.get("heal", 250) + int(ast["int"] * 1.5)
                    max_h = self.bot.engine.get_max_hp(attacker)
                    attacker.hp = min(max_h, attacker.hp + heal_val)
                    log.append(
                        f"✨ @{attacker.username} скастовал [{spell['name']}] и восстановил {heal_val} HP!"
                    )
                elif stype == "shield":
                    shield_val = spell.get("shield", 100) + int(ast["int"] * 1.0)
                    if is_p1:
                        nonlocal match
                        match["p1_shield"] += shield_val
                        p1_shield = match["p1_shield"]
                    else:
                        match["p2_shield"] += shield_val
                        p2_shield = match["p2_shield"]
                    log.append(
                        f"🛡️ @{attacker.username} создал Магический щит (+{shield_val})!"
                    )
                else:
                    m_mult = 2.0 if attacker.accessory_id == "orb_of_avarice" else 1.0
                    base = ast["int"] * spell["damage_mult"] * m_mult
                    crit = random.random() < min(0.3, ast["sen"] * 0.005)
                    dmg = max(1, int(base * (1.5 if crit else 1.0)))

                    target_shield = p2_shield if is_p1 else p1_shield
                    if target_shield > 0:
                        if dmg >= target_shield:
                            dmg -= target_shield
                            if is_p1:
                                p2_shield = 0
                            else:
                                p1_shield = 0
                            defender.hp -= dmg
                        else:
                            if is_p1:
                                p2_shield -= dmg
                            else:
                                p1_shield -= dmg
                            dmg = 0
                    else:
                        defender.hp -= dmg

                    crit_str = " 🔥 (МАГИЧЕСКИЙ КРИТ!)" if crit else ""
                    log.append(
                        f"🔮 @{attacker.username} обрушил [{spell['name']}] на @{defender.username} за {dmg}{crit_str} урона"
                    )

        init1 = (s1["agi"] * 1.0) + (s1["sen"] * 0.8) + random.randint(0, 5)
        init2 = (s2["agi"] * 1.0) + (s2["sen"] * 0.8) + random.randint(0, 5)

        if init1 >= init2:
            await execute_action(p1, p2, act1, True)
            if p2.hp > 0:
                await execute_action(p2, p1, act2, False)
        else:
            await execute_action(p2, p1, act2, False)
            if p1.hp > 0:
                await execute_action(p1, p2, act1, True)

        match["p1_shield"] = p1_shield
        match["p2_shield"] = p2_shield

        max_hp1 = self.bot.engine.get_max_hp(p1)
        max_hp2 = self.bot.engine.get_max_hp(p2)

        winner_p = None
        if p1.hp <= 0 and p2.hp <= 0:
            winner_p = None
        elif p1.hp <= 0:
            winner_p = p2
        elif p2.hp <= 0:
            winner_p = p1
        elif match["round"] >= 10:
            if p1.hp > p2.hp:
                winner_p = p1
            elif p2.hp > p1.hp:
                winner_p = p2

        if winner_p or match["round"] >= 10:
            del self.bot.active_pvp_matches[match_id]
            self.bot.user_active_pvp.pop(match["p1"], None)
            self.bot.user_active_pvp.pop(match["p2"], None)

            if winner_p:
                winner_p.pvp_wins += 1
                ach = self.bot.engine.unlock_achievement(winner_p, "pvp_winner")
                ach_text = (
                    f" 🏆 [{ach['name']}] (+{ach['reward_gold']}💰)" if ach else ""
                )
                res = f" | 👑 ПОБЕДИТЕЛЬ: @{winner_p.username}!{ach_text}"
            else:
                res = " | 🤝 НИЧЬЯ!"

            await self.bot.db.save(p1)
            await self.bot.db.save(p2)

            summary = " ".join(log) + f"\n🏁 ДУЭЛЬ ОКОНЧЕНА!{res}"
            await ctx.send(summary)
        else:
            match["round"] += 1
            match["p1_action"] = None
            match["p2_action"] = None
            await self.bot.db.save(p1)
            await self.bot.db.save(p2)

            summary = (
                " ".join(log)
                + f"\n📊 HP: @{p1.username} ({max(0, p1.hp)}/{max_hp1} HP) | @{p2.username} ({max(0, p2.hp)}/{max_hp2} HP)\n"
                f"🎯 Раунд {match['round']}. Введите ход: !бой удар ИЛИ !бой каст [скилл]"
            )
            await ctx.send(summary)

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
