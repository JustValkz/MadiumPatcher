import brotli
import ctypes
import hashlib
import os
import re
import struct
import subprocess
from ctypes import wintypes

VERSION = "1.2"
CREDIT = "Made by valkz (inspiration by cloudy)"
PATCH_MARK = b"__VALKZ_PATCH_V2__"

# Patches Madium.exe only. Never downloads Madium or client files.
# When you drop in a new Madium.exe, Patch backs that file up and wraps it.
LE_WRAPPER = (
    b"function le(o,e={},t){"
    b"var _i=window.__TAURI_INTERNALS__.invoke;"
    b'if(o==="' + PATCH_MARK + b'")return true;'
    b'if(o==="check_license"||o==="redeem_key"||o==="checkLicense"||o==="redeemKey")'
    b'return {"valid":true,"reason":null,"expires_at":null,"has_token":true};'
    b'if(o==="validate_roblox_version"||o==="check_roblox_compatibility"'
    b'||o==="check_version_compatibility"||o==="is_version_compatible")return true;'
    b'if(o==="check_madium_update"||o==="check_update")return _i(o,e,t).then(function(r){'
    b"if(r&&typeof r===\"object\"){r.update_available=false;r.roblox_compatible=true;"
    b"r.files_match=true;r.version_compatible=true;r.valid=true;r.patched=true;r.issue=null}"
    b"return r});"
    b'if(o==="inspect_roblox_install"||o==="detect_roblox_install")return _i(o,e,t).then(function(r){'
    b"if(r&&typeof r===\"object\"){r.valid=true;r.patched=true;r.issue=null;r.files_match=true;"
    b"r.compatible=true;r.version_match=true;r.is_compatible=true;"
    b"if(r.version)r.supported_roblox_version=r.version;"
    b"if(r.files)r.files=r.files.map(function(f){f.installed=true;return f})}"
    b"return r});"
    b"return _i(o,e,t)}"
)


def enable_ansi():
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def c(code, text):
    return f"\033[{code}m{text}\033[0m"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    clear_screen()
    print()
    print(c("95", "  ╔════════════════════════════════════════════╗"))
    print(c("95", "  ║") + c("97", "           MADIUM PATCHER") + c("95", "                ║"))
    print(c("95", "  ║") + c("90", f"                 v{VERSION}") + c("95", "                    ║"))
    print(c("95", "  ╚════════════════════════════════════════════╝"))
    print()


def print_status(message, status="INFO"):
    colors = {"INFO": "94", "SUCCESS": "92", "WARNING": "93", "ERROR": "91"}
    print(f"\033[{colors.get(status, '0')}m[{status}]\033[0m {message}")


def show_file_picker():
    try:
        BIF_EDITBOX = 0x0010
        BIF_NEWDIALOGSTYLE = 0x0040
        shell32 = ctypes.windll.shell32
        ole32 = ctypes.windll.ole32
        lp_buffer = ctypes.create_unicode_buffer(1024)

        class BROWSEINFO(ctypes.Structure):
            _fields_ = [
                ("hwndOwner", wintypes.HWND),
                ("pidlRoot", ctypes.c_void_p),
                ("pszDisplayName", ctypes.c_wchar_p),
                ("lpszTitle", ctypes.c_wchar_p),
                ("ulFlags", ctypes.c_uint),
                ("lpfn", ctypes.c_void_p),
                ("lParam", ctypes.c_void_p),
                ("iImage", ctypes.c_int),
            ]

        info = BROWSEINFO()
        info.pszDisplayName = lp_buffer
        info.lpszTitle = "Select the folder that contains Madium.exe"
        info.ulFlags = BIF_EDITBOX | BIF_NEWDIALOGSTYLE
        result = shell32.SHBrowseForFolderW(ctypes.byref(info))
        if not result:
            return None
        ole32.CoTaskMemFree(result)
        folder = lp_buffer.value
        if not folder:
            return None
        direct = os.path.join(folder, "Madium.exe")
        if os.path.exists(direct):
            return direct
        for name in os.listdir(folder):
            if name.lower() == "madium.exe":
                return os.path.join(folder, name)
        return None
    except Exception:
        return None


