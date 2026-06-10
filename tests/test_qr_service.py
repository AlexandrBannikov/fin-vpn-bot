from aiogram.types import BufferedInputFile

from app.services.qr_service import QrService


def test_make_qr_returns_buffered_input_file():
    """
    Проверяем, что QR-сервис возвращает BufferedInputFile.
    """
    service = QrService()

    result = service.make_qr("https://example.com")

    assert isinstance(result, BufferedInputFile)


def test_make_qr_returns_png_file():
    """
    Проверяем имя создаваемого файла.
    """
    service = QrService()

    result = service.make_qr("https://example.com")

    assert result.filename == "vpn_subscription_qr.png"


def test_make_qr_returns_non_empty_content():
    """
    Проверяем, что PNG реально создан и содержит данные.
    """
    service = QrService()

    result = service.make_qr("https://example.com")

    assert len(result.data) > 0

