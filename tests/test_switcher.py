import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


FAKE_CRED_A = {"token": {"access_token": "token_a"}, "email": "a@gmail.com"}
FAKE_CRED_B = {"token": {"access_token": "token_b"}, "email": "b@gmail.com"}


class TestSwitcher(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.switcher_data = Path(self.tmp) / "AntigravityProfileSwitcher"
        self.written_cred = None

        def mock_write(data):
            self.written_cred = data
            return True

        self.patches = [
            patch("src.profiles.APP_DATA", self.switcher_data),
            patch("src.profiles.PROFILES_DIR", self.switcher_data / "profiles"),
            patch("src.profiles.STATE_FILE", self.switcher_data / "state.json"),
            patch("src.profiles.read_credential", return_value=FAKE_CRED_A),
            patch("src.switcher.read_credential", return_value=FAKE_CRED_A),
            patch("src.switcher.write_credential", side_effect=mock_write),
            patch("src.switcher.close", return_value=True),
            patch("src.switcher.launch", return_value=True),
            patch("src.switcher.is_running", return_value=True),
            patch("src.switcher.time.sleep"),
        ]
        for p in self.patches:
            p.start()

        from src.profiles import ProfileManager
        self.pm = ProfileManager()

        # Save ProfileA as current
        self.pm.save_current("ProfileA")

        # Create ProfileB manually
        profile_b_dir = self.pm.get_profile_dir("ProfileB")
        profile_b_dir.mkdir(parents=True, exist_ok=True)
        (profile_b_dir / "credential.json").write_text(json.dumps(FAKE_CRED_B))
        (profile_b_dir / "meta.json").write_text(json.dumps({"name": "ProfileB", "email": "b@gmail.com", "created": ""}))

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_switch_writes_target_credential(self):
        from src.switcher import switch_profile
        switch_profile(self.pm, "ProfileB")

        self.assertEqual(self.written_cred["email"], "b@gmail.com")
        self.assertEqual(self.pm.active_profile, "ProfileB")

    def test_switch_backs_up_current(self):
        from src.switcher import switch_profile
        switch_profile(self.pm, "ProfileB")

        # ProfileA's credential should be backed up
        backed_up = json.loads((self.pm.get_profile_dir("ProfileA") / "credential.json").read_text())
        self.assertEqual(backed_up["email"], "a@gmail.com")


if __name__ == "__main__":
    unittest.main()
