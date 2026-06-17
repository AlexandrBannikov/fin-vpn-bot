import secrets
import subprocess
import time
import uuid

from app.config import (
    ENABLE_XUI_RESTART,
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

    def get_or_create_client(self, telegram_id: int) -> dict:
        email = self.make_email(telegram_id)
        existing = self.xui_repository.get_client_by_email(email)

        if existing:
            return {
                "email": existing["email"],
                "uuid": existing["uuid"],
                "sub_id": existing["sub_id"],
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
            "created": True,
        }

    def restart_xui(self) -> None:
        if not ENABLE_XUI_RESTART or not XUI_RESTART_COMMAND:
            return

        subprocess.run(XUI_RESTART_COMMAND, check=False)
