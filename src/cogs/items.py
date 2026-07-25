from twitchio.ext import commands
from src.data import ITEMS

class ItemsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="инвентарь")
    async def cmd_inv(self, ctx):
        it = self.bot.db.get_inventory(ctx.author.name)
        if not it:
            await ctx.send(f"🎒 @{ctx.author.name}, инвентарь пуст."); return
        counts = {}
        for tid in it:
            if tid in ITEMS:
                name = ITEMS[tid]["name"]
                counts[name] = counts.get(name, 0) + 1
        disp = [f"{n} (x{c})" if c > 1 else n for n, c in counts.items()]
        await ctx.send(f"🎒 Инвентарь: " + ", ".join(disp))

    @commands.command(name="надеть")
    async def cmd_equip(self, ctx, *, name: str = ""):
        p = self.bot.get_player(ctx.author.name)
        inv = self.bot.db.get_inventory(p.username)
        tid = next((k for k in inv if name.lower() in ITEMS[k]["name"].lower()), None)
        
        if not tid:
            await ctx.send("❌ Предмет не найден."); return
            
        slot = ITEMS[tid].get("slot")
        if slot == "weapon": p.weapon_id = tid
        elif slot == "armor": p.armor_id = tid
        elif slot == "accessory": p.accessory_id = tid
        else:
            await ctx.send("❌ Этот предмет нельзя надеть."); return
            
        self.bot.db.save(p)
        await ctx.send(f"✅ @{p.username} экипировал {ITEMS[tid]['name']} ({slot})")

    @commands.command(name="снять")
    async def cmd_unequip(self, ctx, slot: str = ""):
        p = self.bot.get_player(ctx.author.name)
        s = slot.lower()
        if s in ["оружие", "weapon"]: p.weapon_id = None
        elif s in ["броня", "armor"]: p.armor_id = None
        elif s in ["аксессуар", "сфера", "accessory"]: p.accessory_id = None
        else:
            await ctx.send("❌ Укажите слот: оружие, броня или аксессуар."); return
        self.bot.db.save(p)
        await ctx.send(f"✅ Слот {slot} теперь пуст.")

    @commands.command(name="магазин")
    async def cmd_shop(self, ctx):
        stock = [f"{i['name']} ({i['price']}💰)" for i in ITEMS.values() if i.get("price", 0) > 0]
        await ctx.send("🏪 Магазин: " + " | ".join(stock))

    @commands.command(name="купить")
    async def cmd_buy(self, ctx, *, name: str = ""):
        p = self.bot.get_player(ctx.author.name)
        tid = next((k for k, v in ITEMS.items() if name.lower() in v["name"].lower() and v.get("price", 0) > 0), None)
        if not tid:
            await ctx.send("❌ Товар не найден."); return
        price = ITEMS[tid]["price"]
        if p.gold < price:
            await ctx.send("❌ Недостаточно золота."); return
        p.gold -= price
        self.bot.db.add_to_inventory(p.username, tid)
        self.bot.db.save(p)
        await ctx.send(f"✅ Куплено: {ITEMS[tid]['name']}!")

    @commands.command(name="пить", aliases=["использовать"])
    async def cmd_use(self, ctx, *, name: str = ""):
        p = self.bot.get_player(ctx.author.name)
        inv = self.bot.db.get_inventory(p.username)
        tid = next((k for k in inv if name.lower() in ITEMS[k]["name"].lower() and ITEMS[k]["type"] == "use"), None)
        if not tid:
            await ctx.send("❌ Зелье не найдено."); return
        item = ITEMS[tid]
        if "heal" in item: p.hp = min(self.bot.engine.get_max_hp(p), p.hp + item["heal"])
        if "restore_mp" in item: p.mp = min(self.bot.engine.get_max_mp(p), p.mp + item["restore_mp"])
        self.bot.db.remove_from_inventory(p.username, tid)
        self.bot.db.save(p)
        await ctx.send(f"🧪 @{p.username} использовал {item['name']}!")