def get_madium_path():
    default_path = os.path.join(
        os.path.expanduser("~"), "AppData", "Local", "Madium", "Bin", "Madium.exe"
    )
    if os.path.exists(default_path):
        return default_path

    print("Madium.exe was not found in the default location.")
    print("  [1] Browse")
    print("  [2] Enter path")
    print()
    while True:
        choice = input("Select (1-2): ").strip()
        if choice == "1":
            path = show_file_picker()
            if path and os.path.exists(path):
                return path
            print_status("No Madium.exe in that folder.", "WARNING")
        elif choice == "2":
            path = input("Path: ").strip().strip('"')
            if os.path.exists(path) and path.lower().endswith(".exe"):
                return path
            print_status("Invalid path.", "ERROR")


def is_madium_running():
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Madium.exe"],
            capture_output=True,
            text=True,
            shell=True,
        )
        return "Madium.exe" in result.stdout
    except Exception:
        return False


def kill_madium():
    try:
        if is_madium_running():
            subprocess.run(
                ["taskkill", "/F", "/IM", "Madium.exe"],
                capture_output=True,
                shell=True,
            )
            return True
        return False
    except Exception:
        return False


def launch_madium(path):
    try:
        if is_madium_running():
            print_status("Already running.", "WARNING")
            return False
        subprocess.Popen([path], shell=True)
        print_status("Launched.", "SUCCESS")
        return True
    except Exception as exc:
        print_status(f"Failed: {exc}", "ERROR")
        return False


def pe_info(data):
    e = struct.unpack_from("<I", data, 0x3C)[0]
    n = struct.unpack_from("<H", data, e + 6)[0]
    o = struct.unpack_from("<H", data, e + 20)[0]
    p = e + 24
    m = struct.unpack_from("<H", data, p)[0]
    b = struct.unpack_from("<Q" if m == 0x20B else "<I", data, p + (0x18 if m == 0x20B else 0x1C))[0]
    s = p + o
    secs = []
    for i in range(n):
        off = s + i * 40
        secs.append((
            b + struct.unpack_from("<I", data, off + 12)[0],
            struct.unpack_from("<I", data, off + 20)[0],
            max(
                struct.unpack_from("<I", data, off + 8)[0],
                struct.unpack_from("<I", data, off + 16)[0],
            ),
        ))
    return b, secs


def va_to_off(v, secs):
    for start, raw, size in secs:
        if start <= v < start + size:
            return raw + (v - start)
    return None


def off_to_va(o, secs):
    for start, raw, size in secs:
        if raw <= o < raw + size:
            return start + (o - raw)
    return None


def extract_chunk(data, path, secs):
    try:
        pb = path.encode("utf-8")
        pi = data.find(pb)
        if pi < 0:
            return None, None, None
        pv = off_to_va(pi, secs)
        if pv is None:
            return None, None, None
        ep = struct.pack("<QQ", pv, len(pb))
        eo = data.find(ep)
        if eo < 0:
            return None, None, None
        dp = struct.unpack_from("<Q", data, eo + 16)[0]
        dl = struct.unpack_from("<Q", data, eo + 24)[0]
        bo = va_to_off(dp, secs)
        if bo is None:
            return None, None, None
        blob = bytes(data[bo:bo + dl])
        return brotli.decompress(blob), eo, bo
    except Exception:
        return None, None, None


def find_js_paths(data):
    paths = set()
    for pattern in (
        rb"/_app/immutable/chunks/[^/\x00]+\.js",
        rb"/_app/immutable/entry/[^/\x00]+\.js",
        rb"/_app/immutable/nodes/[^/\x00]+\.js",
        rb"/_app/immutable/assets/[^/\x00]+\.js",
        rb"/_app/immutable/[^/\x00]+\.js",
        rb"/assets/[^/\x00]+\.js",
    ):
        paths.update(m.decode("utf-8", "ignore") for m in re.findall(pattern, data))
    return paths


