import asyncio
import importlib
import os
import random

from dotenv import load_dotenv
from twitchio.ext import commands, routines

from src.data import ITEMS, RAID_BOSSES
from src.engine import RPGEngine
from src.models import DBManager, Player

load_dotenv()
TOKEN = os.getenv("TWITCH_TOKEN")
CHANNEL = "kwasik67"
ADMINS = ["wastle_", "akseniyy", "kwasik67"]


class SoloLevelingBot(commands.Bot):
    def __init__(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        super().__init__(
            token=TOKEN, prefix="!", initial_channels=[CHANNEL], loop=self._loop
        )

        self.db = DBManager()
        self.engine = RPGEngine()
        self.active_duels = {}
        self.active_raid = None
        self.active_red_gate = None
        self.active_pvp_matches = {}
        self.user_active_pvp = {}
        self.parties = {}
        self.party_invites = {}
        self.player_party = {}

        self.load_extensions()

        self.raid_aoe_task = routines.routine(minutes=5)(self._raid_aoe_logic)
        self.regen_task = routines.routine(minutes=3)(self._passive_regen_logic)
        self.red_gate_task = routines.routine(minutes=45)(self._red_gate_spawn_logic)

    def load_extensions(self):
        cogs_dir = os.path.join("src", "cogs")
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module = importlib.import_module(f"src.cogs.{filename[:-3]}")
                for name in dir(module):
                    obj = getattr(module, name)
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, commands.Cog)
                        and obj is not commands.Cog
                    ):
                        self.add_cog(obj(self))

    async def event_ready(self):
        await self.db.init_db()
        print(f"🔥 Охотник {self.nick} в сети!")
        self.raid_aoe_task.start()
        self.regen_task.start()
        self.red_gate_task.start()

    @commands.command(name="врата_спавн")
    async def admin_spawn_red_gate(self, ctx):
        if ctx.author.name.lower() in ADMINS:
            await self._spawn_red_gate()
            await ctx.send("🚨 Красные Врата принудительно открыты!")

    async def _red_gate_spawn_logic(self):
        if random.random() < 0.5:
            await self._spawn_red_gate()

    async def _spawn_red_gate(self):
        channel = self.get_channel(CHANNEL)
        if not channel:
            return
        self.active_red_gate = {
            "hp": 100000,
            "max_hp": 100000,
            "participants": {},
        }
        await channel.send(
            "🚨 КРАСНЫЕ ВРАТА S-РАНГА ОТКРЫЛИСЬ! У вас есть 3 минуты, чтобы войти командой: !войти"
        )
        await asyncio.sleep(180)
        if not self.active_red_gate:
            return

        gate = self.active_red_gate
        self.active_red_gate = None

        participants = gate["participants"]
        if not participants:
            await channel.send(
                "💀 Красные Врата закрылись, так как ни один охотник не осмелился войти..."
            )
            return

        total_damage = 0
        for p in participants.values():
            st = self.engine.get_stats(p)
            dmg = int(st["str"] * 3.0 + st["int"] * 2.5 + p.lvl * 50)
            total_damage += dmg

        if total_damage >= 100000:
            reward_gold = 2000
            crystals = ["crystal_a", "crystal_s"]
            rewards_msg = f"🎊 Красные Врата зачищены! Совместный урон: {total_damage}/100000. Награды участникам: {reward_gold}💰 и редкие кристаллы (A/S)!"
            for p in participants.values():
                p.gold += reward_gold
                c_drop = random.choice(crystals)
                await self.db.add_to_inventory(p.username, c_drop)
                p.exp += 1500
                self.engine.check_level_up(p)
                await self.db.save(p)
            await channel.send(rewards_msg)
        else:
            for p in participants.values():
                p.hp = max(1, p.hp // 2)
                await self.db.save(p)
            await channel.send(
                f"💀 Охотники проиграли битву в Красных Вратах (урон: {total_damage}/100000)! Босс сокрушил отряд."
            )

    async def event_message(self, message):
        if not message.echo:
            try:
                await self.handle_commands(message)
            except Exception:  # noqa: S110, BLE001
                pass

    async def event_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound) or (
            isinstance(error, TypeError) and "CommandNotFound" in str(error)
        ):
            return
        print(f"⚠️ Ошибка: {error}")

    async def get_player(self, username: str):
        username = username.lower().replace("@", "")
        p = await self.db.load(username)
        if not p:
            p = Player(username=username)
            await self.db.save(p)
        return p

    @commands.command(name="админ_вещи")
    async def admin_give_all(self, ctx):
        if ctx.author.name.lower() in ADMINS:
            p = await self.get_player(ctx.author.name)
            for tid in ITEMS:
                await self.db.add_to_inventory(p.username, tid)
            await ctx.send("🎁 Склад открыт!")

    async def _passive_regen_logic(self):
        players = await self.db.get_all_players()
        for p in players:
            changed = False
            max_hp = self.engine.get_max_hp(p)
            if p.hp < max_hp:
                p.hp = min(
                    max_hp, p.hp + 1 + int(self.engine.get_stats(p)["vit"] * 0.1)
                )
                changed = True
            max_mp = self.engine.get_max_mp(p)
            if p.mp < max_mp:
                p.mp = min(
                    max_mp, p.mp + 2 + int(self.engine.get_stats(p)["int"] * 0.15)
                )
                changed = True
            if changed:
                await self.db.save(p)

    async def _raid_aoe_logic(self):
        if self.active_raid:
            damage = RAID_BOSSES[self.active_raid["id"]].get("aoe_dmg", 10)
            for uname in list(self.active_raid["parts"].keys()):
                p = await self.get_player(uname)
                p.hp -= damage
                if p.hp <= 0:
                    self.engine.handle_death(p)
                    if p.username in self.active_raid["parts"]:
                        del self.active_raid["parts"][p.username]
                await self.db.save(p)


if __name__ == "__main__":
    SoloLevelingBot().run()
