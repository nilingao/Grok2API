import unittest
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.reverse.media_post import MediaPostReverse


class _FakeResponse:
    def __init__(self, status_code: int, text: str = ""):
        self.status_code = status_code
        self.text = text
        self.headers = {}

    def json(self):
        import json

        return json.loads(self.text or "{}")


class _FakeSession:
    async def post(self, *_args, **_kwargs):
        return _FakeResponse(
            404,
            '{"code":5, "message":"Media post not found", "details":[]}',
        )


async def _passthrough_retry(func, *args, **kwargs):
    return await func(*args, **kwargs)


class MediaPost404HandlingTests(unittest.IsolatedAsyncioTestCase):
    async def test_media_post_get_404_is_gracefully_downgraded(self):
        cfg = {
            "proxy.base_proxy_url": "",
            "video.timeout": 5,
            "proxy.browser": "chrome",
        }

        with patch(
            "app.services.reverse.media_post.retry_on_status",
            new=_passthrough_retry,
        ), patch(
            "app.services.reverse.media_post.get_config",
            side_effect=lambda key, default=None: cfg.get(key, default),
        ), patch(
            "app.services.reverse.media_post.build_headers",
            return_value={"Content-Type": "application/json"},
        ):
            response = await MediaPostReverse.get(_FakeSession(), "sso=test", "post-id")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})
