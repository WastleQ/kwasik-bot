#!/usr/bin/env python3
import asyncio

from src.engine import RPGEngine
from src.models import DBManager

db = DBManager()
engine = RPGEngine()


async def main():
    await db.init_db()
    while True:
        print("\n=== KWASIK BOT ADMIN TUI ===")
        print("1. Список всех игроков")
        print("2. Найти / Редактировать игрока")
        print("3. Выдать предмет игроку")
        print("4. Забрать предмет у игрока")
        print("0. Выход")

        choice = input("\nВыберите пункт меню: ").strip()

        if choice == "1":
            players = await db.get_all_players()
            print(f"\nВсего игроков в базе: {len(players)}")
            print(
                f"{'Ник':<15} | {'Ур':<4} | {'Золото':<7} | {'Титул':<15} | {'HP/MP':<10} | {'Статы (Str/Agi/Vit/Int/Sen)'}"
            )
            print("-" * 80)
            for p in players:
                stats = f"{p.str_stat}/{p.agi}/{p.vit}/{p.int_stat}/{p.sen}"
                hpmp = f"{p.hp}/{p.mp}"
                print(
                    f"{p.username:<15} | {p.lvl:<4} | {p.gold:<7} | {p.title:<15} | {hpmp:<10} | {stats}"
                )

        elif choice == "2":
            uname = input("Введите ник игрока: ").strip().lower().replace("@", "")
            p = await db.load(uname)
            if not p:
                print(f"⚠️ Игрок '{uname}' не найден в базе.")
                continue

            while True:
                print(f"\n--- Профиль: {p.username} ---")
                print(1, f"Уровень (lvl): {p.lvl}")
                print(2, f"Опыт (exp): {p.exp}")
                print(3, f"Свободные очки статов (stat_points): {p.stat_points}")
                print(4, f"Золото (gold): {p.gold}")
                print(5, f"Титул (title): {p.title}")
                print(6, f"Сила (str_stat): {p.str_stat}")
                print(7, f"Ловкость (agi): {p.agi}")
                print(8, f"Выносливость (vit): {p.vit}")
                print(9, f"Интеллект (int_stat): {p.int_stat}")
                print(10, f"Восприятие (sen): {p.sen}")
                print(
                    11,
                    f"HP: {p.hp}/{engine.get_max_hp(p)}, MP: {p.mp}/{engine.get_max_mp(p)}",
                )
                print("inv", f"Инвентарь: {await db.get_inventory(p.username)}")
                print("b", "Назад в главное меню")

                sub = input("Что изменить (номер или поле): ").strip().lower()
                if sub == "b":
                    break
                elif sub == "1":
                    try:
                        new_val = int(input("Новый уровень: "))
                        p.lvl = max(1, new_val)
                        engine.clamp_resources(p)
                        await db.save(p)
                        p = await db.load(uname)
                        print("✅ Уровень изменен и статы нормализованы!")
                    except ValueError:
                        print("⚠️ Неверное число.")
                elif sub == "2":
                    try:
                        p.exp = int(input("Новый опыт: "))
                        await db.save(p)
                        p = await db.load(uname)
                        print("✅ Опыт изменен!")
                    except ValueError:
                        print("⚠️ Неверное число.")
                elif sub == "3":
                    try:
                        p.stat_points = int(input("Новые очков статов: "))
                        await db.save(p)
                        p = await db.load(uname)
                        print("✅ Очки статов изменены!")
                    except ValueError:
                        print("⚠️ Неверное число.")
                elif sub == "4":
                    try:
                        p.gold = int(input("Новое золота: "))
                        await db.save(p)
                        p = await db.load(uname)
                        print("✅ Золото изменено!")
                    except ValueError:
                        print("⚠️ Неверное число.")
                elif sub == "5":
                    p.title = input("Новый титул: ").strip()
                    await db.save(p)
                    p = await db.load(uname)
                    print("✅ Титул изменен!")
                elif sub == "6":
                    try:
                        p.str_stat = int(input("Новая Сила: "))
                        engine.clamp_resources(p)
                        await db.save(p)
                        p = await db.load(uname)
                        print("✅ Сила изменена!")
                    except ValueError:
                        print("⚠️ Неверное число.")
                elif sub == "7":
                    try:
                        p.agi = int(input("Новая Ловкость: "))
                        engine.clamp_resources(p)
                        await db.save(p)
                        p = await db.load(uname)
                        print("✅ Ловкость изменена!")
                    except ValueError:
                        print("⚠️ Неверное число.")
                elif sub == "8":
                    try:
                        p.vit = int(input("Новая Выносливость: "))
                        engine.clamp_resources(p)
                        await db.save(p)
                        p = await db.load(uname)
                        print("✅ Выносливость изменена!")
                    except ValueError:
                        print("⚠️ Неверное число.")
                elif sub == "9":
                    try:
                        p.int_stat = int(input("Новый Интеллект: "))
                        engine.clamp_resources(p)
                        await db.save(p)
                        p = await db.load(uname)
                        print("✅ Интеллект изменен!")
                    except ValueError:
                        print("⚠️ Неверное число.")
                elif sub == "10":
                    try:
                        p.sen = int(input("Новое Восприятие: "))
                        engine.clamp_resources(p)
                        await db.save(p)
                        p = await db.load(uname)
                        print("✅ Восприятие изменено!")
                    except ValueError:
                        print("⚠️ Неверное число.")
                else:
                    print("⚠️ Неизвестная команда.")

        elif choice == "3":
            uname = input("Введите ник игрока: ").strip().lower().replace("@", "")
            item_id = input(
                "Введите ID предмета (например iron_sword, hp_potion): "
            ).strip()
            await db.add_to_inventory(uname, item_id)
            print(f"✅ Предмет '{item_id}' выдан игроку '{uname}'.")

        elif choice == "4":
            uname = input("Введите ник игрока: ").strip().lower().replace("@", "")
            inv = await db.get_inventory(uname)
            print(f"Инвентарь: {inv}")
            item_id = input("Введите ID предмета для удаления: ").strip()
            await db.add_to_inventory(uname, item_id)  # wait, remove
            await db.remove_from_inventory(uname, item_id)
            print(f"✅ Предмет '{item_id}' удален у игрока '{uname}'.")

        elif choice == "0":
            print("Выход...")
            break
        else:
            print("⚠️ Неверный выбор.")


if __name__ == "__main__":
    asyncio.run(main())
