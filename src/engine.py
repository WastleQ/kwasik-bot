import random
import math
from src.data import ITEMS

class RPGEngine:
    @staticmethod
    def get_stats(p):
        res = {"str": p.str_stat, "vit": p.vit, "agi": p.agi, "sen": p.sen, "int": p.int_stat}
        # Собираем статы со всех 3-х слотов
        for i_id in [p.weapon_id, p.armor_id, p.accessory_id]:
            if i_id and i_id in ITEMS:
                item = ITEMS[i_id]
                res["str"] += item.get("bonus_str", 0)
                res["vit"] += item.get("bonus_vit", 0)
                res["agi"] += item.get("bonus_agi", 0)
                res["int"] += item.get("bonus_int", 0)
                res["sen"] += item.get("bonus_sen", 0)
        return res

    def get_max_hp(self, p): return 100 + (self.get_stats(p)["vit"] * 15)
    def get_max_mp(self, p): return 150 + (self.get_stats(p)["int"] * 10)

    def get_rank(self, lvl):
        ranks = {10: "E", 20: "D", 30: "C", 40: "B", 50: "A"}
        for t, r in ranks.items():
            if lvl < t: return r
        return "S"

    def handle_death(self, p):
        p.hp = self.get_max_hp(p) // 2
        p.location_id = "0"

    def check_level_up(self, p):
        up = False
        while p.exp >= p.lvl * 100:
            p.lvl += 1
            p.exp -= (p.lvl - 1) * 100
            p.stat_points += 5
            p.hp = self.get_max_hp(p)
            p.mp = self.get_max_mp(p)
            up = True
        return up

    def fight(self, p, dungeon, is_magic=False, spell=None):
        st = self.get_stats(p)
        mob_data = random.choice(dungeon["mobs"])
        mob_name, mob_hp, is_boss = mob_data[0], mob_data[1], mob_data[2]
        
        # ЛОГИКА СФЕРЫ АЛЧНОСТИ
        m_mult = 2.0 if p.accessory_id == "orb_of_avarice" else 1.0

        if is_magic and spell:
            p_dmg = max(1, int(st["int"] * spell["damage_mult"] * m_mult))
        else:
            p_dmg = max(1, int(st["str"] * 2.2 + st["agi"] * 0.6))
        
        rounds = math.ceil(mob_hp / p_dmg)
        hits = 1 if is_magic else rounds
        total_damage = 0
        dodge_ch = min(0.3, st["agi"] * 0.005)
        
        for _ in range(hits):
            if random.random() > dodge_ch:
                dmg = random.randint(dungeon["min_dmg"], dungeon["max_dmg"])
                total_damage += max(1, dmg - int(st["vit"] * 0.7))
        
        p.hp -= total_damage
        if p.hp <= 0:
            self.handle_death(p)
            return f"💀 @{p.username} погиб в бою с {mob_name}!", None

        mob_exp = int(mob_hp * 0.4)
        p.exp += mob_exp
        p.gold += random.randint(30, 70) if is_boss else random.randint(10, 30)
        
        # Шанс дропа (Босс или Обычный)
        drop = None
        if is_boss and dungeon.get("boss_drop"):
            if random.random() < 0.15: drop = dungeon["boss_drop"]
        elif not is_boss and dungeon.get("mob_drop"):
            if random.random() < 0.05: drop = dungeon["mob_drop"]
            
        return f"⚔️ Победа над {mob_name}! +{mob_exp} EXP." + (" ✨ LVL UP!" if self.check_level_up(p) else ""), drop

    def calculate_raid_damage(self, p, has_buff, is_magic, spell):
        st = self.get_stats(p)
        m_mult = 2.0 if p.accessory_id == "orb_of_avarice" else 1.0
        if is_magic and spell:
            base = st["int"] * spell["damage_mult"] * m_mult
            crit = random.random() < min(0.3, st["sen"] * 0.005)
        else:
            base = st["str"] * 2.5
            crit = random.random() < min(0.4, st["agi"] * 0.005)
        dmg = int(base * (2.0 if crit else 1.0))
        return (int(dmg * 1.1) if has_buff else dmg), crit

    def raid_boss_retaliation(self, p, hp_perc):
        st = self.get_stats(p)
        rage = 1.0 + (1.0 - hp_perc) * 1.5
        return max(5, int(random.randint(30, 60) * rage - st["vit"] * 0.6))