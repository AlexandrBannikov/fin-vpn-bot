from app.services.user_service import UserService


class FakeUser:
    def __init__(self):
        self.id = 123456789
        self.username = "test_user"
        self.first_name = "Test"


class FakeMessage:
    def __init__(self):
        self.from_user = FakeUser()


class FakeBotRepository:
    def __init__(self):
        self.users = {}

    def user_exists(self, telegram_id: int) -> bool:
        return telegram_id in self.users

    def save_user(
        self,
        telegram_id: int,
        username: str,
        first_name: str,
        vpn_email: str,
        referrer_id: int | None,
        created_at: int,
    ) -> None:
        self.users[telegram_id] = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "vpn_email": vpn_email,
            "referrer_id": referrer_id,
            "created_at": created_at,
        }


class FakeVpnService:
    def make_email(self, telegram_id: int) -> str:
        return f"tg_{telegram_id}"


def test_save_new_user():
    repository = FakeBotRepository()
    vpn_service = FakeVpnService()
    user_service = UserService(repository, vpn_service)

    message = FakeMessage()

    user_service.save_user_from_message(message, referrer_id=111)

    assert 123456789 in repository.users
    assert repository.users[123456789]["username"] == "test_user"
    assert repository.users[123456789]["vpn_email"] == "tg_123456789"
    assert repository.users[123456789]["referrer_id"] == 111


def test_do_not_duplicate_existing_user():
    repository = FakeBotRepository()
    vpn_service = FakeVpnService()
    user_service = UserService(repository, vpn_service)

    message = FakeMessage()

    user_service.save_user_from_message(message, referrer_id=111)
    user_service.save_user_from_message(message, referrer_id=222)

    assert len(repository.users) == 1
    assert repository.users[123456789]["referrer_id"] == 111


def test_user_cannot_refer_himself():
    repository = FakeBotRepository()
    vpn_service = FakeVpnService()
    user_service = UserService(repository, vpn_service)

    message = FakeMessage()

    user_service.save_user_from_message(message, referrer_id=123456789)

    assert repository.users[123456789]["referrer_id"] is None

