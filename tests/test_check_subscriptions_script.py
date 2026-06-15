import scripts.check_subscriptions as check_subscriptions


class FakeBotRepository:
    pass


class FakeXuiRepository:
    pass


class FakeVpnService:
    instances = []

    def __init__(self, xui_repository):
        self.xui_repository = xui_repository
        self.restart_called = False
        self.__class__.instances.append(self)

    def restart_xui(self):
        self.restart_called = True


class FakeSubscriptionService:
    disabled_user_ids = []

    def __init__(self, bot_repository, xui_repository):
        self.bot_repository = bot_repository
        self.xui_repository = xui_repository

    def disable_expired_users(self):
        return self.disabled_user_ids


def patch_script_dependencies(monkeypatch, disabled_user_ids):
    FakeVpnService.instances = []
    FakeSubscriptionService.disabled_user_ids = disabled_user_ids

    monkeypatch.setattr(check_subscriptions, "BotRepository", FakeBotRepository)
    monkeypatch.setattr(check_subscriptions, "XuiRepository", FakeXuiRepository)
    monkeypatch.setattr(check_subscriptions, "VpnService", FakeVpnService)
    monkeypatch.setattr(
        check_subscriptions,
        "SubscriptionService",
        FakeSubscriptionService,
    )


def test_main_restarts_xui_when_users_were_disabled(monkeypatch, capsys):
    patch_script_dependencies(monkeypatch, [101, 202])

    check_subscriptions.main()

    assert FakeVpnService.instances[0].restart_called is True
    assert capsys.readouterr().out == "Disabled expired users: [101, 202]\n"


def test_main_skips_restart_when_no_users_were_disabled(monkeypatch, capsys):
    patch_script_dependencies(monkeypatch, [])

    check_subscriptions.main()

    assert FakeVpnService.instances[0].restart_called is False
    assert capsys.readouterr().out == "Disabled expired users: []\n"
