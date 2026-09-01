# src/data/dungeons.py

DUNGEONS = {
    "0": {"name": "Город", "mobs": [], "min_dmg": 0, "max_dmg": 0, "boss_drop": None},
    "1": {
        "name": "Слабое логово (Ранг E)",
        "mobs": [
            ("Гоблин", 60, False),
            ("Слизень", 80, False),
            ("Гоблин-Шаман (БОСС)", 250, True),
        ],
        "min_dmg": 5,
        "max_dmg": 15,
        "boss_drop": "kasaka_dagger",
        "mob_drop": "iron_sword",
    },
    "2": {
        "name": "Ледяной лес (Ранг D)",
        "mobs": [("Ледяной медведь", 400, False), ("Ледяной Голем (БОСС)", 1200, True)],
        "min_dmg": 25,
        "max_dmg": 50,
        "boss_drop": "ice_cloak",
        "mob_drop": "iron_sword",
    },
    "3": {
        "name": "Заброшенные копи (Ранг C)",
        "mobs": [
            ("Горный тролль", 1500, False),
            ("Орк-надзиратель", 1800, False),
            ("Верховный Орк (БОСС)", 4500, True),
        ],
        "min_dmg": 70,
        "max_dmg": 120,
        "boss_drop": "knight_sword",
        "mob_drop": "greater_hp_potion",
    },
    "4": {
        "name": "Храм Теней (Ранг B)",
        "mobs": [
            ("Теневой солдат", 6000, False),
            ("Теневой Командир (БОСС)", 15000, True),
        ],
        "min_dmg": 200,
        "max_dmg": 350,
        "boss_drop": "steel_armor",
        "mob_drop": "greater_mp_potion",
    },
    "5": {
        "name": "Врата Хаоса (Ранг A)",
        "mobs": [
            ("Высший орк", 25000, False),
            ("Повелитель Пламени (БОСС)", 70000, True),
        ],
        "min_dmg": 500,
        "max_dmg": 900,
        "boss_drop": "demon_dagger",
        "mob_drop": "ring_of_power",
    },
    "6": {
        "name": "Остров Чеджу (Ранг S)",
        "mobs": [
            ("Мутант-муравей", 100000, False),
            ("Король Муравьев (БОСС)", 400000, True),
        ],
        "min_dmg": 1500,
        "max_dmg": 2500,
        "boss_drop": "amulet_of_wisdom",
        "mob_drop": "knight_spear",
    },
}

RAID_BOSSES = {
    "igris": {
        "name": "Кровавый Командующий Игрис",
        "hp": 100000,
        "aoe_dmg": 150,
        "reward_gold": 5000,
        "reward_exp": 3000,
        "drops": ["igris_sword"],
    }
}
