import json
import secrets
import subprocess
import time
import uuid
from urllib.parse import urlencode, quote

from app.config import (
    ENABLE_XUI_RESTART,
    FLOW,
    INBOUND_ID,
    SERVER_IP,
    SUB_PORT,
    SUB_SCHEME,
    XUI_RESTART_COMMAND,
)
from app.repositories.xui_repository import XuiRepository
from app.services.logger_service import LoggerService


class VpnService:
    def __init__(
        self,
        xui_repository: XuiRepository,
        logger_service: LoggerService | None = None,
    ):
        self.xui_repository = xui_repository
        self.logger_service = logger_service

    def now_ts(self) -> int:
        return int(time.time())

    def make_email(self, telegram_id: int) -> str:
        return f"tg_{telegram_id}"

    def build_sub_url(self, sub_id: str) -> str:
        return f"{SUB_SCHEME}://{SERVER_IP}:{SUB_PORT}/sub/{sub_id}"

    def build_vless_url(self, client_row) -> str:
        inbound = self.xui_repository.get_inbound_by_id(INBOUND_ID)
        stream_settings = self.parse_json_field(inbound, "stream_settings")

        network = stream_settings.get("network", "tcp")
        security = stream_settings.get("security", "none")
        flow = self.row_value(client_row, "flow") or FLOW
        query = {
            "type": network,
            "security": security,
            "encryption": "none",
        }

        if flow:
            query["flow"] = flow

        self.add_transport_params(query, stream_settings, network)
        self.add_security_params(query, stream_settings, security)

        return (
            f"vless://{self.row_value(client_row, 'uuid')}@"
            f"{SERVER_IP}:{self.row_value(inbound, 'port')}"
            f"?{urlencode(query)}"
            f"#{quote(self.row_value(client_row, 'email'))}"
        )

    def parse_json_field(self, row, field_name: str) -> dict:
        raw_value = self.row_value(row, field_name)

        if not raw_value:
            return {}

        try:
            return json.loads(raw_value)
        except json.JSONDecodeError:
            return {}

    def row_value(self, row, field_name: str):
        try:
            return row[field_name]
        except (IndexError, KeyError, TypeError):
            return None

    def add_transport_params(
        self,
        query: dict[str, str],
        stream_settings: dict,
        network: str,
    ) -> None:
        if network == "tcp":
            tcp_settings = stream_settings.get("tcpSettings", {})
            header = tcp_settings.get("header", {})
            header_type = header.get("type")

            if header_type:
                query["headerType"] = header_type

        if network == "ws":
            ws_settings = stream_settings.get("wsSettings", {})
            path = ws_settings.get("path")
            host = ws_settings.get("headers", {}).get("Host")

            if path:
                query["path"] = path
            if host:
                query["host"] = host

        if network == "grpc":
            grpc_settings = stream_settings.get("grpcSettings", {})
            service_name = grpc_settings.get("serviceName")

            if service_name:
                query["serviceName"] = service_name

    def add_security_params(
        self,
        query: dict[str, str],
        stream_settings: dict,
        security: str,
    ) -> None:
        if security == "reality":
            reality_settings = stream_settings.get("realitySettings", {})
            client_settings = reality_settings.get("settings", {})
            public_key = client_settings.get("publicKey")
            fingerprint = client_settings.get("fingerprint")
            server_name = (
                client_settings.get("serverName")
                or self.first_value(reality_settings.get("serverNames"))
            )
            short_id = self.first_value(reality_settings.get("shortIds"))
            spider_x = client_settings.get("spiderX")

            if public_key:
                query["pbk"] = public_key
            if fingerprint:
                query["fp"] = fingerprint
            if server_name:
                query["sni"] = server_name
            if short_id:
                query["sid"] = short_id
            if spider_x:
                query["spx"] = spider_x

        if security == "tls":
            tls_settings = stream_settings.get("tlsSettings", {})
            server_name = tls_settings.get("serverName")
            fingerprint = tls_settings.get("fingerprint")

            if server_name:
                query["sni"] = server_name
            if fingerprint:
                query["fp"] = fingerprint

    def first_value(self, value) -> str | None:
        if isinstance(value, list) and value:
            return value[0]

        if isinstance(value, str) and value:
            return value

        return None

    def get_or_create_client(self, telegram_id: int) -> dict:
        email = self.make_email(telegram_id)
        existing = self.xui_repository.get_client_by_email(email)

        if existing:
            return {
                "email": existing["email"],
                "uuid": existing["uuid"],
                "sub_id": existing["sub_id"],
                "vless_url": self.build_vless_url(existing),
                "created": False,
            }

        client = self.create_client_for_email(
            email=email,
            telegram_id=telegram_id,
        )
        client["created"] = True

        return client

    def create_client_for_email(self, email: str, telegram_id: int) -> dict:
        created_at = self.now_ts()
        sub_id = uuid.uuid4().hex[:16]
        client_uuid = str(uuid.uuid4())
        password = secrets.token_hex(8)
        auth = secrets.token_hex(8)

        client_id = self.xui_repository.create_client(
            email=email,
            sub_id=sub_id,
            client_uuid=client_uuid,
            password=password,
            auth=auth,
            telegram_id=telegram_id,
            created_at=created_at,
        )

        self.xui_repository.bind_client_to_inbound(
            client_id=client_id,
            created_at=created_at,
        )

        self.xui_repository.create_client_traffic(email=email)

        client_row = self.xui_repository.get_client_by_id(client_id)
        self.xui_repository.add_client_to_inbound_settings(client_row)

        self.restart_xui()

        if self.logger_service:
            self.logger_service.info(
                event="VPN_CREATED",
                message=f"telegram_id={telegram_id}, email={email}, sub_id={sub_id}",
            )

        return {
            "email": email,
            "uuid": client_uuid,
            "sub_id": sub_id,
            "vless_url": self.build_vless_url(client_row),
            "created": True,
        }

    def restart_xui(self) -> None:
        if not ENABLE_XUI_RESTART or not XUI_RESTART_COMMAND:
            return

        subprocess.run(XUI_RESTART_COMMAND, check=False)
