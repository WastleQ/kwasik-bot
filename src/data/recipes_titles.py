# src/data/recipes_titles.py

ACHIEVEMENTS = {
    "first_hunt": {
        "name": "Первая кровь",
        "desc": "Совершить первую охоту в подземелье",
        "reward_gold": 100,
    },
    "hunter_10": {
        "name": "Опытный охотник",
        "desc": "Достигнуть 10 уровня",
        "reward_gold": 500,
    },
    "boss_slayer": {
        "name": "Убийца боссов",
        "desc": "Победить босса в подземелье",
        "reward_gold": 1000,
    },
    "pvp_winner": {
        "name": "Дуэлянт",
        "desc": "Одержать победу в PvP дуэли",
        "reward_gold": 300,
    },
}

TITLES = {
    "novice": {"name": "Новичок", "bonus_str": 0, "bonus_vit": 0, "req": None},
    "hunter_e": {
        "name": "Охотник E-ранга",
        "bonus_str": 5,
        "bonus_vit": 5,
        "req": "hunter_10",
    },
    "shadow_monarch": {
        "name": "Теневой Монарх",
        "bonus_str": 25,
        "bonus_agi": 15,
        "bonus_vit": 20,
        "req": "boss_slayer",
    },
}

CRAFTING_RECIPES = {
    "shadow_dagger": {
        "key": "shadow_dagger",
        "name": "Кинжал Тени",
        "req": {"crystal_b": 5, "kasaka_dagger": 1},
        "desc": "+35 STR, +10 AGI",
    },
    "monarch_ring": {
        "key": "monarch_ring",
        "name": "Перстень Монарха",
        "req": {"crystal_s": 3, "ring_of_power": 1},
        "desc": "+20 STR, +15 VIT, +10 INT",
    },
    "dragon_blade": {
        "key": "dragon_blade",
        "name": "Клинок Дракона",
        "req": {"crystal_s": 5, "igris_sword": 1},
        "desc": "+65 STR, +20 AGI",
    },
    "elixir_of_life": {
        "key": "elixir_of_life",
        "name": "Эликсир Жизни",
        "req": {"crystal_c": 3, "greater_hp_potion": 2},
        "desc": "Восстанавливает 1000 HP",
    },
}
