from twitchio.ext import commands

from src.data import RAID_BOSSES, SPELLS


class RaidCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="рейд")
    async def cmd_raid(self, ctx, action: str = "", arg2: str = "шар"):
        user = ctx.author.name.lower()
        if action == "запустить" and user == "wastle_":
            if arg2 not in RAID_BOSSES:
                return
            boss = RAID_BOSSES[arg2]
            self.bot.active_raid = {
                "id": arg2,
                "hp": boss["hp"],
                "max_hp": boss["hp"],
                "parts": {},
            }
            await ctx.send(
                f"⚠️ КРАСНЫЕ ВРАТА: {boss['name']} призван! Пишите !рейд удар или !рейд каст [скилл]"
            )
            return

        if action in ["удар", "каст"]:
            if not getattr(self.bot, "active_raid", None):
                await ctx.send("❌ Нет активного рейда.")
                return
            p = await self.bot.get_player(user)
            raid = self.bot.active_raid

            is_magic = action == "каст"
            spell = SPELLS.get(arg2.lower()) if is_magic else None
            if is_magic and (not spell or p.mp < spell["mp_cost"]):
                await ctx.send("❌ Ошибка магии (мана или имя)")
                return
            if is_magic:
                p.mp -= spell["mp_cost"]

            s_type = spell.get("type", "attack") if (is_magic and spell) else "attack"
            if is_magic and s_type == "heal":
                heal_val = spell.get("heal", 250) + int(
                    self.bot.engine.get_stats(p)["int"] * 1.5
                )
                max_hp = self.bot.engine.get_max_hp(p)
                p.hp = min(max_hp, p.hp + heal_val)
                await self.bot.db.save(p)
                await ctx.send(
                    f"✨ @{p.username} исцелил себя на {heal_val} HP в рейде!"
                )
                return
            elif is_magic and s_type == "shield":
                shield_val = spell.get("shield", 100) + int(
                    self.bot.engine.get_stats(p)["int"] * 1.0
                )
                p.hp = min(
                    self.bot.engine.get_max_hp(p) + shield_val, p.hp + shield_val
                )
                await self.bot.db.save(p)
                await ctx.send(
                    f"🛡️ @{p.username} наложил Магический щит (+{shield_val}) в рейде!"
                )
                return

            dmg, _is_crit = self.bot.engine.calculate_raid_damage(
                p, len(raid["parts"]) >= 5, is_magic, spell
            )
            raid["hp"] -= dmg
            raid["parts"][p.username] = raid["parts"].get(p.username, 0) + dmg
            p.hp -= self.bot.engine.raid_boss_retaliation(
                p, raid["hp"] / raid["max_hp"]
            )

            if p.hp <= 0:
                self.bot.engine.handle_death(p)
                if p.username in raid["parts"]:
                    del raid["parts"][p.username]
                await self.bot.db.save(p)
                await ctx.send(f"💀 @{p.username} пал в рейде!")
                return

            await self.bot.db.save(p)
            if raid["hp"] <= 0:
                boss_data = RAID_BOSSES[raid["id"]]
                await ctx.send(f"🎊 {boss_data['name']} ПОВЕРЖЕН!")
                self.bot.active_raid = None
            else:
                await ctx.send(
                    f"{'🔮' if is_magic else '⚔️'} @{p.username} нанес {dmg}! Босс: {max(0, raid['hp'])} HP"
                )

    @commands.command(name="атака")
    async def cmd_attack_alias(self, ctx):
        await self.cmd_raid(ctx, action="удар")
