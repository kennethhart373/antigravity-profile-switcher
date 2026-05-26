import json
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


FAKE_CRED = {"token": {"access_token": "ya29.fake", "token_type": "Bearer"}, "email": "test@gmail.com"}


class TestProfileManager(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.switcher_data = Path(self.tmp) / "AntigravityProfileSwitcher"

        self.patches = [
            patch("src.profiles.APP_DATA", self.switcher_data),
            patch("src.profiles.PROFILES_DIR", self.switcher_data / "profiles"),
            patch("src.profiles.STATE_FILE", self.switcher_data / "state.json"),
            patch("src.profiles.read_credential", return_value=FAKE_CRED),
            patch("src.profiles.encrypt_data", side_effect=lambda d: json.dumps(d).encode()),
            patch("src.profiles.decrypt_data", side_effect=lambda b: json.loads(b.decode())),
        ]
        for p in self.patches:
            p.start()

        from src.profiles import ProfileManager
        self.pm = ProfileManager()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_save_and_list(self):
        meta = self.pm.save_current("Account1")
        self.assertEqual(meta["name"], "Account1")
        self.assertEqual(meta["email"], "test@gmail.com")

        profiles = self.pm.list_profiles()
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0]["name"], "Account1")

    def test_active_profile(self):
        self.pm.save_current("A")
        self.assertEqual(self.pm.active_profile, "A")

    def test_delete_profile(self):
        self.pm.save_current("ToDelete")
        self.pm.delete_profile("ToDelete")
        self.assertEqual(len(self.pm.list_profiles()), 0)
        self.assertIsNone(self.pm.active_profile)

    def test_get_profile_credential(self):
        self.pm.save_current("X")
        # Patch decrypt to return the data
        with patch("src.profiles.decrypt_data", return_value=FAKE_CRED):
            cred = self.pm.get_profile_credential("X")
        self.assertEqual(cred["email"], "test@gmail.com")


if __name__ == "__main__":
    unittest.main()
