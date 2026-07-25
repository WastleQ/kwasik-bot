# src/data.py

ITEMS = {
    # Зелья
    "hp_potion": {"name": "Зелье здоровья", "type": "use", "heal": 150, "price": 50},
    "mp_potion": {"name": "Зелье маны", "type": "use", "restore_mp": 100, "price": 50},
    
    # Оружие
    "iron_sword": {"name": "Железный меч", "type": "weapon", "slot": "weapon", "bonus_str": 5, "price": 200},
    "kasaka_dagger": {"name": "Кинжал Ракаша", "type": "weapon", "slot": "weapon", "bonus_str": 15, "bonus_agi": 5, "price": 0},
    "igris_sword": {"name": "Меч Игриса", "type": "weapon", "slot": "weapon", "bonus_str": 30, "price": 0},
    
    # Артефакты
    "orb_of_avarice": {
        "name": "Сфера Алчности", 
        "type": "weapon", 
        "slot": "accessory", 
        "bonus_int": 10,
        "magic_boost": 2.0, 
        "price": 0
    },
    
    # Броня
    "leather_armor": {"name": "Кожаная броня", "type": "armor", "slot": "armor", "bonus_vit": 5, "price": 200},
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
        "min_dmg": 70, "max_dmg": 120, "boss_drop": "hp_potion", "mob_drop": "iron_sword"
    },
    "4": {
        "name": "Храм Теней (Ранг B)",
        "mobs": [("Теневой солдат", 6000, False), ("Теневой Командир (БОСС)", 15000, True)],
        "min_dmg": 200, "max_dmg": 350, "boss_drop": "leather_armor", "mob_drop": "iron_sword"
    },
    "5": {
        "name": "Врата Хаоса (Ранг A)",
        "mobs": [("Высший орк", 25000, False), ("Повелитель Пламени (БОСС)", 70000, True)],
        "min_dmg": 500, "max_dmg": 900, "boss_drop": "orb_of_avarice", "mob_drop": "iron_sword"
    },
    "6": {
        "name": "Остров Чеджу (Ранг S)",
        "mobs": [("Мутант-муравей", 100000, False), ("Король Муравьев (БОСС)", 400000, True)],
        "min_dmg": 1800, "max_dmg": 3500, "boss_drop": "hp_potion", "mob_drop": "iron_sword"
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