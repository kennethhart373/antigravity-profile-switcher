import time

from src.credman import read_credential, write_credential
from src.process import close, launch, is_running
from src.profiles import ProfileManager


def switch_profile(pm: ProfileManager, target_name: str) -> bool:
    """Switch to target profile: close Antigravity, swap credential, restart.

    Conversation data is left untouched so history carries forward.
    Returns True on success.
    """
    target_cred = pm.get_profile_credential(target_name)
    if target_cred is None:
        raise FileNotFoundError(f"Profile '{target_name}' has no saved credential")

    # 1. Back up current credential to active profile (if one is active)
    if pm.active_profile and pm.active_profile != target_name:
        _backup_current(pm)

    # 2. Close Antigravity
    if is_running():
        close()
        time.sleep(1)

    # 3. Write target credential to Windows Credential Manager
    if not write_credential(target_cred):
        raise RuntimeError("Failed to write credential to Windows Credential Manager")

    # 4. Update active profile
    pm.active_profile = target_name

    # 5. Restart Antigravity
    launch()
    return True


def _backup_current(pm: ProfileManager):
    """Save current Antigravity credential back to the active profile's storage."""
    current_cred = read_credential()
    if current_cred:
        profile_dir = pm.get_profile_dir(pm.active_profile)
        profile_dir.mkdir(parents=True, exist_ok=True)
        import json
        (profile_dir / "credential.json").write_text(json.dumps(current_cred, indent=2), encoding="utf-8")
