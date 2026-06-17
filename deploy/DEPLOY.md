# Deploy fin-vpn-bot

Инструкция рассчитана на Linux-сервер, где уже установлен и настроен 3X-UI.
Примеры используют каталог `/opt/fin-vpn-bot`.

## 1. Подготовить сервер

```bash
sudo apt update
sudo apt install -y git python3 python3-venv curl
```

Проверьте, что база 3X-UI существует:

```bash
sudo test -f /etc/x-ui/x-ui.db
```

## 2. Установить проект

```bash
sudo git clone https://github.com/AlexandrBannikov/fin-vpn-bot.git /opt/fin-vpn-bot
cd /opt/fin-vpn-bot

sudo python3 -m venv venv
sudo ./venv/bin/pip install --upgrade pip
sudo ./venv/bin/pip install -r requirements.txt
```

## 3. Настроить `.env`

```bash
sudo cp .env.example .env
sudo nano .env
```

Минимально проверьте:

```env
BOT_TOKEN=replace_me
ADMIN_ID=228333796
BOT_DB_PATH=/opt/fin-vpn-bot/bot.db
XUI_DB_PATH=/etc/x-ui/x-ui.db
INBOUND_ID=1
SERVER_IP=31.57.93.95
SUB_PORT=2096
INVITE_WEB_SCHEME=http
INVITE_WEB_PORT=8081
ENABLE_XUI_RESTART=true
XUI_RESTART_COMMAND=systemctl restart x-ui
```

Закройте `.env` от чтения посторонними:

```bash
sudo chmod 600 /opt/fin-vpn-bot/.env
```

## 4. Проверить запуск вручную

```bash
cd /opt/fin-vpn-bot
sudo ./venv/bin/python -m compileall app bot.py web.py subscription_daily_job.py scripts
sudo ./venv/bin/python scripts/check_subscriptions.py
```

Проверить web endpoint можно так:

```bash
cd /opt/fin-vpn-bot
sudo ./venv/bin/uvicorn web:app --host 127.0.0.1 --port 8081
curl http://127.0.0.1:8081/health
```

Остановите `uvicorn` после проверки.

## 5. Установить systemd-сервисы

```bash
cd /opt/fin-vpn-bot
sudo cp deploy/systemd/fin-vpn-bot.service /etc/systemd/system/
sudo cp deploy/systemd/fin-vpn-web.service /etc/systemd/system/
sudo cp deploy/systemd/fin-vpn-backup.service /etc/systemd/system/
sudo cp deploy/systemd/fin-vpn-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now fin-vpn-bot fin-vpn-web
sudo systemctl enable --now fin-vpn-backup.timer
```

Проверка статуса:

```bash
sudo systemctl status fin-vpn-bot fin-vpn-web
systemctl list-timers fin-vpn-backup.timer
curl http://127.0.0.1:8081/health
curl http://127.0.0.1:8081/health/xui
```

Логи:

```bash
journalctl -u fin-vpn-bot -f
journalctl -u fin-vpn-web -f
```

## 6. Открыть доступ к invite-web

Если invite-ссылки должны открываться снаружи, настройте firewall и reverse proxy.
Минимальный вариант для прямого порта:

```bash
sudo ufw allow 8081/tcp
```

Более аккуратный вариант — закрыть прямой порт и проксировать через nginx или
Caddy с HTTPS. Тогда в `.env` укажите публичную схему и домен:

```env
INVITE_WEB_SCHEME=https
SERVER_IP=vpn.example.com
INVITE_WEB_PORT=443
```

## 7. Backup и restore

Ручной backup:

```bash
cd /opt/fin-vpn-bot
sudo ./scripts/backup_databases.sh
```

Backup-и сохраняются в `/opt/fin-vpn-bot/backups/<timestamp>/`.
По умолчанию хранятся 14 дней. Это настраивается в `.env`:

```env
BACKUP_DIR=/opt/fin-vpn-bot/backups
RETENTION_DAYS=14
```

Проверить timer:

```bash
systemctl list-timers fin-vpn-backup.timer
journalctl -u fin-vpn-backup.service -n 50
```

Restore из backup:

```bash
sudo systemctl stop fin-vpn-bot fin-vpn-web
sudo cp /opt/fin-vpn-bot/backups/<timestamp>/bot.db /opt/fin-vpn-bot/bot.db
sudo cp /opt/fin-vpn-bot/backups/<timestamp>/x-ui.db /etc/x-ui/x-ui.db
sudo chmod 600 /opt/fin-vpn-bot/bot.db /etc/x-ui/x-ui.db
sudo systemctl restart x-ui
sudo systemctl start fin-vpn-bot fin-vpn-web
```

После восстановления проверьте:

```bash
curl http://127.0.0.1:8081/health
curl http://127.0.0.1:8081/health/xui
sudo systemctl status fin-vpn-bot fin-vpn-web
```

## 8. Обновление проекта

Перед обновлением сделайте backup баз:

```bash
sudo systemctl stop fin-vpn-bot fin-vpn-web
cd /opt/fin-vpn-bot
sudo ./scripts/backup_databases.sh
```

Обновите код и зависимости:

```bash
sudo git pull
sudo ./venv/bin/pip install -r requirements.txt
sudo ./venv/bin/python -m compileall app bot.py web.py subscription_daily_job.py scripts
sudo systemctl start fin-vpn-bot fin-vpn-web
```

Проверьте:

```bash
sudo systemctl status fin-vpn-bot fin-vpn-web
curl http://127.0.0.1:8081/health
```

## 9. Быстрый rollback

Если обновление сломалось:

```bash
cd /opt/fin-vpn-bot
sudo git log --oneline -5
sudo git checkout <previous_commit_sha>
sudo ./venv/bin/pip install -r requirements.txt
sudo systemctl restart fin-vpn-bot fin-vpn-web
```

Если проблема в данных, восстановите последние backup-файлы баз перед запуском.
