from fastapi.testclient import TestClient

import web


class FakeLoggerService:
    def __init__(self):
        self.events = []

    def info(self, event: str, message: str) -> None:
        self.events.append(
            {
                "event": event,
                "message": message,
            }
        )

    def error(self, event: str, message: str) -> None:
        self.events.append(
            {
                "event": event,
                "message": message,
            }
        )


class FakeBotRepository:
    def count_users(self) -> int:
        return 10

    def count_all_referrals(self) -> int:
        return 3


class FakeInviteRepository:
    def __init__(self):
        self.invites = {
            "new-token": {
                "token": "new-token",
                "sub_id": "sub-123",
                "vpn_email": "invite_123",
                "used_at": None,
            },
            "used-token": {
                "token": "used-token",
                "sub_id": "sub-456",
                "vpn_email": "invite_456",
                "used_at": 123456789,
            },
        }

    def count_all_invite_links(self) -> int:
        return 5

    def get_by_token(self, token: str):
        return self.invites.get(token)

    def mark_as_used(self, token: str, used_at: int) -> None:
        self.invites[token]["used_at"] = used_at


class FakeVpnService:
    def build_sub_url(self, sub_id: str) -> str:
        return f"https://example.com/sub/{sub_id}"

    def build_vless_url(self, client_row) -> str:
        return f"vless://uuid@example.com:443?type=tcp#{client_row['email']}"


class FakeXuiRepository:
    def get_client_by_email(self, email: str):
        return {
            "email": email,
            "uuid": "uuid",
            "flow": "xtls-rprx-vision",
        }

    def get_inbound_by_id(self, inbound_id: int):
        return {
            "id": inbound_id,
            "settings": "{}",
        }

    def count_clients(self) -> int:
        return 7


class MissingInboundXuiRepository(FakeXuiRepository):
    def get_inbound_by_id(self, inbound_id: int):
        return None


class BrokenXuiRepository(FakeXuiRepository):
    def get_inbound_by_id(self, inbound_id: int):
        raise RuntimeError("x-ui is unavailable")


def setup_fake_services():
    web.rate_limit_storage.clear()
    web.invite_repository = FakeInviteRepository()
    web.bot_repository = FakeBotRepository()
    web.vpn_service = FakeVpnService()
    web.xui_repository = FakeXuiRepository()
    web.logger_service = FakeLoggerService()
    web.check_sqlite_database = lambda db_path: (True, None)


def test_root_status_ok():
    setup_fake_services()

    client = TestClient(web.app)
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_status_ok():
    setup_fake_services()

    client = TestClient(web.app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "fin-vpn-web",
        "checks": {
            "bot_db": {
                "status": "ok",
                "error": None,
            },
            "xui_db": {
                "status": "ok",
                "error": None,
            },
            "xui_inbound": {
                "status": "ok",
                "inbound_id": web.INBOUND_ID,
                "error": None,
            },
        },
        "metrics": {
            "users": 10,
            "vpn_clients": 7,
            "invite_links": 5,
        },
    }


def test_health_status_returns_error_when_xui_db_is_missing():
    setup_fake_services()
    web.check_sqlite_database = lambda db_path: (
        False,
        "file_not_found",
    ) if str(db_path) == str(web.XUI_DB_PATH) else (True, None)

    client = TestClient(web.app)
    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "error"
    assert response.json()["checks"]["xui_db"] == {
        "status": "error",
        "error": "file_not_found",
    }


def test_health_status_returns_error_when_inbound_is_missing():
    setup_fake_services()
    web.xui_repository = MissingInboundXuiRepository()

    client = TestClient(web.app)
    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["checks"]["xui_inbound"] == {
        "status": "error",
        "inbound_id": web.INBOUND_ID,
        "error": "inbound_not_found",
    }


def test_health_xui_logs_exception_when_repository_fails():
    setup_fake_services()
    web.xui_repository = BrokenXuiRepository()

    client = TestClient(web.app)
    response = client.get("/health/xui")

    assert response.status_code == 200
    assert response.json() == {
        "status": "error",
        "xui": "unavailable",
        "inbound_id": web.INBOUND_ID,
    }
    assert web.logger_service.events == [
        {
            "event": "HEALTH_XUI_FAILED",
            "message": f"inbound_id={web.INBOUND_ID}, error=RuntimeError",
        }
    ]


