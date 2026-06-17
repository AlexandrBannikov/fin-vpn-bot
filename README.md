# fin-vpn-bot

Telegram-бот для выдачи VPN-подписок через 3X-UI. Бот создаёт клиентов в базе
3X-UI, отдаёт пользователю subscription URL и QR-код, ведёт собственную SQLite
базу пользователей, подписок, рефералов и одноразовых invite-ссылок.

## Возможности

- `/start`, `/getvpn`, `/myvpn`, `/apps`, `/help`
- выдача VPN-ссылки и QR-кода
- реферальные ссылки и одноразовые invite-ссылки
- роли `user`, `admin`, `owner`
- админская статистика и health-check
- продление, отключение и включение подписок
- отдельный daily job для предупреждений и истечения подписок

## Требования

- Python 3.11+
- установленный и настроенный 3X-UI
- доступ к SQLite базе 3X-UI, обычно `/etc/x-ui/x-ui.db`
- права на перезапуск сервиса `x-ui`, если включён автоматический restart

Подробный production-deploy описан в `deploy/DEPLOY.md`.

## Быстрый старт

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Заполните `.env` реальным `BOT_TOKEN`, `ADMIN_ID`, `SERVER_IP`, путями к базам и
параметрами inbound.

```bash
python bot.py
```

Для локальной разработки без перезапуска 3X-UI можно поставить:

```env
ENABLE_XUI_RESTART=false
```

## Web invite endpoint

Файл `web.py` поднимает HTTP endpoint для одноразовых invite-ссылок:

```bash
uvicorn web:app --host 0.0.0.0 --port 8081
```

Порт и схема ссылки настраиваются через:

```env
INVITE_WEB_SCHEME=http
INVITE_WEB_PORT=8081
```

## Daily subscription job

Проверка истекающих и просроченных подписок:

```bash
python subscription_daily_job.py
```

## Миграции БД

Схема `bot.db` обновляется идемпотентными миграциями. Перед ручным запуском или
после `git pull` можно явно применить миграции:

```bash
python scripts/migrate.py
```

## systemd

Готовые unit-файлы лежат в `deploy/systemd/` и рассчитаны на установку проекта в
`/opt/fin-vpn-bot`:

- `fin-vpn-bot.service` — Telegram-бот
- `fin-vpn-web.service` — web endpoint для invite-ссылок
- `fin-vpn-backup.timer` — ежедневный backup `bot.db` и `x-ui.db`

Пример установки:

```bash
sudo cp deploy/systemd/fin-vpn-bot.service /etc/systemd/system/
sudo cp deploy/systemd/fin-vpn-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now fin-vpn-bot fin-vpn-web
```

Проверка:

```bash
sudo systemctl status fin-vpn-bot fin-vpn-web
journalctl -u fin-vpn-bot -f
journalctl -u fin-vpn-web -f
curl http://127.0.0.1:8081/health
```

## Проверка

```bash
pip install -r requirements-dev.txt
pytest --cov=app --cov=web --cov=scripts --cov-report=term-missing --cov-fail-under=90
python -m compileall app bot.py web.py subscription_daily_job.py scripts
```

## Важные настройки

Все основные параметры вынесены в `.env`:

- `BOT_TOKEN` — токен Telegram-бота
- `ADMIN_ID` — Telegram ID владельца
- `BOT_DB_PATH` — база самого бота
- `XUI_DB_PATH` — база 3X-UI
- `INBOUND_ID` — inbound в 3X-UI
- `SERVER_IP` — IP/домен сервера для subscription URL
- `SUB_PORT` — порт subscription endpoint 3X-UI
- `FLOW` — flow клиента, например `xtls-rprx-vision`
- `ENABLE_XUI_RESTART` — перезапускать ли `x-ui` после создания клиента
- `XUI_RESTART_COMMAND` — команда перезапуска 3X-UI

Не коммитьте `.env`, базы данных, логи и backup-архивы. Они уже закрыты
`.gitignore`.
