import os
import asyncio
import importlib
from dotenv import load_dotenv
from twitchio.ext import commands, routines
from src.models import DBManager, Player
from src.engine import RPGEngine
from src.data import RAID_BOSSES, ITEMS

import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TWITCH_TOKEN")
CHANNEL = "akseniyy"
ADMINS = ["wastle_", "akseniyy"]

class SoloLevelingBot(commands.Bot):
    def __init__(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        super().__init__(token=TOKEN, prefix="!", initial_channels=[CHANNEL], loop=self._loop)
        
        self.db = DBManager()
        self.engine = RPGEngine()
        self.active_duels = {}
        self.active_raid = None

        self.load_extensions()

        self.raid_aoe_task = routines.routine(minutes=5)(self._raid_aoe_logic)
        self.regen_task = routines.routine(minutes=3)(self._passive_regen_logic)

    def load_extensions(self):
        cogs_dir = os.path.join("src", "cogs")
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module = importlib.import_module(f"src.cogs.{filename[:-3]}")
                for name in dir(module):
                    obj = getattr(module, name)
                    if isinstance(obj, type) and issubclass(obj, commands.Cog) and obj is not commands.Cog:
                        self.add_cog(obj(self))

    async def event_ready(self):
        print(f"🔥 Охотник {self.nick} в сети!")
        self.raid_aoe_task.start()
        self.regen_task.start()

    async def event_message(self, message):
        if not message.echo: await self.handle_commands(message)

    async def event_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound) or (isinstance(error, TypeError) and "CommandNotFound" in str(error)):
            return
        print(f"⚠️ Ошибка: {error}")

    def get_player(self, username: str):
        username = username.lower().replace("@", "")
        p = self.db.load(username)
        if not p: p = Player(username=username); self.db.save(p)
        return p

    @commands.command(name="админ_вещи")
    async def admin_give_all(self, ctx):
        if ctx.author.name.lower() in ADMINS:
            p = self.get_player(ctx.author.name)
            for tid in ITEMS: self.db.add_to_inventory(p.username, tid)
            await ctx.send("🎁 Склад открыт!")

    async def _passive_regen_logic(self):
        for p in self.db.get_all_players():
            max_hp = self.engine.get_max_hp(p)
            if p.hp < max_hp:
                p.hp = min(max_hp, p.hp + 1 + int(self.engine.get_stats(p)['vit'] * 0.1))
                self.db.save(p)

    async def _raid_aoe_logic(self):
        if self.active_raid:
            damage = RAID_BOSSES[self.active_raid["id"]].get("aoe_dmg", 10)
            for uname in list(self.active_raid["parts"].keys()):
                p = self.get_player(uname); p.hp -= damage
                if p.hp <= 0: 
                    self.engine.handle_death(p)
                    del self.active_raid["parts"][p.username]
                self.db.save(p)

if __name__ == "__main__":
    SoloLevelingBot().run()
