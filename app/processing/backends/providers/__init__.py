"""Cloud Providers Package for AI Background Remover."""

from app.processing.backends.providers.base_provider import CloudProvider
from app.processing.backends.providers.huggingface_provider import HuggingFaceProvider
from app.processing.backends.providers.custom_api_provider import CustomAPIProvider
from app.processing.backends.providers.future_provider import FutureProvider

__all__ = [
    "CloudProvider",
    "HuggingFaceProvider",
    "CustomAPIProvider",
    "FutureProvider",
]
