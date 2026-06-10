import secrets
import time
import uuid

from app.config import SERVER_IP
from app.repositories.invite_repository import InviteRepository
from app.services.vpn_service import VpnService


class InviteService:
    def __init__(
        self,
        invite_repository: InviteRepository,
        vpn_service: VpnService,
    ):
        self.invite_repository = invite_repository
        self.vpn_service = vpn_service

    def now_ts(self) -> int:
        return int(time.time())

    def make_invite_email(self, owner_tg_id: int) -> str:
        unique_part = uuid.uuid4().hex[:8]
        return f"invite_{owner_tg_id}_{unique_part}"

    def create_invite_link(self, owner_tg_id: int) -> dict:
        vpn_email = self.make_invite_email(owner_tg_id)

        client = self.vpn_service.create_client_for_email(
            email=vpn_email,
            telegram_id=owner_tg_id,
        )

        token = secrets.token_urlsafe(24)

        self.invite_repository.save_invite_link(
            owner_tg_id=owner_tg_id,
            vpn_email=vpn_email,
            sub_id=client["sub_id"],
            token=token,
            created_at=self.now_ts(),
        )

        invite_url = f"http://{SERVER_IP}:8081/invite/{token}"

        return {
            "vpn_email": vpn_email,
            "sub_id": client["sub_id"],
            "invite_url": invite_url,
            "token": token,
        }

    def get_invite_by_token(self, token: str):
        return self.invite_repository.get_by_token(token)

    def mark_invite_as_used(self, token: str) -> None:
        self.invite_repository.mark_as_used(
            token=token,
            used_at=self.now_ts(),
        )

    def count_invite_links(self, owner_tg_id: int) -> int:
        return self.invite_repository.count_invite_links(owner_tg_id)

