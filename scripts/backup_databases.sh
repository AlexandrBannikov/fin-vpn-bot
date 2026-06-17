#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/fin-vpn-bot}"
ENV_FILE="${ENV_FILE:-$APP_DIR/.env}"

read_env_value() {
  local key="$1"

  if [[ ! -f "$ENV_FILE" ]]; then
    return
  fi

  grep -E "^${key}=" "$ENV_FILE" \
    | tail -n 1 \
    | cut -d "=" -f 2- \
    | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//"
}

BOT_DB_PATH="${BOT_DB_PATH:-$(read_env_value BOT_DB_PATH)}"
XUI_DB_PATH="${XUI_DB_PATH:-$(read_env_value XUI_DB_PATH)}"
BACKUP_DIR="${BACKUP_DIR:-$(read_env_value BACKUP_DIR)}"
RETENTION_DAYS="${RETENTION_DAYS:-$(read_env_value RETENTION_DAYS)}"

BOT_DB_PATH="${BOT_DB_PATH:-$APP_DIR/bot.db}"
XUI_DB_PATH="${XUI_DB_PATH:-/etc/x-ui/x-ui.db}"
BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
TARGET_DIR="$BACKUP_DIR/$TIMESTAMP"

mkdir -p "$TARGET_DIR"

copy_db() {
  local source_path="$1"
  local target_name="$2"

  if [[ ! -f "$source_path" ]]; then
    echo "Skip missing database: $source_path"
    return
  fi

  cp "$source_path" "$TARGET_DIR/$target_name"
  chmod 600 "$TARGET_DIR/$target_name"
  echo "Backed up $source_path to $TARGET_DIR/$target_name"
}

copy_db "$BOT_DB_PATH" "bot.db"
copy_db "$XUI_DB_PATH" "x-ui.db"

find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d -mtime +"$RETENTION_DAYS" -exec rm -rf {} +

echo "Backup finished: $TARGET_DIR"
