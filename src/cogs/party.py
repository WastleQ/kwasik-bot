import random

from twitchio.ext import commands

from src.data import DUNGEONS, ITEMS


class PartyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="пати")
    async def cmd_party(self, ctx, action: str = "", *, arg: str = ""):
        user = ctx.author.name.lower()
        action = action.lower()

        if not action:
            # Показать статус пати
            leader = self.bot.player_party.get(user)
            if not leader:
                await ctx.send(
                    f"👥 @{ctx.author.name}, ты не состоишь в группе. Используй: !пати создать"
                )
                return
            members = self.bot.parties.get(leader, [])
            await ctx.send(
                f"👥 Группа лидера @{leader}: " + ", ".join([f"@{m}" for m in members])
            )
            return

        if action == "создать":
            if self.bot.player_party.get(user):
                await ctx.send(
                    "❌ Ты уже состоишь в группе. Сначала покинь текущую (!пати покинуть)."
                )
                return
            self.bot.parties[user] = [user]
            self.bot.player_party[user] = user
            await ctx.send(
                f"⚔️ @{ctx.author.name} создал группу! Приглашай бойцов: !пати инвайт @юзер"
            )

        elif action == "инвайт":
            leader = self.bot.player_party.get(user)
            if not leader or leader != user:
                await ctx.send("❌ Только лидер группы может приглашать игроков.")
                return
            target = arg.strip("@").lower()
            if not target or target == user:
                await ctx.send("❌ Укажи корректного пользователя.")
                return
            if self.bot.player_party.get(target):
                await ctx.send(f"❌ @{target} уже состоит в другой группе.")
                return
            self.bot.party_invites[target] = leader
            await ctx.send(
                f"📩 @{target}, приглашение в пати от @{user}! Напиши !пати принять"
            )

        elif action == "принять":
            leader = self.bot.party_invites.pop(user, None)
            if not leader or leader not in self.bot.parties:
                await ctx.send("❌ У тебя нет активных приглашений в группу.")
                return
            if len(self.bot.parties[leader]) >= 5:
                await ctx.send("❌ Группа уже заполнена (максимум 5 участников).")
                return
            self.bot.parties[leader].append(user)
            self.bot.player_party[user] = leader
            await ctx.send(f"🤝 @{ctx.author.name} присоединился к группе @{leader}!")

        elif action == "покинуть":
            leader = self.bot.player_party.get(user)
            if not leader:
                await ctx.send("❌ Ты не в группе.")
                return

            members = self.bot.parties.get(leader, [])
            if user in members:
                members.remove(user)
            del self.bot.player_party[user]

            if user == leader or not members:
                # Распускаем пати
                if leader in self.bot.parties:
                    del self.bot.parties[leader]
                for m in members:
                    if m in self.bot.player_party:
                        del self.bot.player_party[m]
                await ctx.send(f"🛑 Группа @{leader} распущена.")
            else:
                await ctx.send(f"🚪 @{ctx.author.name} покинул группу.")

        elif action == "ход":
            leader = self.bot.player_party.get(user)
            if not leader or leader != user:
                await ctx.send("❌ Только лидер группы может изменять локацию пати.")
                return
            loc_id = arg.strip()
            if loc_id not in DUNGEONS:
                await ctx.send("❌ Неверный ID врат. Используй !врата")
                return
            members = self.bot.parties[leader]
            for m in members:
                p = await self.bot.get_player(m)
                p.location_id = loc_id
                await self.bot.db.save(p)
            await ctx.send(
                f"🚀 Группа @{leader} переместилась во врата: {DUNGEONS[loc_id]['name']}"
            )

        elif action == "охота":
            leader = self.bot.player_party.get(user)
            if not leader or leader != user:
                await ctx.send("❌ Только лидер группы может начать совместную охоту.")
                return

            members = self.bot.parties.get(leader, [])
            if not members:
                await ctx.send("❌ Группа пуста.")
                return

            # Проверяем локацию первого участника
            p_lead = await self.bot.get_player(members[0])
            loc_id = p_lead.location_id
            if loc_id == "0":
                await ctx.send(
                    "🏘️ Группа в городе. Лидер должен выбрать врата: !пати ход [ID]"
                )
                return

            dungeon = DUNGEONS[loc_id]
            mob_data = random.choice(dungeon["mobs"])
            mob_name, mob_hp, is_boss = mob_data[0], mob_data[1], mob_data[2]

            # Собираем живых участников и их урон
            battle_log = [f"⚔️ Группа атаковала {mob_name} ({mob_hp} HP)!"]
            total_party_dmg = 0
            alive_players = []

            for m in members:
                p = await self.bot.get_player(m)
                if p.hp <= 0:
                    battle_log.append(f"💀 @{m} без сознания и не может сражаться.")
                    continue
                alive_players.append(p)
                st = self.bot.engine.get_stats(p)
                m_mult = 2.0 if p.accessory_id == "orb_of_avarice" else 1.0
                p_dmg = max(
                    1,
                    int(st["str"] * 2.0 + st["agi"] * 0.5 + st["int"] * 0.5)
                    * int(m_mult),
                )
                total_party_dmg += p_dmg

            if not alive_players:
                await ctx.send("❌ Все участники группы погибли и не могут сражаться!")
                return

            if total_party_dmg >= mob_hp:
                # Победа группы
                exp_reward = int((mob_hp * 0.5) / len(alive_players))
                gold_reward = int((70 if is_boss else 30) / len(alive_players))

                drop = None
                if is_boss and dungeon.get("boss_drop") and random.random() < 0.25:
                    drop = dungeon["boss_drop"]
                elif not is_boss and dungeon.get("mob_drop") and random.random() < 0.10:
                    drop = dungeon["mob_drop"]

                for p in alive_players:
                    p.exp += exp_reward
                    p.gold += gold_reward
                    if drop:
                        await self.bot.db.add_to_inventory(p.username, drop)
                    self.bot.engine.check_level_up(p)
                    await self.bot.db.save(p)

                res = f"🎉 Победа группы над {mob_name}! Каждый получил +{exp_reward} EXP и +{gold_reward}💰."
                if drop:
                    res += f" 💎 Группа добыла: {ITEMS[drop]['name']}!"
                await ctx.send(res)
            else:
                # Обычный бой с ответным уроном
                mob_dmg = random.randint(dungeon["min_dmg"], dungeon["max_dmg"])
                for p in alive_players:
                    st = self.bot.engine.get_stats(p)
                    actual_dmg = max(1, mob_dmg - int(st["vit"] * 0.5))
                    p.hp -= actual_dmg
                    if p.hp <= 0:
                        self.bot.engine.handle_death(p)
                    await self.bot.db.save(p)
                await ctx.send(
                    f"⚔️ Бой с {mob_name} продолжается! Группа нанесла {total_party_dmg} урона (нужно {mob_hp}). Монстр контратаковал!"
                )
        else:
            await ctx.send(
                "❌ Команды пати: !пати [создать|инвайт|принять|покинуть|ход|охота]"
            )
