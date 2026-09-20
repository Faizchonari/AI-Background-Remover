"""Custom Cloud API Provider for AI Background Remover.

Allows advanced users to connect to self-hosted or private HTTPS endpoints
running background removal AI models.
"""

import base64
import io
import json
import socket
import time
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from PIL import Image

from app.core.credentials import CredentialStore, mask_token
from app.processing.backends.providers.base_provider import CloudProvider
from app.utils.logger import get_logger

logger = get_logger()


class CustomAPIProvider(CloudProvider):
    """Provider for user-configured custom HTTPS background removal APIs."""

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        auth_header_type: str = "Bearer",
        token: Optional[str] = None,
        timeout: int = 35,
        credential_store: Optional[CredentialStore] = None
    ):
        self.endpoint_url = (endpoint_url or "").rstrip("/")
        self.auth_header_type = auth_header_type
        self._manual_token = token
        self._cred_store = credential_store or CredentialStore()
        self.timeout = timeout
        self._cancel_requested = False

    @property
    def provider_id(self) -> str:
        return "custom_api"

    @property
    def display_name(self) -> str:
        return "Custom Cloud API"

    @property
    def plan_type(self) -> str:
        return "User Configured"

    @property
    def requires_authentication(self) -> bool:
        return bool(self.get_token())

    def get_token(self) -> Optional[str]:
        if self._manual_token:
            return self._manual_token
        return self._cred_store.get_token("custom_api")

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "User-Agent": "AI-Background-Remover-Client/1.2.0",
            "Accept": "image/png, application/json, */*",
            "Content-Type": "application/json",
        }
        token = self.get_token()
        if token:
            if self.auth_header_type.lower() == "bearer":
                headers["Authorization"] = f"Bearer {token}"
            elif self.auth_header_type.lower() == "x-api-key":
                headers["X-API-Key"] = token
            else:
                headers["Authorization"] = f"{self.auth_header_type} {token}"
        return headers

    def test_connection(self) -> tuple[bool, str]:
        if not self.endpoint_url:
            return False, "Custom endpoint URL is not configured."

        if not self.endpoint_url.startswith("https://") and not self.endpoint_url.startswith("http://localhost"):
            return False, "Custom API endpoint must use secure HTTPS."

        token = self.get_token()
        logger.info(f"Testing custom endpoint: {self.endpoint_url} (Token: {mask_token(token)})")

        try:
            req = Request(self.endpoint_url, headers=self._get_headers(), method="GET")
            with urlopen(req, timeout=10) as resp:
                if resp.status in (200, 204, 404, 405):
                    return True, f"Connected to custom endpoint (HTTP {resp.status})!"
        except HTTPError as e:
            if e.code in (401, 403):
                return False, f"Authentication failed (HTTP {e.code}). Please verify your token."
            elif e.code in (404, 405):
                return True, f"Endpoint reachable (HTTP {e.code})."
            return False, f"HTTP error: {e.code} ({e.reason})"
        except Exception as e:
            return False, f"Connection failed: {e}"

        return True, "Custom API endpoint is reachable."

    def get_quota_status(self) -> dict:
        return {
            "provider": self.display_name,
            "plan": self.plan_type,
            "status": "Configured" if self.endpoint_url else "Not Configured",
            "cost": "User Managed",
            "limits": "Determined by self-hosted server.",
            "requires_internet": True,
        }

    def process_image(
        self,
        image: Image.Image,
        model_id: str,
        settings: Optional[dict] = None
    ) -> tuple[Image.Image, Image.Image]:
        if not self.endpoint_url:
            raise ValueError("Custom API endpoint is not configured in Settings.")

        self._cancel_requested = False
        orig_w, orig_h = image.size
        orig_rgb = image.convert("RGB")

        # Encode input image to base64
        buf = io.BytesIO()
        orig_rgb.save(buf, format="PNG")
        buf.seek(0)
        b64_image = base64.b64encode(buf.read()).decode("utf-8")

        payload = json.dumps({"image": b64_image, "format": "PNG"}).encode("utf-8")
        headers = self._get_headers()
        req = Request(self.endpoint_url, data=payload, headers=headers, method="POST")

        t_start = time.time()
        logger.info(f"Sending image ({orig_w}x{orig_h}) to Custom API: {self.endpoint_url}...")

        try:
            with urlopen(req, timeout=self.timeout) as resp:
                content_type = resp.headers.get("Content-Type", "")
                raw_bytes = resp.read()

                if "image" in content_type:
                    rgba_result = Image.open(io.BytesIO(raw_bytes))
                else:
                    data = json.loads(raw_bytes.decode("utf-8"))
                    img_data = data.get("image") or data.get("data", [""])[0]
                    if img_data.startswith("data:"):
                        img_data = img_data.split(",", 1)[1]
                    rgba_result = Image.open(io.BytesIO(base64.b64decode(img_data)))

        except HTTPError as e:
            if e.code in (401, 403):
                raise PermissionError(f"Custom API authentication failed (HTTP {e.code}).")
            elif e.code == 429:
                raise RuntimeError("Custom API rate limit reached.")
            raise RuntimeError(f"Custom API server error (HTTP {e.code}): {e.reason}")
        except Exception as e:
            raise ConnectionError(f"Custom API request failed: {e}")

        if rgba_result.mode != "RGBA":
            rgba_result = rgba_result.convert("RGBA")

        if rgba_result.size != (orig_w, orig_h):
            rgba_result = rgba_result.resize((orig_w, orig_h), Image.Resampling.LANCZOS)

        alpha_mask = rgba_result.split()[3]
        elapsed = time.time() - t_start
        logger.info(f"Custom API processing completed in {elapsed:.2f}s.")
        return rgba_result, alpha_mask

    def cancel(self) -> None:
        self._cancel_requested = True
