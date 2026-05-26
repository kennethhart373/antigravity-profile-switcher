import json
import os
from datetime import datetime
from pathlib import Path

from src.credman import read_credential, write_credential, encrypt_data, decrypt_data

APP_DATA = Path(os.environ["APPDATA"]) / "AntigravityProfileSwitcher"
PROFILES_DIR = APP_DATA / "profiles"
STATE_FILE = APP_DATA / "state.json"


class ProfileManager:
    def __init__(self):
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        self._state = self._load_state()

    def _load_state(self) -> dict:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return {"active_profile": None}

    def _save_state(self):
        STATE_FILE.write_text(json.dumps(self._state, indent=2), encoding="utf-8")

    @property
    def active_profile(self) -> str | None:
        return self._state.get("active_profile")

    @active_profile.setter
    def active_profile(self, name: str | None):
        self._state["active_profile"] = name
        self._save_state()

    def list_profiles(self) -> list[dict]:
        profiles = []
        for p in PROFILES_DIR.iterdir():
            meta_file = p / "meta.json"
            if meta_file.exists():
                profiles.append(json.loads(meta_file.read_text(encoding="utf-8")))
        return sorted(profiles, key=lambda x: x.get("created", ""))

    def save_current(self, name: str) -> dict:
        """Capture the current Antigravity credential as a named profile."""
        cred_data = read_credential()
        if cred_data is None:
            raise FileNotFoundError("No Antigravity credential found in Windows Credential Manager. Is Antigravity logged in?")

        profile_dir = PROFILES_DIR / name
        profile_dir.mkdir(parents=True, exist_ok=True)

        # Save credential data (encrypted with DPAPI)
        (profile_dir / "credential.bin").write_bytes(encrypt_data(cred_data))

        # Extract email from token data
        email = self._extract_email(cred_data)

        meta = {
            "name": name,
            "email": email,
            "created": datetime.now().isoformat(),
        }
        (profile_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

        self.active_profile = name
        return meta

    def get_profile_dir(self, name: str) -> Path:
        return PROFILES_DIR / name

    def get_profile_credential(self, name: str) -> dict | None:
        cred_file = PROFILES_DIR / name / "credential.bin"
        if cred_file.exists():
            return decrypt_data(cred_file.read_bytes())
        # Fallback: read legacy unencrypted file and migrate
        legacy = PROFILES_DIR / name / "credential.json"
        if legacy.exists():
            data = json.loads(legacy.read_text(encoding="utf-8"))
            cred_file.write_bytes(encrypt_data(data))
            legacy.unlink()
            return data
        return None

    def delete_profile(self, name: str):
        profile_dir = PROFILES_DIR / name
        if profile_dir.exists():
            import shutil
            shutil.rmtree(profile_dir)
        if self.active_profile == name:
            self.active_profile = None

    def _extract_email(self, cred_data: dict) -> str:
        try:
            # Try common structures
            for key in ("email", "user", "account"):
                if key in cred_data:
                    return cred_data[key]
            # Check nested token object
            token = cred_data.get("token", {})
            for key in ("email", "user", "account"):
                if key in token:
                    return token[key]
        except Exception:
            pass
        return "unknown"
