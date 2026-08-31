import math
import random

from src.data import ACHIEVEMENTS, ITEMS, TITLES


class RPGEngine:
    @staticmethod
    def get_stats(p):
        res = {
            "str": p.str_stat,
            "vit": p.vit,
            "agi": p.agi,
            "sen": p.sen,
            "int": p.int_stat,
        }
        # Собираем статы со всех 3-х слотов снаряжения
        for i_id in [p.weapon_id, p.armor_id, p.accessory_id]:
            if i_id and i_id in ITEMS:
                item = ITEMS[i_id]
                res["str"] += item.get("bonus_str", 0)
                res["vit"] += item.get("bonus_vit", 0)
                res["agi"] += item.get("bonus_agi", 0)
                res["int"] += item.get("bonus_int", 0)
                res["sen"] += item.get("bonus_sen", 0)

        # Бонусы от активного титула
        if p.title in TITLES:
            t_data = TITLES[p.title]
            res["str"] += t_data.get("bonus_str", 0)
            res["vit"] += t_data.get("bonus_vit", 0)
            res["agi"] += t_data.get("bonus_agi", 0)
            res["int"] += t_data.get("bonus_int", 0)
            res["sen"] += t_data.get("bonus_sen", 0)

        return res

    def get_max_hp(self, p):
        return 100 + (self.get_stats(p)["vit"] * 10)

    def get_max_mp(self, p):
        return 150 + (self.get_stats(p)["int"] * 5)

    def get_rank(self, lvl):
        ranks = {10: "E", 20: "D", 30: "C", 40: "B", 50: "A"}
        for t, r in ranks.items():
            if lvl < t:
                return r
        return "S"

    def handle_death(self, p):
        p.hp = max(1, int(self.get_max_hp(p) * 0.1))
        p.mp = max(0, int(self.get_max_mp(p) * 0.1))
        p.gold = max(0, int(p.gold * 0.9))
        p.location_id = "0"

    def handle_pvp_defeat(self, p):
        p.hp = max(1, int(self.get_max_hp(p) * 0.1))
        p.mp = max(0, int(self.get_max_mp(p) * 0.1))

    def normalize_player_stats(self, p):
        max_earned = max(0, (p.lvl - 1) * 5)
        current_spent = (
            (p.str_stat - 10)
            + (p.agi - 10)
            + (p.vit - 10)
            + (p.int_stat - 10)
            + (p.sen - 10)
        )
        total_points = current_spent + p.stat_points
        if total_points > max_earned:
            p.str_stat = 10
            p.agi = 10
            p.vit = 10
            p.int_stat = 10
            p.sen = 10
            p.stat_points = max_earned
            p.hp = self.get_max_hp(p)
            p.mp = self.get_max_mp(p)
        elif total_points < max_earned:
            p.stat_points += max_earned - total_points

    def clamp_resources(self, p):
        self.normalize_player_stats(p)
        p.hp = min(p.hp, self.get_max_hp(p))
        p.mp = min(p.mp, self.get_max_mp(p))
        p.hp = max(0, p.hp)
        p.mp = max(0, p.mp)

    def get_exp_required(self, lvl):
        base = lvl * 100
        return base * 2 if lvl >= 100 else base

    def check_level_up(self, p):
        up = False
        while p.exp >= self.get_exp_required(p.lvl):
            req = self.get_exp_required(p.lvl)
            p.lvl += 1
            p.exp -= req
            p.stat_points += 5
            p.hp = self.get_max_hp(p)
            p.mp = self.get_max_mp(p)
            up = True
        return up

    @staticmethod
    def unlock_achievement(p, ach_id):
        if ach_id not in ACHIEVEMENTS:
            return None
        unlocked = [a.strip() for a in p.achievements.split(",") if a.strip()]
        if ach_id not in unlocked:
            unlocked.append(ach_id)
            p.achievements = ",".join(unlocked)
            ach = ACHIEVEMENTS[ach_id]
            p.gold += ach.get("reward_gold", 0)
            return ach
        return None

    @staticmethod
    def get_crystal_drop(location_id, is_boss=False):
        mapping = {
            "1": "crystal_e",
            "2": "crystal_d",
            "3": "crystal_c",
            "4": "crystal_b",
            "5": "crystal_a",
            "6": "crystal_s",
        }
        c_id = mapping.get(str(location_id))
        if not c_id:
            return None
        chance = 0.50 if is_boss else 0.25
        return c_id if random.random() < chance else None

    def fight(self, p, dungeon, is_magic=False, spell=None):
        st = self.get_stats(p)
        mob_data = random.choice(dungeon["mobs"])
        mob_name, mob_hp, is_boss = mob_data[0], mob_data[1], mob_data[2]

        # ЛОГИКА СФЕРЫ АЛЧНОСТИ
        m_mult = 1.3 if p.accessory_id == "orb_of_avarice" else 1.0

        if is_magic and spell:
            s_type = spell.get("type", "attack")
            if s_type == "heal":
                heal_val = spell.get("heal", 250) + int(st["int"] * 1.5)
                max_hp = self.get_max_hp(p)
                p.hp = min(max_hp, p.hp + heal_val)
                return (
                    f"✨ @{p.username} кастует [{spell['name']}] и восстанавливает {heal_val} HP!",
                    None,
                )
            elif s_type == "shield":
                shield_val = spell.get("shield", 150) + int(st["int"] * 1.5)
                p.hp = min(self.get_max_hp(p) + shield_val, p.hp + shield_val)
                return (
                    f"🛡️ @{p.username} создает Магический щит (+{shield_val} прочности)!",
                    None,
                )
            else:
                base_dmg = st["int"] * spell["damage_mult"] * m_mult
                crit = random.random() < min(
                    0.45, (st["sen"] * 0.003) + (st["int"] * 0.003)
                )
                p_dmg = max(1, int(base_dmg * (1.5 if crit else 1.0)))
        else:
            p_dmg = max(1, int(st["str"] * 3.0 + st["agi"] * 0.8))

        rounds = math.ceil(mob_hp / p_dmg)
        hits = 1 if (is_magic and spell and spell.get("type") == "attack") else rounds
        total_damage = 0
        dodge_ch = (
            0.0
            if (is_magic and spell and spell.get("type") == "attack")
            else min(0.3, st["agi"] * 0.005)
        )

        for _ in range(hits):
            if random.random() > dodge_ch:
                dmg = random.randint(dungeon["min_dmg"], dungeon["max_dmg"])
                total_damage += max(1, dmg - int(st["vit"] * 0.7))

        p.hp -= total_damage
        if p.hp <= 0:
            self.handle_death(p)
            return f"💀 @{p.username} погиб в бою с {mob_name}!", None

        player_damage = p_dmg * hits
        mob_exp = int(mob_hp * 0.2)
        p.exp += mob_exp
        p.gold += random.randint(30, 70) if is_boss else random.randint(10, 30)

        # Проверяем достижения за охоту и боссов
        ach_msg = ""
        ach1 = self.unlock_achievement(p, "first_hunt")
        if ach1:
            ach_msg += f" 🏆 Достижение: [{ach1['name']}] (+{ach1['reward_gold']}💰)!"

        if is_boss:
            ach2 = self.unlock_achievement(p, "boss_slayer")
            if ach2:
                ach_msg += (
                    f" 🏆 Достижение: [{ach2['name']}] (+{ach2['reward_gold']}💰)!"
                )

        if p.lvl >= 10:
            ach3 = self.unlock_achievement(p, "hunter_10")
            if ach3:
                ach_msg += (
                    f" 🏆 Достижение: [{ach3['name']}] (+{ach3['reward_gold']}💰)!"
                )

        # Шанс дропа (Босс или Обычный)
        drops = []
        if is_boss and dungeon.get("boss_drop") and random.random() < 0.15:
            drops.append(dungeon["boss_drop"])
        elif not is_boss and dungeon.get("mob_drop") and random.random() < 0.05:
            drops.append(dungeon["mob_drop"])

        c_drop = self.get_crystal_drop(p.location_id, is_boss)
        if c_drop:
            drops.append(c_drop)

        crit_label = (
            " крит."
            if (
                is_magic
                and spell
                and spell.get("type") == "attack"
                and "crit" in locals()
                and crit
            )
            else ""
        )
        max_hp = self.get_max_hp(p)
        max_mp = self.get_max_mp(p)
        return (
            f"⚔️ Победа над {mob_name}! Урон: {player_damage}{crit_label}. +{mob_exp} EXP. (❤️ Осталось: {p.hp}/{max_hp} HP, 🔮 {p.mp}/{max_mp} MP){ach_msg}"
            + (" ✨ LVL UP!" if self.check_level_up(p) else ""),
            drops,
        )

    def calculate_raid_damage(self, p, has_buff, is_magic, spell):
        st = self.get_stats(p)
        m_mult = 1.3 if p.accessory_id == "orb_of_avarice" else 1.0
        if is_magic and spell:
            s_type = spell.get("type", "attack")
            if s_type in ["heal", "shield"]:
                return 0, False
            base = st["int"] * spell["damage_mult"] * m_mult
            crit = random.random() < min(
                0.45, (st["sen"] * 0.003) + (st["int"] * 0.003)
            )
        else:
            base = st["str"] * 3.0
            crit = random.random() < min(0.4, st["agi"] * 0.005)
        dmg = int(base * (2.0 if crit else 1.0))
        return (int(dmg * 1.1) if has_buff else dmg), crit

    def raid_boss_retaliation(self, p, hp_perc):
        st = self.get_stats(p)
        rage = 1.0 + (1.0 - hp_perc) * 1.5
        return max(5, int(random.randint(30, 60) * rage - st["vit"] * 0.6))
