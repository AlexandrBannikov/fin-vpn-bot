import logging
from pathlib import Path


class LoggerService:
    """
    Отдельный сервис для логирования событий проекта.

    Не смешиваем логирование с бизнес-логикой.
    Так проще сопровождать проект и искать ошибки.
    """

    def __init__(self, log_file_path: str = "logs/bot.log"):
        self.log_file_path = Path(log_file_path)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

        logger_name = f"fin_vpn_bot.{self.log_file_path}"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file_path, encoding="utf-8")
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def info(self, event: str, message: str) -> None:
        """
        Записывает информационное событие.
        """
        self.logger.info("%s | %s", event, message)

    def error(self, event: str, message: str) -> None:
        """
        Записывает ошибку.
        """
        self.logger.error("%s | %s", event, message)

