# src/data/spells.py

SPELLS = {
    "шар": {
        "name": "Огненный шар",
        "mp_cost": 50,
        "damage_mult": 1.3,
        "type": "attack",
    },
    "молния": {
        "name": "Удар молнии",
        "mp_cost": 100,
        "damage_mult": 1.7,
        "type": "attack",
    },
    "метеор": {
        "name": "Метеорит",
        "mp_cost": 300,
        "damage_mult": 2.2,
        "type": "attack",
    },
    "хил": {"name": "Исцеление", "mp_cost": 40, "heal": 250, "type": "heal"},
    "щит": {"name": "Магический щит", "mp_cost": 40, "shield": 150, "type": "shield"},
}
