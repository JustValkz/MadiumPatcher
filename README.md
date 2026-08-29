# Madium Patcher

Made by valkz (inspiration by cloudy)

Patches `Madium.exe` so setup unlocks on current and newer Madium builds. It finds the Tauri invoke wrapper by content, not by chunk filename, so hashed JS names after an update still work.

## Usage

1. Close Madium
2. Run `madium_patcher.exe`
3. **Patch** (or **Force re-patch** after you replace Madium.exe)
4. **Launch**

Menu:

- **Patch** — backup original if needed, then patch
- **Restore** — put the original `Madium.exe` back
- **Launch** — start the patched exe
- **Change target** — pick a different Madium.exe
- **Force re-patch** — restore from backup, then patch again

Default target: `%LOCALAPPDATA%\Madium\Bin\Madium.exe`

## Build

```powershell
pip install pyinstaller brotli
python -m PyInstaller --clean madium_patcher.spec
```

Output: `dist\madium_patcher.exe`
