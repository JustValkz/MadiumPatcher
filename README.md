# Madium Patcher

Made by valkz (inspiration by cloudy)

Patches your local `Madium.exe` only. It never downloads Madium, never replaces Madium.exe from the internet, and never pulls client files from their CDN.

When you get a new Madium build, drop the new `Madium.exe` over the old one, then run **Patch**. The patcher backs up that new file and wraps it. Hashed JS chunk names can change every release — it finds the invoke wrapper by content.

## Usage

1. Close Madium
2. If Madium updated: replace `%LOCALAPPDATA%\Madium\Bin\Madium.exe` with the new exe
3. Run `madium_patcher.exe` → **Patch**
4. **Launch**

Menu:

- **Patch** — backup this exe if it is unpatched, then patch
- **Restore** — put the backed-up original back
- **Launch** — start the patched exe
- **Change target** — pick a different Madium.exe
- **Force re-patch** — re-wrap the current build from its matching backup
- **Exit**

Default target: `%LOCALAPPDATA%\Madium\Bin\Madium.exe`

## Build

```powershell
pip install pyinstaller brotli
python -m PyInstaller --clean madium_patcher.spec
```

Output: `dist\madium_patcher.exe`