def test_health_xui_status_ok():
    setup_fake_services()

    client = TestClient(web.app)
    response = client.get("/health/xui")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "xui": "available",
        "inbound_id": web.INBOUND_ID,
    }


def test_stats_status_ok():
    setup_fake_services()

    client = TestClient(web.app)
    response = client.get("/stats")

    assert response.status_code == 200
    assert response.json() == {
        "users": 10,
        "referrals": 3,
        "vpn_clients": 7,
        "invite_links": 5,
    }


def test_invite_page_shows_activation_button():
    setup_fake_services()

    client = TestClient(web.app)
    response = client.get("/invite/new-token")

    assert response.status_code == 200
    assert "VPN-приглашение" in response.text
    assert "Получить VPN-ссылку" in response.text


def test_unknown_invite_token():
    setup_fake_services()

    client = TestClient(web.app)
    response = client.get("/invite/bad-token")

    assert response.status_code == 200
    assert "Ссылка не найдена" in response.text


def test_used_invite_token():
    setup_fake_services()

    client = TestClient(web.app)
    response = client.get("/invite/used-token")

    assert response.status_code == 200
    assert "Эта ссылка уже используется" in response.text


def test_activate_invite_shows_direct_vless_link_and_marks_used():
    setup_fake_services()

    client = TestClient(web.app)
    response = client.post("/invite/new-token/activate")

    assert response.status_code == 200
    assert "VPN-ссылка готова" in response.text
    assert "vless://uuid@example.com:443?type=tcp#invite_123" in response.text
    assert "https://example.com/sub/sub-123" not in response.text
    assert web.invite_repository.invites["new-token"]["used_at"] is not None
    assert web.logger_service.events == [
        {
            "event": "INVITE_ACTIVATED",
            "message": "token=new-token, vpn_email=invite_123",
        }
    ]


def test_activate_invite_second_time_is_blocked():
    setup_fake_services()

    client = TestClient(web.app)

    first_response = client.post("/invite/new-token/activate")
    second_response = client.post("/invite/new-token/activate")

    assert "VPN-ссылка готова" in first_response.text
    assert "Эта ссылка уже используется" in second_response.text


def test_get_client_ip_returns_forwarded_ip():
    setup_fake_services()

    client = TestClient(web.app)
    response = client.get(
        "/invite/new-token",
        headers={"x-forwarded-for": "1.2.3.4, 5.6.7.8"},
    )

    assert response.status_code == 200
    assert "VPN-приглашение" in response.text
    assert "1.2.3.4" in web.rate_limit_storage


def test_rate_limit_blocks_too_many_invite_page_requests():
    setup_fake_services()

    client = TestClient(web.app)

    for _ in range(web.RATE_LIMIT_MAX_REQUESTS):
        response = client.get(
            "/invite/bad-token",
            headers={"x-forwarded-for": "9.9.9.9"},
        )
        assert response.status_code == 200

    blocked_response = client.get(
        "/invite/bad-token",
        headers={"x-forwarded-for": "9.9.9.9"},
    )

    assert blocked_response.status_code == 200
    assert "Слишком много запросов" in blocked_response.text
    assert web.logger_service.events[-1]["event"] == "RATE_LIMITED"
    assert "ip=9.9.9.9" in web.logger_service.events[-1]["message"]


def test_rate_limit_blocks_too_many_activate_requests():
    setup_fake_services()

    client = TestClient(web.app)

    for index in range(web.RATE_LIMIT_MAX_REQUESTS):
        token = f"missing-token-{index}"
        response = client.post(
            f"/invite/{token}/activate",
            headers={"x-forwarded-for": "8.8.8.8"},
        )
        assert response.status_code == 200

    blocked_response = client.post(
        "/invite/another-missing-token/activate",
        headers={"x-forwarded-for": "8.8.8.8"},
    )

    assert blocked_response.status_code == 200
    assert "Слишком много запросов" in blocked_response.text
    assert web.logger_service.events[-1]["event"] == "RATE_LIMITED"
    assert "action=activate_invite" in web.logger_service.events[-1]["message"]


def test_rate_limit_allows_requests_after_window():
    setup_fake_services()

    ip = "7.7.7.7"

    for _ in range(web.RATE_LIMIT_MAX_REQUESTS):
        assert web.is_rate_limited(ip, now=1000) is False

    assert web.is_rate_limited(ip, now=1000) is True
    assert web.is_rate_limited(ip, now=1000 + web.RATE_LIMIT_WINDOW_SECONDS + 1) is False
