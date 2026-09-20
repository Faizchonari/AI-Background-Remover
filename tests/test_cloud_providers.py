"""Unit tests for Cloud Providers (Hugging Face, Custom API, Future Provider).

Tests HTTP request generation, response parsing, error handling (401, 403, 429, 500, timeouts),
dimension preservation, and connection testing using mocks.
"""

import base64
import io
import json
import socket
import unittest
from urllib.error import HTTPError, URLError
from unittest.mock import MagicMock, patch
from PIL import Image

from app.processing.backends.providers.huggingface_provider import HuggingFaceProvider
from app.processing.backends.providers.custom_api_provider import CustomAPIProvider
from app.processing.backends.providers.future_provider import FutureProvider


def _create_test_image(width=100, height=80, color=(255, 0, 0)) -> Image.Image:
    """Create a simple test RGB image."""
    return Image.new("RGB", (width, height), color)


def _create_test_rgba_b64(width=100, height=80) -> str:
    """Create a base64-encoded test RGBA image."""
    img = Image.new("RGBA", (width, height), (0, 255, 0, 180))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


class TestHuggingFaceProvider(unittest.TestCase):
    """Test suite for Hugging Face Spaces provider."""

    def setUp(self):
        self.provider = HuggingFaceProvider(
            endpoint_url="https://test-space.hf.space",
            timeout=5
        )

    def test_provider_properties(self):
        """Verify provider metadata and quota."""
        self.assertEqual(self.provider.provider_id, "huggingface")
        self.assertEqual(self.provider.display_name, "Hugging Face Spaces")
        quota = self.provider.get_quota_status()
        self.assertEqual(quota["cost"], "Free (Zero Cost)")

    @patch("app.processing.backends.providers.huggingface_provider.urlopen")
    def test_process_image_success(self, mock_urlopen):
        """Verify successful image processing from Gradio base64 response."""
        test_img = _create_test_image(120, 90)
        b64_rgba = _create_test_rgba_b64(120, 90)

        # Mock Gradio response: {"data": ["data:image/png;base64,..."]}
        resp_data = json.dumps({"data": [f"data:image/png;base64,{b64_rgba}"]}).encode("utf-8")
        mock_resp = MagicMock()
        mock_resp.read.return_value = resp_data
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        rgba, mask = self.provider.process_image(test_img, "birefnet-portrait-cloud")

        self.assertIsInstance(rgba, Image.Image)
        self.assertIsInstance(mask, Image.Image)
        self.assertEqual(rgba.mode, "RGBA")
        self.assertEqual(mask.mode, "L")
        self.assertEqual(rgba.size, (120, 90))
        self.assertEqual(mask.size, (120, 90))

    @patch("app.processing.backends.providers.huggingface_provider.urlopen")
    def test_process_image_preserves_original_dimensions(self, mock_urlopen):
        """Verify output dimensions match input even if remote returned different size."""
        test_img = _create_test_image(200, 150)
        # Remote returns 100x75
        b64_rgba = _create_test_rgba_b64(100, 75)

        resp_data = json.dumps({"data": [f"data:image/png;base64,{b64_rgba}"]}).encode("utf-8")
        mock_resp = MagicMock()
        mock_resp.read.return_value = resp_data
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        rgba, mask = self.provider.process_image(test_img, "birefnet-portrait-cloud")
        self.assertEqual(rgba.size, (200, 150))
        self.assertEqual(mask.size, (200, 150))

    @patch("app.processing.backends.providers.huggingface_provider.urlopen")
    def test_http_401_unauthorized(self, mock_urlopen):
        """Verify HTTP 401 raises PermissionError."""
        mock_urlopen.side_effect = HTTPError(
            url="https://test-space.hf.space/api/predict",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=io.BytesIO(b"")
        )
        test_img = _create_test_image()
        with self.assertRaises(PermissionError):
            self.provider.process_image(test_img, "birefnet-portrait-cloud")

    @patch("app.processing.backends.providers.huggingface_provider.urlopen")
    def test_http_429_rate_limit(self, mock_urlopen):
        """Verify HTTP 429 raises RuntimeError indicating quota/rate limit."""
        mock_urlopen.side_effect = HTTPError(
            url="https://test-space.hf.space/api/predict",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=io.BytesIO(b"")
        )
        test_img = _create_test_image()
        with self.assertRaises(RuntimeError) as ctx:
            self.provider.process_image(test_img, "birefnet-portrait-cloud")
        self.assertIn("quota or rate limit", str(ctx.exception).lower())

    @patch("app.processing.backends.providers.huggingface_provider.urlopen")
    def test_http_500_server_error(self, mock_urlopen):
        """Verify HTTP 500 raises RuntimeError."""
        mock_urlopen.side_effect = HTTPError(
            url="https://test-space.hf.space/api/predict",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=io.BytesIO(b"")
        )
        test_img = _create_test_image()
        with self.assertRaises(RuntimeError) as ctx:
            self.provider.process_image(test_img, "birefnet-portrait-cloud")
        self.assertIn("server error", str(ctx.exception).lower())

    @patch("app.processing.backends.providers.huggingface_provider.urlopen")
    def test_network_timeout(self, mock_urlopen):
        """Verify network timeout raises ConnectionError."""
        mock_urlopen.side_effect = socket.timeout("timed out")
        test_img = _create_test_image()
        with self.assertRaises(ConnectionError):
            self.provider.process_image(test_img, "birefnet-portrait-cloud")

    @patch("app.processing.backends.providers.huggingface_provider.urlopen")
    def test_test_connection_success(self, mock_urlopen):
        """Verify test_connection returns True on 200 OK."""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        ok, msg = self.provider.test_connection()
        self.assertTrue(ok)
        self.assertIn("successfully", msg.lower())

    @patch("app.processing.backends.providers.huggingface_provider.urlopen")
    def test_test_connection_auth_failure(self, mock_urlopen):
        """Verify test_connection returns False on 401."""
        mock_urlopen.side_effect = HTTPError(
            url="https://test-space.hf.space/info",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=io.BytesIO(b"")
        )
        ok, msg = self.provider.test_connection()
        self.assertFalse(ok)
        self.assertIn("authentication failed", msg.lower())


