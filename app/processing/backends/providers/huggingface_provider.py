"""Hugging Face Cloud Provider for AI Background Remover.

Connects to Hugging Face Spaces (Gradio API or FastAPI endpoint) running BiRefNet
or compatible background removal models.
Guarantees:
- Uses Python standard library (urllib.request) for zero extra dependencies.
- Handles Gradio API (/api/predict, /call/predict) and direct REST (/api/remove-background).
- Gracefully handles rate limits (429), auth failures (401/403), server cold starts (503),
  and network timeouts.
- Never logs API tokens in plain text.
- Strictly preserves original image dimensions and returns lossless transparent PNG.
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


class HuggingFaceProvider(CloudProvider):
    """Cloud provider integrating with Hugging Face Spaces."""

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: int = 35,
        credential_store: Optional[CredentialStore] = None
    ):
        self.endpoint_url = (endpoint_url or "https://faizchonari-birefnet-portrait.hf.space").rstrip("/")
        self._cred_store = credential_store or CredentialStore()
        self._manual_token = token
        self.timeout = timeout
        self._cancel_requested = False

    @property
    def provider_id(self) -> str:
        return "huggingface"

    @property
    def display_name(self) -> str:
        return "Hugging Face Spaces"

    @property
    def plan_type(self) -> str:
        return "Free / Limited"

    @property
    def requires_authentication(self) -> bool:
        return False  # Optional token for public spaces, increases rate limit

    def get_token(self) -> Optional[str]:
        """Retrieve token from manual override or secure credential store."""
        if self._manual_token:
            return self._manual_token
        return self._cred_store.get_token("huggingface")

    def _get_headers(self) -> dict[str, str]:
        """Build request headers with optional Bearer token."""
        headers = {
            "User-Agent": "AI-Background-Remover-Client/1.2.0",
            "Accept": "application/json, image/png, */*",
            "Content-Type": "application/json",
        }
        token = self.get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def test_connection(self) -> tuple[bool, str]:
        """Test reachability of the Hugging Face Space endpoint."""
        token = self.get_token()
        masked = mask_token(token) if token else "None"
        logger.info(f"Testing connection to Hugging Face endpoint: {self.endpoint_url} (Token: {masked})")

        # Validate HTTPS
        if not self.endpoint_url.startswith("https://") and not self.endpoint_url.startswith("http://localhost"):
            return False, "Hugging Face endpoints must use secure HTTPS."

        try:
            # Check root or info endpoint
            info_url = f"{self.endpoint_url}/info"
            req = Request(info_url, headers=self._get_headers(), method="GET")
            with urlopen(req, timeout=12) as response:
                if response.status == 200:
                    return True, "Connected successfully to Hugging Face Space!"
        except HTTPError as e:
            if e.code in (401, 403):
                return False, f"Authentication failed (HTTP {e.code}). Please check your Hugging Face token."
            elif e.code == 429:
                return False, "Rate limit or quota reached on Hugging Face. Please try again later."
            elif e.code == 503:
                return True, "Connected! Note: Space is currently waking up from sleep (ZeroGPU / Cold Start)."
            # If /info is 404, check root URL
            try:
                req_root = Request(self.endpoint_url, headers=self._get_headers(), method="GET")
                with urlopen(req_root, timeout=12) as resp_root:
                    if resp_root.status == 200:
                        return True, "Connected successfully to Hugging Face Space!"
            except Exception:
                pass
            return False, f"HTTP error from server: {e.code} ({e.reason})"
        except (URLError, socket.timeout) as e:
            return False, f"Could not connect to {self.endpoint_url}: {e.reason if hasattr(e, 'reason') else e}"
        except Exception as e:
            return False, f"Connection test failed: {e}"

        return True, "Connected successfully to Hugging Face Space!"

    def get_quota_status(self) -> dict:
        """Return provider quota status."""
        return {
            "provider": self.display_name,
            "plan": self.plan_type,
            "status": "Available",
            "cost": "Free (Zero Cost)",
            "limits": "Standard Hugging Face Space queue and rate limits apply.",
            "requires_internet": True,
        }

    def process_image(
        self,
        image: Image.Image,
        model_id: str,
        settings: Optional[dict] = None
    ) -> tuple[Image.Image, Image.Image]:
        """Send image to Hugging Face Space and receive transparent result."""
        self._cancel_requested = False
        orig_w, orig_h = image.size
        orig_rgb = image.convert("RGB")

        # 1. Encode input image to base64
        buf = io.BytesIO()
        orig_rgb.save(buf, format="PNG")
        buf.seek(0)
        b64_image = base64.b64encode(buf.read()).decode("utf-8")
        data_uri = f"data:image/png;base64,{b64_image}"

        # 2. Try endpoints in order of standard Gradio support:
        # a) /api/predict/ (Gradio 3 & 4 standard predict)
        # b) /api/remove-background (FastAPI direct mount)
        payload = json.dumps({"data": [data_uri]}).encode("utf-8")
        predict_url = f"{self.endpoint_url}/api/predict"

        headers = self._get_headers()
        req = Request(predict_url, data=payload, headers=headers, method="POST")

        if self._cancel_requested:
            raise RuntimeError("Cloud processing cancelled by user.")

        t_start = time.time()
        logger.info(f"Uploading image ({orig_w}x{orig_h}) to Hugging Face Space: {predict_url}...")

        try:
            with urlopen(req, timeout=self.timeout) as response:
                if self._cancel_requested:
                    raise RuntimeError("Cloud processing cancelled by user.")

                resp_bytes = response.read()
                resp_json = json.loads(resp_bytes.decode("utf-8"))

                # Gradio returns {"data": ["data:image/png;base64,..."]}
                out_data = resp_json.get("data")
                if not out_data or not isinstance(out_data, list) or len(out_data) == 0:
                    raise ValueError(f"Malformed response from Hugging Face Space: {resp_json}")

                result_entry = out_data[0]
                if isinstance(result_entry, str) and result_entry.startswith("data:image/"):
                    # Base64 data URI
                    header, b64_content = result_entry.split(",", 1)
                    raw_out_bytes = base64.b64decode(b64_content)
                elif isinstance(result_entry, dict) and "url" in result_entry:
                    # File URL returned by newer Gradio versions
                    file_url = result_entry["url"]
                    if not file_url.startswith("http"):
                        file_url = f"{self.endpoint_url}/{file_url.lstrip('/')}"
                    req_img = Request(file_url, headers=headers, method="GET")
                    with urlopen(req_img, timeout=self.timeout) as img_resp:
                        raw_out_bytes = img_resp.read()
                elif isinstance(result_entry, str) and (result_entry.startswith("http://") or result_entry.startswith("https://")):
                    req_img = Request(result_entry, headers=headers, method="GET")
                    with urlopen(req_img, timeout=self.timeout) as img_resp:
                        raw_out_bytes = img_resp.read()
                else:
                    raise ValueError(f"Unrecognized image data format in response: {type(result_entry)}")

        except HTTPError as e:
            if e.code in (401, 403):
                raise PermissionError(f"Hugging Face authentication failed (HTTP {e.code}). Please check your API token.")
            elif e.code == 429:
                raise RuntimeError(
                    "Cloud processing quota or rate limit has been reached. "
                    "You can continue using Local Processing or try again later."
                )
            elif e.code == 503:
                raise RuntimeError(
                    "Hugging Face Space is currently starting up (ZeroGPU cold start). "
                    "Please wait a moment and try again, or use Local Processing."
                )
            elif e.code >= 500:
                raise RuntimeError(f"Hugging Face server error (HTTP {e.code}): {e.reason}")
            else:
                raise RuntimeError(f"Cloud request failed (HTTP {e.code}): {e.reason}")

        except (URLError, socket.timeout) as e:
            raise ConnectionError(
                f"Network connection failed: {e.reason if hasattr(e, 'reason') else e}. "
                "Please verify your internet connection or switch to Local Processing."
            )

        # 3. Decode returned transparent RGBA image
        try:
            rgba_result = Image.open(io.BytesIO(raw_out_bytes))
            if rgba_result.mode != "RGBA":
                rgba_result = rgba_result.convert("RGBA")
        except Exception as e:
            raise ValueError(f"Failed to decode returned image from cloud provider: {e}")

        # 4. Strictly preserve original dimensions
        if rgba_result.size != (orig_w, orig_h):
            rgba_result = rgba_result.resize((orig_w, orig_h), Image.Resampling.LANCZOS)

        # Extract alpha mask
        alpha_mask = rgba_result.split()[3]

        elapsed = time.time() - t_start
        logger.info(f"Cloud processing completed via Hugging Face in {elapsed:.2f}s ({orig_w}x{orig_h}).")

        return rgba_result, alpha_mask

    def cancel(self) -> None:
        """Cancel ongoing request."""
        self._cancel_requested = True
