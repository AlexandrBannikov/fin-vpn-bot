from io import BytesIO

import qrcode
from aiogram.types import BufferedInputFile


class QrService:
    def make_qr(self, text: str) -> BufferedInputFile:
        image = qrcode.make(text)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        return BufferedInputFile(
            buffer.read(),
            filename="vpn_subscription_qr.png",
        )