def find_invoke_chunk(data, secs):
    best = None
    best_score = -1
    for path in find_js_paths(data):
        js, _, _ = extract_chunk(data, path, secs)
        if not js:
            continue
        score = 0
        if b"function le(" in js or b"const le=" in js or b"const le =" in js:
            score += 80
        if b"__TAURI_INTERNALS__.invoke" in js:
            score += 40
        if b"check_license" in js or b"redeem_key" in js:
            score += 100
        if b"inspect_roblox_install" in js or b"detect_roblox_install" in js:
            score += 80
        if b"patch_roblox_install" in js:
            score += 40
        if score > best_score:
            best_score = score
            best = path
    return best


def find_function_span(js, start_pat):
    match = re.search(start_pat, js)
    if not match:
        return None
    start = match.start()
    depth = 1
    pos = match.end()
    while pos < len(js) and depth > 0:
        ch = js[pos:pos + 1]
        if ch == b"{":
            depth += 1
        elif ch == b"}":
            depth -= 1
        pos += 1
    if depth != 0:
        return None
    return start, pos


def replace_le(js):
    steps = []
    span = find_function_span(js, rb"function le\s*\([^)]*\)\s*\{")
    if span:
        start, end = span
        js = js[:start] + LE_WRAPPER + js[end:]
        steps.append("function-le")
        return js, steps

    const_pat = re.compile(rb"const\s+le\s*=\s*", re.DOTALL)
    match = const_pat.search(js)
    if match:
        end = js.find(b";", match.end())
        if end != -1:
            js = js[:match.start()] + b"const le = " + LE_WRAPPER + js[end + 1:]
            steps.append("const-le")
            return js, steps

    invoke_wrap = re.compile(
        rb"function\s+\w+\s*\([^)]*\)\s*\{\s*return\s+window\.__TAURI_INTERNALS__\.invoke\([^)]*\)\s*\}",
        re.DOTALL,
    )
    match = invoke_wrap.search(js)
    if match:
        js = js[:match.start()] + LE_WRAPPER + js[match.end():]
        steps.append("invoke-wrapper")
        return js, steps

    return None, []


def is_current_patch(js):
    return PATCH_MARK in js and b"r.patched=true" in js and b"f.installed=true" in js


def js_looks_patched(js):
    return PATCH_MARK in js or b'if(o==="check_license"||o==="redeem_key"' in js


def write_chunk(data, js, entry, blob, path):
    compressed = brotli.compress(js, quality=11)
    slot = struct.unpack_from("<Q", data, entry + 24)[0]
    if len(compressed) > slot:
        for quality in (10, 9, 7, 5, 3, 1):
            compressed = brotli.compress(js, quality=quality)
            if len(compressed) <= slot:
                break
        else:
            return False, "recompressed larger than slot"
    data[blob:blob + len(compressed)] = compressed
    struct.pack_into("<Q", data, entry + 24, len(compressed))
    with open(path, "wb") as handle:
        handle.write(data)
    return True, "ok"


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def save_backup(path, data):
    with open(path + ".bak", "wb") as handle:
        handle.write(bytes(data))


