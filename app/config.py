import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 228333796

XUI_DB_PATH = "/etc/x-ui/x-ui.db"
BOT_DB_PATH = "/opt/fin-vpn-bot/bot.db"

INBOUND_ID = 1
SERVER_IP = "31.57.93.95"
SUB_PORT = 2096
FLOW = "xtls-rprx-vision"

