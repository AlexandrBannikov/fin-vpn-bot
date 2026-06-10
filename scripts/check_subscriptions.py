from app.repositories.bot_repository import BotRepository
from app.repositories.xui_repository import XuiRepository
from app.services.subscription_service import SubscriptionService
from app.services.vpn_service import VpnService


def main() -> None:
    """
    Проверяет подписки и отключает пользователей,
    у которых срок подписки уже закончился.
    """
    bot_repository = BotRepository()
    xui_repository = XuiRepository()
    vpn_service = VpnService(xui_repository)

    subscription_service = SubscriptionService(
        bot_repository=bot_repository,
        xui_repository=xui_repository,
    )

    disabled_user_ids = subscription_service.disable_expired_users()

    if disabled_user_ids:
        vpn_service.restart_xui()

    print(f"Disabled expired users: {disabled_user_ids}")


if __name__ == "__main__":
    main()

