import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import keyring.errors
from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("FLET_APP_STORAGE_DATA", tempfile.gettempdir())

from utils import google_drive


class MemoryKeyring:
    def __init__(self):
        self.keys = {}

    def get_password(self, service, username):
        return self.keys.get((service, username))

    def set_password(self, service, username, password):
        self.keys[service, username] = password

    def delete_password(self, service, username):
        del self.keys[service, username]


class GoogleCredentialTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "google_token.json"
        self.store = MemoryKeyring()
        self.path_patch = patch.object(google_drive, "TOKEN_PATH", str(self.path))
        self.store_patch = patch.object(google_drive, "_keyring", return_value=self.store)
        self.path_patch.start()
        self.store_patch.start()
        self.addCleanup(self.path_patch.stop)
        self.addCleanup(self.store_patch.stop)
        self.creds = Credentials(
            token="test-access-token",
            refresh_token="test-refresh-token",
            token_uri="https://oauth2.googleapis.com/token",
            client_id="test-client",
            client_secret="test-secret",
            scopes=google_drive.SCOPES,
            expiry=(datetime.now(timezone.utc) + timedelta(hours=1)).replace(tzinfo=None),
        )

    def test_round_trip_encrypts_and_disconnect_removes_credentials(self):
        google_drive._save_credentials(self.creds)
        ciphertext = self.path.read_bytes()
        self.assertNotIn(b"test-access-token", ciphertext)
        self.assertNotIn(b"test-refresh-token", ciphertext)
        self.assertTrue(google_drive.is_authenticated())
        self.assertEqual(google_drive._load_credentials().token, self.creds.token)
        google_drive.disconnect()
        self.assertFalse(self.path.exists())
        self.assertFalse(self.store.keys)
        self.assertFalse(google_drive.is_authenticated())

    def test_plaintext_is_migrated_without_losing_credentials(self):
        self.path.write_text(self.creds.to_json(), encoding="utf-8")
        self.assertTrue(google_drive.is_authenticated())
        self.assertNotIn(b"test-refresh-token", self.path.read_bytes())
        self.assertEqual(google_drive._load_credentials().refresh_token, self.creds.refresh_token)

    def test_failed_migration_preserves_plaintext(self):
        original = self.creds.to_json()
        self.path.write_text(original, encoding="utf-8")
        with patch.object(self.store, "set_password", side_effect=keyring.errors.PasswordSetError):
            with self.assertRaises(google_drive.SecureStorageError):
                google_drive._read_credentials()
        self.assertEqual(self.path.read_text(encoding="utf-8"), original)

    @unittest.skipUnless(sys.platform == "win32", "Windows native error")
    def test_windows_store_failure_is_reported(self):
        error = google_drive.NativeStorageError(5, "CredRead", "Access denied")
        with patch.object(self.store, "get_password", side_effect=error):
            with self.assertRaises(google_drive.SecureStorageError):
                google_drive._save_credentials(self.creds)
        self.assertFalse(self.path.exists())

    def test_failed_replace_preserves_plaintext_and_cleans_temp_file(self):
        original = self.creds.to_json()
        self.path.write_text(original, encoding="utf-8")
        with patch.object(google_drive.os, "replace", side_effect=OSError("replace failed")):
            with self.assertRaises(OSError):
                google_drive._read_credentials()
        self.assertEqual(self.path.read_text(encoding="utf-8"), original)
        self.assertEqual(list(Path(self.directory.name).iterdir()), [self.path])

    def test_missing_or_wrong_key_is_reported_without_overwriting(self):
        google_drive._save_credentials(self.creds)
        ciphertext = self.path.read_bytes()
        self.store.keys.clear()
        with self.assertRaises(google_drive.SecureStorageError):
            google_drive._load_credentials()
        with self.assertRaises(google_drive.SecureStorageError):
            google_drive._save_credentials(self.creds)
        self.assertEqual(self.path.read_bytes(), ciphertext)
        self.store.set_password("StoryBoard Google Drive", google_drive._key_name(), Fernet.generate_key().decode())
        with self.assertRaises(google_drive.SecureStorageError):
            google_drive._load_credentials()
        self.assertEqual(self.path.read_bytes(), ciphertext)

    def test_explicit_reauthentication_can_replace_a_lost_key(self):
        google_drive._save_credentials(self.creds)
        self.store.keys.clear()
        google_drive._save_credentials(self.creds, allow_key_creation=True)
        self.assertEqual(google_drive._load_credentials().token, self.creds.token)

    def test_refreshed_credentials_remain_encrypted(self):
        self.creds.expiry = (datetime.now(timezone.utc) - timedelta(hours=1)).replace(tzinfo=None)
        google_drive._save_credentials(self.creds)

        def refresh(creds, request):
            creds.token = "refreshed-access-token"
            creds.expiry = (datetime.now(timezone.utc) + timedelta(hours=1)).replace(tzinfo=None)

        with patch.object(Credentials, "refresh", autospec=True, side_effect=refresh):
            self.assertEqual(google_drive._load_credentials().token, "refreshed-access-token")
        self.assertNotIn(b"refreshed-access-token", self.path.read_bytes())
        self.assertEqual(google_drive._load_credentials().token, "refreshed-access-token")


if __name__ == "__main__":
    unittest.main()