class TestCustomAPIProvider(unittest.TestCase):
    """Test suite for Custom API provider."""

    def setUp(self):
        self.provider = CustomAPIProvider(
            endpoint_url="https://my-api.example.com/api/remove-bg",
            auth_header_type="Bearer",
            token="mysecret"
        )

    def test_provider_properties(self):
        """Verify custom API provider metadata."""
        self.assertEqual(self.provider.provider_id, "custom_api")
        self.assertEqual(self.provider.display_name, "Custom Cloud API")

    @patch("app.processing.backends.providers.custom_api_provider.urlopen")
    def test_process_image_custom_api(self, mock_urlopen):
        """Verify processing via custom REST API."""
        test_img = _create_test_image(80, 60)
        b64_rgba = _create_test_rgba_b64(80, 60)
        raw_rgba = base64.b64decode(b64_rgba)

        # Mock direct PNG response
        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Type": "image/png"}
        mock_resp.read.return_value = raw_rgba
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        rgba, mask = self.provider.process_image(test_img, "custom-model")
        self.assertEqual(rgba.size, (80, 60))
        self.assertEqual(rgba.mode, "RGBA")


class TestFutureProvider(unittest.TestCase):
    """Test suite for Future provider stub."""

    def test_future_provider(self):
        """Verify future provider is marked coming soon and raises error on process."""
        provider = FutureProvider()
        ok, msg = provider.test_connection()
        self.assertFalse(ok)
        with self.assertRaises(RuntimeError):
            provider.process_image(_create_test_image(), "future-model")


if __name__ == "__main__":
    unittest.main()