def do_patch(path, force=False):
    try:
        with open(path, "rb") as handle:
            data = bytearray(handle.read())

        bak = path + ".bak"
        current_patched = js_looks_patched(bytes(data))

        # New Madium.exe dropped in (unpatched) — always keep that as the backup.
        # Never restore an old .bak over a freshly replaced exe.
        if not current_patched:
            save_backup(path, data)
        elif force and os.path.exists(bak):
            with open(bak, "rb") as handle:
                bak_data = handle.read()
            if not js_looks_patched(bak_data):
                data = bytearray(bak_data)
            else:
                return False, "backup is already patched; replace Madium.exe with a fresh download first"
        elif not force:
            _, secs = pe_info(data)
            chunk = find_invoke_chunk(data, secs)
            if chunk:
                js, _, _ = extract_chunk(bytes(data), chunk, secs)
                if js is not None and is_current_patch(js):
                    return True, "already patched"

        _, secs = pe_info(data)
        chunk = find_invoke_chunk(data, secs)
        if not chunk:
            return False, "no invoke chunk found (this Madium build may use a new layout)"
        js, entry, blob = extract_chunk(bytes(data), chunk, secs)
        if js is None:
            return False, "chunk extraction failed"

        if is_current_patch(js) and not force:
            return True, "already patched"

        replaced, steps = replace_le(js)
        if replaced is None:
            return False, "could not find invoke wrapper in this build"
        js = replaced

        ok, msg = write_chunk(data, js, entry, blob, path)
        if not ok:
            return False, msg
        return True, "applied (" + ", ".join(steps) + ")"
    except Exception as exc:
        return False, f"error: {exc}"


def restore_backup(path):
    backup_path = path + ".bak"
    if not os.path.exists(backup_path):
        print_status("Backup not found.", "ERROR")
        return False
    try:
        kill_madium()
        with open(backup_path, "rb") as handle:
            data = handle.read()
        with open(path, "wb") as handle:
            handle.write(data)
        print_status("Restored original Madium.exe.", "SUCCESS")
        return True
    except Exception:
        print_status("Restore failed.", "ERROR")
        return False


def safe_input(prompt=""):
    try:
        return input(prompt).strip()
    except (EOFError, RuntimeError):
        return "6"


def pause():
    input("\nPress Enter...")


def main():
    enable_ansi()
    try:
        print_header()
        print_status("Looking for Madium.exe...", "INFO")
        path = get_madium_path()
        if not path:
            print_status("No target selected.", "ERROR")
            pause()
            return

        while True:
            print_header()
            print(f"  Target  {c('97', path)}")
            if is_madium_running():
                print(f"  Status  {c('93', 'Madium is running — close it before patching')}")
            else:
                print(f"  Status  {c('92', 'Ready')}")
            print()
            print("  [1] Patch")
            print("  [2] Restore")
            print("  [3] Launch")
            print("  [4] Change target")
            print("  [5] Force re-patch")
            print("  [6] Exit")
            print()
            print(c("90", f"  {CREDIT}"))
            print()

            choice = safe_input("  Select (1-6): ")

            if choice == "1":
                print_header()
                print_status("Patching...", "INFO")
                if is_madium_running():
                    kill_madium()
                ok, msg = do_patch(path)
                print_status(("Success. " if ok else "Failed. ") + msg, "SUCCESS" if ok else "WARNING")
                pause()

            elif choice == "2":
                print_header()
                restore_backup(path)
                pause()

            elif choice == "3":
                print_header()
                launch_madium(path)
                pause()

            elif choice == "4":
                print_header()
                new_path = get_madium_path()
                if new_path:
                    path = new_path
                    print_status("Target changed.", "SUCCESS")
                pause()

            elif choice == "5":
                print_header()
                print_status("Re-applying patch to this Madium.exe...", "INFO")
                if is_madium_running():
                    kill_madium()
                ok, msg = do_patch(path, force=True)
                print_status(("Success. " if ok else "Failed. ") + msg, "SUCCESS" if ok else "WARNING")
                pause()

            elif choice == "6":
                print_header()
                print_status("Bye.", "INFO")
                break
            else:
                print_status("Invalid choice.", "ERROR")
                pause()
    except KeyboardInterrupt:
        print()
        print_status("Exited.", "INFO")
    except Exception:
        print_status("Fatal error.", "ERROR")
        pause()


if __name__ == "__main__":
    main()
