import os
import shlex
from dotenv import load_dotenv

load_dotenv()


def get_env_str(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def get_env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)

    if raw_value is None or raw_value.strip() == "":
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def get_env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)

    if raw_value is None or raw_value.strip() == "":
        return default

    return raw_value.strip().lower() in ("1", "true", "yes", "on")


BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = get_env_int("ADMIN_ID", 228333796)

XUI_DB_PATH = get_env_str("XUI_DB_PATH", "/etc/x-ui/x-ui.db")
BOT_DB_PATH = get_env_str("BOT_DB_PATH", "/opt/fin-vpn-bot/bot.db")

INBOUND_ID = get_env_int("INBOUND_ID", 1)
SERVER_IP = get_env_str("SERVER_IP", "31.57.93.95")
SUB_SCHEME = get_env_str("SUB_SCHEME", "http")
SUB_PORT = get_env_int("SUB_PORT", 2096)
FLOW = get_env_str("FLOW", "xtls-rprx-vision")

INVITE_WEB_PORT = get_env_int("INVITE_WEB_PORT", 8081)
INVITE_WEB_SCHEME = get_env_str("INVITE_WEB_SCHEME", "http")

ENABLE_XUI_RESTART = get_env_bool("ENABLE_XUI_RESTART", True)
XUI_RESTART_COMMAND = shlex.split(
    get_env_str("XUI_RESTART_COMMAND", "systemctl restart x-ui")
)
