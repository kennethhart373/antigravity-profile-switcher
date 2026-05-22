# Antigravity Profile Switcher

A lightweight Windows tray app for switching between multiple Google Antigravity 2.0 accounts without losing your conversation history.

## Why?

If you use multiple Antigravity accounts (e.g. to get around quota limits), you know the pain of manually logging out, logging back in, and losing your chat context. This tool fixes that.

It works by swapping the auth credential stored in Windows Credential Manager while leaving all your local conversation data untouched — so your history carries over to whichever account you switch to.

## How it works

1. Log into Antigravity with an account
2. Open the Profile Switcher and click **Save Current Account**
3. Repeat for your other accounts
4. When you need to switch, just pick a profile — the app closes Antigravity, swaps the credential, and relaunches it

Your conversations stay intact because the `.pb` files and session data are stored locally and aren't tied to a specific account.

## Installation

Grab the latest `.exe` from [Releases](../../releases) — it's a single standalone file, no Python needed.

Or run from source:

```
pip install -r requirements.txt
python -m src
```

## Building from source

```
pip install -r requirements.txt
pyinstaller AntigravityProfileSwitcher.spec
```

The exe will be in `dist/`.

## Tech stack

- Python + CustomTkinter (GUI)
- pystray (system tray)
- psutil (process management)
- Windows Credential Manager API via ctypes
- PyInstaller (packaging)

## Notes

- Windows only (relies on Windows Credential Manager)
- Antigravity must be installed in the default location (`%LOCALAPPDATA%\Programs\antigravity\`)
- The app minimizes to the system tray when you close the window — right-click the tray icon to switch profiles quickly

## License

MIT
