#!/usr/bin/env python3
import logging
import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()
TOKEN = os.getenv("TG_BOT_TOKEN", "8610234867:AAEONuZCm6arZ4mImXmj_SkKH7swo0i2P10")
WEB_APP_URL = os.getenv(
    "WEB_APP_URL", "https://kwasik-bot-production.up.railway.app"
)  # Fallback or user web app URL

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("TelegramBot")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or user.first_name or "hunter"

    keyboard = [
        [
            InlineKeyboardButton(
                "🎮 Открыть Kwasik RPG",
                web_app=WebAppInfo(url=f"{WEB_APP_URL}?user={username}"),
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🔥 Привет, Охотник **{user.first_name}**!\n\n"
        "Добро пожаловать в **Kwasik RPG** — интерактивную ролевую игру по мотивам *Solo Leveling*.\n\n"
        "Нажми кнопку ниже, чтобы открыть игру в Telegram Mini App:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


def main():
    if not TOKEN:
        logger.error("❌ Telegram Bot Token not found!")
        return

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    logger.info("🤖 Telegram Bot started and listening...")
    application.run_polling()


if __name__ == "__main__":
    main()
