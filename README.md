# Madium Patcher

Made by valkz (inspiration by cloudy)

Just patches your local Madium.exe. Doesn't download anything.

1. Close Madium
2. If they updated, swap in the new Madium.exe
3. Run the patcher, hit Patch, then Launch

Default path is `%LOCALAPPDATA%\Madium\Bin\Madium.exe`

```
pip install pyinstaller brotli
python -m PyInstaller --clean madium_patcher.spec
```
