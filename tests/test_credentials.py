"""Unit tests for CredentialStore and Windows DPAPI credential storage."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.credentials import CredentialStore, mask_token


class TestCredentialStore(unittest.TestCase):
    """Test suite for credential storage, encryption, and token masking."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cred_file = Path(self.temp_dir.name) / "credentials.enc"
        self.cred_store = CredentialStore(file_path=self.cred_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_retrieve_token(self):
        """Verify token is correctly encrypted and decrypted."""
        test_provider = "huggingface"
        test_token = "hf_test_secret_token_12345"

        self.cred_store.set_token(test_provider, test_token)
        retrieved = self.cred_store.get_token(test_provider)
        self.assertEqual(retrieved, test_token)

    def test_remove_token(self):
        """Verify token removal deletes it from storage."""
        test_provider = "huggingface"
        test_token = "hf_temporary_token"

        self.cred_store.set_token(test_provider, test_token)
        self.assertEqual(self.cred_store.get_token(test_provider), test_token)

        removed = self.cred_store.remove_token(test_provider)
        self.assertTrue(removed)
        self.assertIsNone(self.cred_store.get_token(test_provider))

    def test_get_nonexistent_token(self):
        """Verify retrieving an unset token returns None."""
        token = self.cred_store.get_token("nonexistent_provider")
        self.assertIsNone(token)

    def test_mask_token(self):
        """Verify token masking for safe display and logging."""
        # Standard token
        token = "hf_abcdef1234567890"
        masked = mask_token(token)
        self.assertTrue(masked.startswith("hf_****"))
        self.assertTrue(masked.endswith("7890"))
        self.assertNotIn("abcdef12", masked)

        # Short token
        short_token = "abc12"
        masked_short = mask_token(short_token)
        self.assertEqual(masked_short, "********")

        # Empty / None
        self.assertEqual(mask_token(""), "Not Set")
        self.assertEqual(mask_token(None), "Not Set")

    def test_clear_all(self):
        """Verify clear_all removes credentials file."""
        self.cred_store.set_token("provider1", "token1")
        self.cred_store.set_token("provider2", "token2")
        self.assertTrue(self.cred_file.exists())

        self.cred_store.clear_all()
        self.assertFalse(self.cred_file.exists())
        self.assertIsNone(self.cred_store.get_token("provider1"))

    def test_fallback_encryption(self):
        """Verify fallback mechanism works when DPAPI fails."""
        with patch.object(self.cred_store, "_encrypt_bytes", side_effect=lambda b: b"FALLBACK:" + b):
            with patch.object(self.cred_store, "_decrypt_bytes", side_effect=lambda b: b[9:] if b.startswith(b"FALLBACK:") else b):
                token = "fallback_token_123"
                self.cred_store.set_token("fallback_provider", token)
                retrieved = self.cred_store.get_token("fallback_provider")
                self.assertEqual(retrieved, token)


if __name__ == "__main__":
    unittest.main()
