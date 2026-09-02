#!/usr/bin/env python3
import subprocess
import sys


def main():
    while True:
        print("\n=== KWASIK RPG BOT LAUNCHER ===")
        print("1. 🚀 Запустить ВСЁ (Twitch Bot + Telegram Bot + Web API)")
        print("2. 🎮 Запустить Twitch-бота (main.py)")
        print("3. 🤖 Запустить Telegram-бота (telegram_bot.py)")
        print("4. 🌐 Запустить Web / Mini App сервер (run_web.py)")
        print("5. 👑 Запустить Admin TUI (admin_tui.py)")
        print("0. Выход")

        choice = input("\nВыберите пункт меню: ").strip()
        if choice == "1":
            print("🚀 Запуск всех сервисов... Нажмите Ctrl+C для остановки.")
            procs = [
                subprocess.Popen([sys.executable, "main.py"]),
                subprocess.Popen([sys.executable, "telegram_bot.py"]),
                subprocess.Popen([sys.executable, "run_web.py"]),
            ]
            try:
                for p in procs:
                    p.wait()
            except KeyboardInterrupt:
                print("\n🛑 Остановка всех сервисов...")
                for p in procs:
                    p.terminate()
        elif choice == "2":
            subprocess.run([sys.executable, "main.py"], check=False)
        elif choice == "3":
            subprocess.run([sys.executable, "telegram_bot.py"], check=False)
        elif choice == "4":
            subprocess.run([sys.executable, "run_web.py"], check=False)
        elif choice == "5":
            subprocess.run([sys.executable, "admin_tui.py"], check=False)
        elif choice == "0":
            print("Выход...")
            break
        else:
            print("⚠️ Неверный выбор.")


if __name__ == "__main__":
    main()
