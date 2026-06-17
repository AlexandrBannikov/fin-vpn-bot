import sqlite3
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.config import BOT_DB_PATH, INBOUND_ID, XUI_DB_PATH
from app.db import connect_sqlite
from app.repositories.bot_repository import BotRepository
from app.repositories.invite_repository import InviteRepository
from app.repositories.xui_repository import XuiRepository
from app.services.logger_service import LoggerService
from app.services.vpn_service import VpnService

app = FastAPI()

invite_repository = InviteRepository()
bot_repository = BotRepository()
xui_repository = XuiRepository()
vpn_service = VpnService(xui_repository)
logger_service = LoggerService()

RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 20
rate_limit_storage: dict[str, list[int]] = {}


def now_ts() -> int:
    """
    Возвращает текущее Unix-время в секундах.
    """
    return int(time.time())


def get_client_ip(request: Request) -> str:
    """
    Возвращает IP клиента.

    Если сервис стоит за прокси, сначала пробуем взять X-Forwarded-For.
    Если прокси нет — берём request.client.host.
    """
    forwarded_for = request.headers.get("x-forwarded-for")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host

    return "unknown"


def is_rate_limited(ip: str, now: int | None = None) -> bool:
    """
    Проверяет, превысил ли IP лимит запросов.

    Лимит простой:
    - RATE_LIMIT_MAX_REQUESTS запросов;
    - за RATE_LIMIT_WINDOW_SECONDS секунд.
    """
    current_time = now if now is not None else now_ts()
    window_start = current_time - RATE_LIMIT_WINDOW_SECONDS

    request_times = rate_limit_storage.get(ip, [])
    request_times = [
        request_time
        for request_time in request_times
        if request_time >= window_start
    ]

    if len(request_times) >= RATE_LIMIT_MAX_REQUESTS:
        rate_limit_storage[ip] = request_times
        return True

    request_times.append(current_time)
    rate_limit_storage[ip] = request_times

    return False


def render_page(title: str, body: str) -> HTMLResponse:
    html = f"""
    <!doctype html>
    <html lang="ru">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{title}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif;
                background: #f5f5f7;
                padding: 24px;
                color: #111;
            }}
            .card {{
                max-width: 560px;
                margin: 40px auto;
                background: white;
                border-radius: 18px;
                padding: 24px;
                box-shadow: 0 10px 30px rgba(0,0,0,.08);
            }}
            .link {{
                word-break: break-all;
                background: #f0f0f0;
                padding: 14px;
                border-radius: 12px;
                font-size: 15px;
                margin-top: 12px;
            }}
            .button {{
                display: inline-block;
                margin-top: 18px;
                padding: 14px 18px;
                background: #1677ff;
                color: white;
                border-radius: 12px;
                text-decoration: none;
                border: none;
                font-size: 16px;
                cursor: pointer;
            }}
            .muted {{
                color: #666;
                font-size: 14px;
                line-height: 1.45;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            {body}
        </div>
    </body>
    </html>
    """
    return HTMLResponse(html)


def render_rate_limit_page() -> HTMLResponse:
    """
    Формирует страницу при слишком частых запросах.
    """
    return render_page(
        "Слишком много запросов",
        """
        <h2>Слишком много запросов</h2>
        <p>Попробуйте открыть ссылку позже.</p>
        """,
    )


def check_sqlite_database(db_path: str | Path) -> tuple[bool, str | None]:
    path = Path(db_path)

    if not path.exists():
        return False, "file_not_found"

    try:
        with connect_sqlite(path) as conn:
            conn.execute("SELECT 1")
        return True, None
    except sqlite3.Error as exc:
        return False, exc.__class__.__name__


def build_health_report() -> dict:
    bot_db_ok, bot_db_error = check_sqlite_database(BOT_DB_PATH)
    xui_db_ok, xui_db_error = check_sqlite_database(XUI_DB_PATH)
    inbound_ok = False
    inbound_error = None

    if xui_db_ok:
        try:
            inbound_ok = xui_repository.get_inbound_by_id(INBOUND_ID) is not None
            if not inbound_ok:
                inbound_error = "inbound_not_found"
        except Exception as exc:
            xui_db_ok = False
            xui_db_error = exc.__class__.__name__
            inbound_error = "xui_query_failed"

    status = "ok" if bot_db_ok and xui_db_ok and inbound_ok else "error"

    report = {
        "status": status,
        "service": "fin-vpn-web",
        "checks": {
            "bot_db": {
                "status": "ok" if bot_db_ok else "error",
                "error": bot_db_error,
            },
            "xui_db": {
                "status": "ok" if xui_db_ok else "error",
                "error": xui_db_error,
            },
            "xui_inbound": {
                "status": "ok" if inbound_ok else "error",
                "inbound_id": INBOUND_ID,
                "error": inbound_error,
            },
        },
    }

    if status == "ok":
        report["metrics"] = {
            "users": bot_repository.count_users(),
            "vpn_clients": xui_repository.count_clients(),
            "invite_links": invite_repository.count_all_invite_links(),
        }

    return report


