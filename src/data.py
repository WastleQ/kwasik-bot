# src/data.py

ITEMS = {
    # Зелья
    "hp_potion": {"name": "Зелье здоровья", "type": "use", "heal": 150, "price": 50},
    "mp_potion": {"name": "Зелье маны", "type": "use", "restore_mp": 100, "price": 50},
    "greater_hp_potion": {"name": "Большое зелье здоровья", "type": "use", "heal": 400, "price": 150},
    "greater_mp_potion": {"name": "Большое зелье маны", "type": "use", "restore_mp": 300, "price": 150},
    
    # Оружие
    "iron_sword": {"name": "Железный меч", "type": "weapon", "slot": "weapon", "bonus_str": 5, "price": 200},
    "knight_sword": {"name": "Рыцарский меч", "type": "weapon", "slot": "weapon", "bonus_str": 12, "bonus_agi": 3, "price": 500},
    "knight_spear": {"name": "Рыцарское копьё", "type": "weapon", "slot": "weapon", "bonus_str": 20, "price": 900},
    "kasaka_dagger": {"name": "Кинжал Ракаша", "type": "weapon", "slot": "weapon", "bonus_str": 15, "bonus_agi": 5, "price": 0},
    "igris_sword": {"name": "Меч Игриса", "type": "weapon", "slot": "weapon", "bonus_str": 30, "price": 0},
    "demon_dagger": {"name": "Демонический кинжал", "type": "weapon", "slot": "weapon", "bonus_str": 45, "bonus_agi": 15, "price": 0},
    
    # Артефакты
    "orb_of_avarice": {
        "name": "Сфера Алчности", 
        "type": "weapon", 
        "slot": "accessory", 
        "bonus_int": 10,
        "magic_boost": 2.0, 
        "price": 0
    },
    "ring_of_power": {"name": "Кольцо силы", "type": "weapon", "slot": "accessory", "bonus_str": 8, "bonus_vit": 5, "price": 800},
    "amulet_of_wisdom": {"name": "Амулет мудрости", "type": "weapon", "slot": "accessory", "bonus_int": 15, "bonus_sen": 10, "price": 1000},
    
    # Броня
    "leather_armor": {"name": "Кожаная броня", "type": "armor", "slot": "armor", "bonus_vit": 5, "price": 200},
    "steel_armor": {"name": "Стальная броня", "type": "armor", "slot": "armor", "bonus_vit": 15, "price": 600},
    "shadow_cloak": {"name": "Плащ тени", "type": "armor", "slot": "armor", "bonus_vit": 20, "bonus_agi": 10, "price": 1200},
    "ice_cloak": {"name": "Ледяной плащ", "type": "armor", "slot": "armor", "bonus_vit": 10, "bonus_int": 5, "price": 0}
}

DUNGEONS = {
    "0": {"name": "Город", "mobs": [], "min_dmg": 0, "max_dmg": 0, "boss_drop": None},
    "1": {
        "name": "Слабое логово (Ранг E)",
        "mobs": [("Гоблин", 60, False), ("Слизень", 80, False), ("Гоблин-Шаман (БОСС)", 250, True)],
        "min_dmg": 5, "max_dmg": 15, "boss_drop": "kasaka_dagger", "mob_drop": "iron_sword"
    },
    "2": {
        "name": "Ледяной лес (Ранг D)",
        "mobs": [("Ледяной медведь", 400, False), ("Ледяной Голем (БОСС)", 1200, True)],
        "min_dmg": 25, "max_dmg": 50, "boss_drop": "ice_cloak", "mob_drop": "iron_sword"
    },
    "3": {
        "name": "Заброшенные копи (Ранг C)",
        "mobs": [("Горный тролль", 1500, False), ("Орк-надзиратель", 1800, False), ("Верховный Орк (БОСС)", 4500, True)],
        "min_dmg": 70, "max_dmg": 120, "boss_drop": "knight_sword", "mob_drop": "greater_hp_potion"
    },
    "4": {
        "name": "Храм Теней (Ранг B)",
        "mobs": [("Теневой солдат", 6000, False), ("Теневой Командир (БОСС)", 15000, True)],
        "min_dmg": 200, "max_dmg": 350, "boss_drop": "steel_armor", "mob_drop": "greater_mp_potion"
    },
    "5": {
        "name": "Врата Хаоса (Ранг A)",
        "mobs": [("Высший орк", 25000, False), ("Повелитель Пламени (БОСС)", 70000, True)],
        "min_dmg": 500, "max_dmg": 900, "boss_drop": "demon_dagger", "mob_drop": "ring_of_power"
    },
    "6": {
        "name": "Остров Чеджу (Ранг S)",
        "mobs": [("Мутант-муравей", 100000, False), ("Король Муравьев (БОСС)", 400000, True)],
        "min_dmg": 1800, "max_dmg": 3500, "boss_drop": "amulet_of_wisdom", "mob_drop": "knight_spear"
    }
}

RAID_BOSSES = {
    "igris": {
        "name": "Кровавый Командующий Игрис",
        "hp": 100000, "aoe_dmg": 150, "reward_gold": 5000, "reward_exp": 3000,
        "drops": ["igris_sword"]
    }
}

SPELLS = {
    "шар": {"name": "Огненный шар", "mp_cost": 30, "damage_mult": 5.0},
    "молния": {"name": "Удар молнии", "mp_cost": 50, "damage_mult": 8.0}
}

ACHIEVEMENTS = {
    "first_hunt": {"name": "Первая кровь", "desc": "Совершить первую охоту в подземелье", "reward_gold": 100},
    "hunter_10": {"name": "Опытный охотник", "desc": "Достигнуть 10 уровня", "reward_gold": 500},
    "boss_slayer": {"name": "Убийца боссов", "desc": "Победить босса в подземелье", "reward_gold": 1000},
    "pvp_winner": {"name": "Дуэлянт", "desc": "Одержать победу в PvP дуэли", "reward_gold": 300}
}

TITLES = {
    "novice": {"name": "Новичок", "bonus_str": 0, "bonus_vit": 0, "req": None},
    "hunter_e": {"name": "Охотник E-ранга", "bonus_str": 5, "bonus_vit": 5, "req": "hunter_10"},
    "shadow_monarch": {"name": "Теневой Монарх", "bonus_str": 25, "bonus_agi": 15, "bonus_vit": 20, "req": "boss_slayer"}
}
