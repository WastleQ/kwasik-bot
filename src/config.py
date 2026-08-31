import os

from dotenv import load_dotenv

load_dotenv()

TWITCH_TOKEN = os.getenv("TWITCH_TOKEN")
CHANNEL = os.getenv("CHANNEL", "akseniyy")
ADMINS = ["wastle_", "akseniyy", "kwasik67"]
DATABASE_URL = os.getenv("DATABASE_URL")
