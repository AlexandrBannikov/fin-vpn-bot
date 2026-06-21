import json

import app.services.vpn_service as vpn_service_module
from app.services.vpn_service import VpnService


class FakeXuiRepository:
    def __init__(self):
        self.clients_by_email = {}
        self.bound_clients = []
        self.traffic_clients = []
        self.inbound_settings_clients = []
        self.inbound = {
            "port": 34889,
            "stream_settings": json.dumps({
                "network": "tcp",
                "security": "reality",
                "realitySettings": {
                    "serverNames": ["www.apple.com"],
                    "shortIds": ["abcd1234"],
                    "settings": {
                        "publicKey": "public-key",
                        "fingerprint": "chrome",
                        "spiderX": "/",
                    },
                },
            }),
        }

    def get_client_by_email(self, email: str):
        return self.clients_by_email.get(email)

    def create_client(
        self,
        email: str,
        sub_id: str,
        client_uuid: str,
        password: str,
        auth: str,
        telegram_id: int,
        created_at: int,
    ) -> int:
        client_id = len(self.clients_by_email) + 1

        self.clients_by_email[email] = {
            "id": client_id,
            "email": email,
            "uuid": client_uuid,
            "sub_id": sub_id,
            "password": password,
            "auth": auth,
            "tg_id": telegram_id,
            "created_at": created_at,
            "updated_at": created_at,
        }

        return client_id

    def bind_client_to_inbound(self, client_id: int, created_at: int) -> None:
        self.bound_clients.append({
            "client_id": client_id,
            "created_at": created_at,
        })

    def create_client_traffic(self, email: str) -> None:
        self.traffic_clients.append(email)

    def get_client_by_id(self, client_id: int):
        for client in self.clients_by_email.values():
            if client["id"] == client_id:
                return client

        return None

    def add_client_to_inbound_settings(self, client_row) -> None:
        self.inbound_settings_clients.append(client_row)

    def get_inbound_by_id(self, inbound_id: int):
        return self.inbound


class FakeLoggerService:
    def __init__(self):
        self.events = []

    def info(self, event: str, message: str) -> None:
        self.events.append({
            "event": event,
            "message": message,
        })

    def error(self, event: str, message: str) -> None:
        self.events.append({
            "event": event,
            "message": message,
        })

class FakeVpnServiceWithoutRestart(VpnService):
    def __init__(self, xui_repository):
        super().__init__(xui_repository)
        self.restart_called = False

    def restart_xui(self) -> None:
        self.restart_called = True


def test_make_email():
    repository = FakeXuiRepository()
    service = FakeVpnServiceWithoutRestart(repository)

    assert service.make_email(123456) == "tg_123456"


def test_build_sub_url():
    repository = FakeXuiRepository()
    service = FakeVpnServiceWithoutRestart(repository)

    assert service.build_sub_url("abc123") == "http://31.57.93.95:2096/sub/abc123"


def test_build_sub_url_uses_configured_scheme(monkeypatch):
    repository = FakeXuiRepository()
    service = FakeVpnServiceWithoutRestart(repository)

    monkeypatch.setattr(vpn_service_module, "SUB_SCHEME", "https")

    assert service.build_sub_url("abc123") == "https://31.57.93.95:2096/sub/abc123"


def test_build_vless_url_uses_inbound_settings():
    repository = FakeXuiRepository()
    service = FakeVpnServiceWithoutRestart(repository)
    client = {
        "email": "tg_123456",
        "uuid": "11111111-1111-1111-1111-111111111111",
        "flow": "xtls-rprx-vision",
    }

    url = service.build_vless_url(client)

    assert url.startswith(
        "vless://11111111-1111-1111-1111-111111111111@31.57.93.95:34889?"
    )
    assert "type=tcp" in url
    assert "security=reality" in url
    assert "encryption=none" in url
    assert "flow=xtls-rprx-vision" in url
    assert "pbk=public-key" in url
    assert "fp=chrome" in url
    assert "sni=www.apple.com" in url
    assert "sid=abcd1234" in url
    assert "spx=%2F" in url
    assert url.endswith("#tg_123456")


def test_create_new_client():
    repository = FakeXuiRepository()
    service = FakeVpnServiceWithoutRestart(repository)

    client = service.get_or_create_client(telegram_id=123456)

    assert client["email"] == "tg_123456"
    assert client["created"] is True
    assert client["sub_id"]

    assert "tg_123456" in repository.clients_by_email
    assert len(repository.bound_clients) == 1
    assert repository.traffic_clients == ["tg_123456"]
    assert len(repository.inbound_settings_clients) == 1
    assert service.restart_called is True


def test_existing_client_is_not_duplicated():
    repository = FakeXuiRepository()
    service = FakeVpnServiceWithoutRestart(repository)

    first_client = service.get_or_create_client(telegram_id=123456)
    service.restart_called = False

    second_client = service.get_or_create_client(telegram_id=123456)

    assert second_client["email"] == first_client["email"]
    assert second_client["uuid"] == first_client["uuid"]
    assert second_client["sub_id"] == first_client["sub_id"]
    assert second_client["vless_url"].startswith("vless://")
    assert second_client["created"] is False

    assert len(repository.clients_by_email) == 1
    assert service.restart_called is False

def test_new_client_creation_is_logged():
    repository = FakeXuiRepository()
    logger_service = FakeLoggerService()
    service = FakeVpnServiceWithoutRestart(repository)
    service.logger_service = logger_service

    client = service.get_or_create_client(telegram_id=123456)

    assert client["created"] is True
    assert len(logger_service.events) == 1
    assert logger_service.events[0]["event"] == "VPN_CREATED"
    assert "telegram_id=123456" in logger_service.events[0]["message"]
    assert "email=tg_123456" in logger_service.events[0]["message"]
    assert "sub_id=" in logger_service.events[0]["message"]


def test_restart_xui_can_be_disabled(monkeypatch):
    repository = FakeXuiRepository()
    service = VpnService(repository)
    calls = []

    monkeypatch.setattr(vpn_service_module, "ENABLE_XUI_RESTART", False)
    monkeypatch.setattr(
        vpn_service_module.subprocess,
        "run",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    service.restart_xui()

    assert calls == []


def test_restart_xui_uses_configured_command(monkeypatch):
    repository = FakeXuiRepository()
    service = VpnService(repository)
    calls = []

    monkeypatch.setattr(vpn_service_module, "ENABLE_XUI_RESTART", True)
    monkeypatch.setattr(vpn_service_module, "XUI_RESTART_COMMAND", ["service", "x-ui", "restart"])
    monkeypatch.setattr(
        vpn_service_module.subprocess,
        "run",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    service.restart_xui()

    assert calls == [((["service", "x-ui", "restart"],), {"check": False})]
