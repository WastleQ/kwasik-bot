from twitchio.ext import commands

from src.data import CRAFTING_RECIPES, ITEMS


class ItemsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="инвентарь")
    async def cmd_inv(self, ctx):
        it = await self.bot.db.get_inventory(ctx.author.name)
        if not it:
            await ctx.send(f"🎒 @{ctx.author.name}, инвентарь пуст.")
            return
        counts = {}
        for tid in it:
            if tid in ITEMS:
                name = ITEMS[tid]["name"]
                counts[name] = counts.get(name, 0) + 1
        disp = [f"{n} (x{c})" if c > 1 else n for n, c in counts.items()]
        await ctx.send("🎒 Инвентарь: " + ", ".join(disp))

    @commands.command(name="надеть")
    async def cmd_equip(self, ctx, *, name: str = ""):
        p = await self.bot.get_player(ctx.author.name)
        inv = await self.bot.db.get_inventory(p.username)
        tid = next((k for k in inv if name.lower() in ITEMS[k]["name"].lower()), None)

        if not tid:
            await ctx.send("❌ Предмет не найден.")
            return

        slot = ITEMS[tid].get("slot")
        if slot == "weapon":
            p.weapon_id = tid
        elif slot == "armor":
            p.armor_id = tid
        elif slot == "accessory":
            p.accessory_id = tid
        else:
            await ctx.send("❌ Этот предмет нельзя надеть.")
            return

        await self.bot.db.save(p)
        await ctx.send(f"✅ @{p.username} экипировал {ITEMS[tid]['name']} ({slot})")

    @commands.command(name="снять")
    async def cmd_unequip(self, ctx, slot: str = ""):
        p = await self.bot.get_player(ctx.author.name)
        s = slot.lower()
        if s in ["оружие", "weapon"]:
            p.weapon_id = None
        elif s in ["броня", "armor"]:
            p.armor_id = None
        elif s in ["аксессуар", "сфера", "accessory"]:
            p.accessory_id = None
        else:
            await ctx.send("❌ Укажите слот: оружие, броня или аксессуар.")
            return
        await self.bot.db.save(p)
        await ctx.send(f"✅ Слот {slot} теперь пуст.")

    @commands.command(name="магазин")
    async def cmd_shop(self, ctx):
        potions = []
        gear = []
        crystals = []

        for i in ITEMS.values():
            if i.get("price", 0) <= 0:
                continue
            item_str = f"{i['name']} ({i['price']}💰)"
            if i.get("type") == "use":
                potions.append(item_str)
            elif i.get("type") == "material":
                crystals.append(item_str)
            else:
                gear.append(item_str)

        lines = ["🏪 Магазин:"]
        if potions:
            lines.append("🧪 Расходники: " + " | ".join(potions))
        if gear:
            lines.append("⚔️ Экипировка: " + " | ".join(gear))
        if crystals:
            lines.append("💎 Кристаллы: " + " | ".join(crystals))

        await ctx.send("\n".join(lines))

    @commands.command(name="купить")
    async def cmd_buy(self, ctx, *, name: str = ""):
        p = await self.bot.get_player(ctx.author.name)
        tid = next(
            (
                k
                for k, v in ITEMS.items()
                if name.lower() in v["name"].lower() and v.get("price", 0) > 0
            ),
            None,
        )
        if not tid:
            await ctx.send("❌ Товар не найден.")
            return
        price = ITEMS[tid]["price"]
        if p.gold < price:
            await ctx.send("❌ Недостаточно золота.")
            return
        p.gold -= price
        await self.bot.db.add_to_inventory(p.username, tid)
        await self.bot.db.save(p)
        await ctx.send(f"✅ Куплено: {ITEMS[tid]['name']}!")

    @commands.command(name="крафты")
    async def cmd_crafts(self, ctx):
        recipes_info = []
        for r_key, r in CRAFTING_RECIPES.items():
            reqs = ", ".join(
                [f"{count}x {ITEMS[mat]['name']}" for mat, count in r["req"].items()]
            )
            recipes_info.append(
                f"{r['name']} [{r_key}]: Требует [{reqs}] ({r['desc']})"
            )
        await ctx.send("⚒️ Доступные рецепты крафта: " + " | ".join(recipes_info))

    @commands.command(name="крафт")
    async def cmd_craft(self, ctx, *, name: str = ""):
        name = name.lower().strip()
        recipe = CRAFTING_RECIPES.get(name) or next(
            (r for r in CRAFTING_RECIPES.values() if name in r["name"].lower()),
            None,
        )
        if not recipe:
            await ctx.send("❌ Рецепт не найден. Посмотрите !крафты")
            return

        p = await self.bot.get_player(ctx.author.name)
        inv = await self.bot.db.get_inventory(p.username)

        inv_counts = {}
        for i in inv:
            inv_counts[i] = inv_counts.get(i, 0) + 1

        for mat, count in recipe["req"].items():
            if inv_counts.get(mat, 0) < count:
                await ctx.send(
                    f"❌ Недостаточно ингредиентов! Нужно {count}x {ITEMS[mat]['name']}"
                )
                return

        for mat, count in recipe["req"].items():
            for _ in range(count):
                await self.bot.db.remove_from_inventory(p.username, mat)

        await self.bot.db.add_to_inventory(p.username, recipe["key"])
        await self.bot.db.save(p)
        await ctx.send(f"✨ @{p.username} успешно скрафтил [{recipe['name']}]!")

    @commands.command(name="продать")
    async def cmd_sell(self, ctx, *, name: str = ""):
        p = await self.bot.get_player(ctx.author.name)
        inv = await self.bot.db.get_inventory(p.username)
        tid = next(
            (
                k
                for k in inv
                if name.lower() in ITEMS[k]["name"].lower()
                and ITEMS[k].get("price", 0) > 0
            ),
            None,
        )
        if not tid:
            await ctx.send("❌ Предмет не найден в инвентаре или его нельзя продать.")
            return
        item = ITEMS[tid]
        sell_price = item["price"] // 2
        p.gold += sell_price
        await self.bot.db.remove_from_inventory(p.username, tid)
        await self.bot.db.save(p)
        await ctx.send(f"💰 @{p.username} продал {item['name']} за {sell_price}💰!")

    @commands.command(name="пить", aliases=["использовать"])
    async def cmd_use(self, ctx, *, name: str = ""):
        p = await self.bot.get_player(ctx.author.name)
        inv = await self.bot.db.get_inventory(p.username)
        tid = next(
            (
                k
                for k in inv
                if name.lower() in ITEMS[k]["name"].lower()
                and ITEMS[k]["type"] == "use"
            ),
            None,
        )
        if not tid:
            await ctx.send("❌ Зелье не найдено.")
            return
        item = ITEMS[tid]
        if "heal" in item:
            p.hp = min(self.bot.engine.get_max_hp(p), p.hp + item["heal"])
        if "restore_mp" in item:
            p.mp = min(self.bot.engine.get_max_mp(p), p.mp + item["restore_mp"])
        await self.bot.db.remove_from_inventory(p.username, tid)
        await self.bot.db.save(p)
        await ctx.send(f"🧪 @{p.username} использовал {item['name']}!")

    @commands.command(name="передать")
    async def cmd_give(
        self, ctx, category: str = "", target: str = "", *, arg: str = ""
    ):
        category = category.lower()
        target_name = target.strip("@").lower()
        sender_name = ctx.author.name.lower()

        if not category or not target_name:
            await ctx.send(
                "❌ Формат: !передать золото @юзер <сумма> ИЛИ !передать предмет @юзер <название>"
            )
            return

        if target_name == sender_name:
            await ctx.send("❌ Нельзя передавать предметы самому себе.")
            return

        sender_p = await self.bot.get_player(sender_name)
        target_p = await self.bot.get_player(target_name)

        if category in ["золото", "gold"]:
            try:
                amount = int(arg)
            except ValueError:
                await ctx.send("❌ Укажите корректную сумму золота.")
                return

            if amount <= 0:
                await ctx.send("❌ Сумма должна быть больше нуля.")
                return

            if sender_p.gold < amount:
                await ctx.send(
                    f"❌ У тебя недостаточно золота. В наличии: {sender_p.gold}💰"
                )
                return

            sender_p.gold -= amount
            target_p.gold += amount

            await self.bot.db.save(sender_p)
            await self.bot.db.save(target_p)
            await ctx.send(
                f"🤝 @{sender_p.username} передал @{target_p.username} {amount}💰!"
            )

        elif category in ["предмет", "item"]:
            item_query = arg.strip()
            if not item_query:
                await ctx.send("❌ Укажите название предмета для передачи.")
                return

            inv = await self.bot.db.get_inventory(sender_p.username)
            tid = next(
                (k for k in inv if item_query.lower() in ITEMS[k]["name"].lower()), None
            )

            if not tid:
                await ctx.send("❌ У тебя нет такого предмета в инвентаре.")
                return

            await self.bot.db.remove_from_inventory(sender_p.username, tid)
            await self.bot.db.add_to_inventory(target_p.username, tid)

            await ctx.send(
                f"🎁 @{sender_p.username} передал @{target_p.username} предмет: {ITEMS[tid]['name']}!"
            )
        else:
            await ctx.send(
                "❌ Использование: !передать золото @юзер <сумма> ИЛИ !передать предмет @юзер <название>"
            )