@app.get("/invite/{token}", response_class=HTMLResponse)
async def show_invite(token: str, request: Request):
    client_ip = get_client_ip(request)

    if is_rate_limited(client_ip):
        logger_service.error(
            event="RATE_LIMITED",
            message=f"ip={client_ip}, action=show_invite, token={token}",
        )
        return render_rate_limit_page()

    invite = invite_repository.get_by_token(token)

    if not invite:
        return render_page(
            "Ссылка не найдена",
            """
            <h2>Ссылка не найдена</h2>
            <p>Проверьте ссылку или попросите отправить новую.</p>
            """,
        )

    if invite["used_at"]:
        return render_page(
            "Ссылка уже используется",
            """
            <h2>Эта ссылка уже используется</h2>
            <p>Попросите отправить новую пригласительную ссылку.</p>
            """,
        )

    return render_page(
        "Активация VPN",
        f"""
        <h2>VPN-приглашение</h2>
        <p>Нажмите кнопку ниже, чтобы получить VPN-подписку.</p>

        <form method="post" action="/invite/{token}/activate">
            <button class="button" type="submit">Получить VPN-подписку</button>
        </form>

        <p class="muted">
            Ссылка одноразовая. После нажатия кнопки она больше не покажет подписку.
        </p>
        """,
    )


@app.post("/invite/{token}/activate", response_class=HTMLResponse)
async def activate_invite(token: str, request: Request):
    client_ip = get_client_ip(request)

    if is_rate_limited(client_ip):
        logger_service.error(
            event="RATE_LIMITED",
            message=f"ip={client_ip}, action=activate_invite, token={token}",
        )
        return render_rate_limit_page()

    invite = invite_repository.get_by_token(token)

    if not invite:
        return render_page(
            "Ссылка не найдена",
            """
            <h2>Ссылка не найдена</h2>
            <p>Проверьте ссылку или попросите отправить новую.</p>
            """,
        )

    if invite["used_at"]:
        return render_page(
            "Ссылка уже используется",
            """
            <h2>Эта ссылка уже используется</h2>
            <p>Попросите отправить новую пригласительную ссылку.</p>
            """,
        )

    sub_url = vpn_service.build_sub_url(invite["sub_id"])
    invite_repository.mark_as_used(token, now_ts())
    logger_service.info(
        event="INVITE_ACTIVATED",
        message=f"token={token}, sub_id={invite['sub_id']}",
    )

    return render_page(
        "VPN-подписка",
        f"""
        <h2>VPN-подписка готова ✅</h2>
        <p>Скопируйте ссылку ниже и добавьте её в Happ или 2rayTun как подписку.</p>

        <div class="link">{sub_url}</div>

        <p class="muted">
            Эта пригласительная ссылка уже активирована.
            При повторном открытии подписка больше не будет показана.
        </p>
        """,
    )


@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/health")
async def health():
    """
    Проверка FastAPI-сервиса и основных зависимостей.
    """
    report = build_health_report()
    status_code = 200 if report["status"] == "ok" else 503
    return JSONResponse(report, status_code=status_code)


@app.get("/health/xui")
async def health_xui():
    """
    Проверка доступности базы 3X-UI и нужного inbound.
    """
    try:
        inbound = xui_repository.get_inbound_by_id(INBOUND_ID)

        if inbound:
            return {
                "status": "ok",
                "xui": "available",
                "inbound_id": INBOUND_ID,
            }

        return {
            "status": "error",
            "xui": "inbound_not_found",
            "inbound_id": INBOUND_ID,
        }

    except Exception as exc:
        logger_service.error(
            event="HEALTH_XUI_FAILED",
            message=f"inbound_id={INBOUND_ID}, error={exc.__class__.__name__}",
        )
        return {
            "status": "error",
            "xui": "unavailable",
            "inbound_id": INBOUND_ID,
        }


@app.get("/stats")
async def stats():
    """
    Общая статистика проекта.
    """
    return {
        "users": bot_repository.count_users(),
        "referrals": bot_repository.count_all_referrals(),
        "vpn_clients": xui_repository.count_clients(),
        "invite_links": invite_repository.count_all_invite_links(),
    }
