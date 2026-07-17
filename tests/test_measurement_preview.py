import asyncio

from app.routes import measure


class DummyUpload:
    filename = "sample.jpg"

    async def read(self):
        return b"fake-image"


def test_measurement_returns_preview_message_without_calibration():
    result = asyncio.run(measure(DummyUpload()))

    assert result["message"].startswith("Preview mode:")
    assert result["area_cm2"] == 0.0
