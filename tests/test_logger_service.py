from app.services.logger_service import LoggerService


def test_logger_service_writes_info_event(tmp_path):
    log_file = tmp_path / "bot.log"

    logger_service = LoggerService(str(log_file))

    logger_service.info(
        event="TEST_EVENT",
        message="Test message",
    )

    content = log_file.read_text(encoding="utf-8")

    assert "TEST_EVENT" in content
    assert "Test message" in content


def test_logger_service_writes_error_event(tmp_path):
    log_file = tmp_path / "bot.log"

    logger_service = LoggerService(str(log_file))

    logger_service.error(
        event="TEST_ERROR",
        message="Test error message",
    )

    content = log_file.read_text(encoding="utf-8")

    assert "TEST_ERROR" in content
    assert "Test error message" in content

