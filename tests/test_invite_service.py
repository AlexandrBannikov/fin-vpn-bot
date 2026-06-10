from app.services.invite_service import InviteService


class FakeInviteRepository:
    def __init__(self):
        self.invites = []

    def save_invite_link(
        self,
        owner_tg_id: int,
        vpn_email: str,
        sub_id: str,
        token: str,
        created_at: int,
    ) -> None:
        self.invites.append({
            "owner_tg_id": owner_tg_id,
            "vpn_email": vpn_email,
            "sub_id": sub_id,
            "token": token,
            "created_at": created_at,
            "used_at": None,
        })

    def get_by_token(self, token: str):
        for invite in self.invites:
            if invite["token"] == token:
                return invite

        return None

    def mark_as_used(self, token: str, used_at: int) -> None:
        for invite in self.invites:
            if invite["token"] == token:
                invite["used_at"] = used_at
                return

    def count_invite_links(self, owner_tg_id: int) -> int:
        return len([
            invite for invite in self.invites
            if invite["owner_tg_id"] == owner_tg_id
        ])


class FakeVpnService:
    def create_client_for_email(self, email: str, telegram_id: int) -> dict:
        return {
            "email": email,
            "uuid": "fake-uuid",
            "sub_id": "fake-sub-id",
            "created": True,
        }


def test_create_invite_link():
    invite_repository = FakeInviteRepository()
    vpn_service = FakeVpnService()
    invite_service = InviteService(invite_repository, vpn_service)

    result = invite_service.create_invite_link(owner_tg_id=123)

    assert result["sub_id"] == "fake-sub-id"
    assert result["invite_url"].startswith("http://31.57.93.95:8081/invite/")
    assert result["token"]
    assert result["vpn_email"].startswith("invite_123_")

    assert len(invite_repository.invites) == 1
    assert invite_repository.invites[0]["owner_tg_id"] == 123
    assert invite_repository.invites[0]["sub_id"] == "fake-sub-id"
    assert invite_repository.invites[0]["token"] == result["token"]
    assert invite_repository.invites[0]["used_at"] is None


def test_count_invite_links():
    invite_repository = FakeInviteRepository()
    vpn_service = FakeVpnService()
    invite_service = InviteService(invite_repository, vpn_service)

    invite_service.create_invite_link(owner_tg_id=123)
    invite_service.create_invite_link(owner_tg_id=123)
    invite_service.create_invite_link(owner_tg_id=456)

    assert invite_service.count_invite_links(owner_tg_id=123) == 2
    assert invite_service.count_invite_links(owner_tg_id=456) == 1


def test_mark_invite_as_used():
    invite_repository = FakeInviteRepository()
    vpn_service = FakeVpnService()
    invite_service = InviteService(invite_repository, vpn_service)

    result = invite_service.create_invite_link(owner_tg_id=123)

    invite_service.mark_invite_as_used(result["token"])

    invite = invite_repository.get_by_token(result["token"])

    assert invite["used_at"] is not None

