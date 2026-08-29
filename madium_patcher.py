import brotli
import os
import struct
import re
import subprocess
import ctypes
import hashlib
from ctypes import wintypes

VER = "1.4"
MARK = b"__vpatch3__"
DEFAULT = os.path.expanduser("~") + "\\AppData\\Local\\Madium\\Bin\\Madium.exe"
DL_DIR = os.path.expanduser("~") + "\\Downloads"

WRAP = (
    b'function le(o,e={},t){var _i=window.__TAURI_INTERNALS__.invoke;'
    b'if(o==="' + MARK + b'")return true;'
    b'if(o==="check_license"||o==="redeem_key"||o==="checkLicense"||o==="redeemKey")'
    b'return {"valid":true,"reason":null,"expires_at":null,"has_token":true};'
    b'if(o==="validate_roblox_version"||o==="check_roblox_compatibility"'
    b'||o==="check_version_compatibility"||o==="is_version_compatible")return true;'
    b'if(o==="inspect_roblox_install"||o==="detect_roblox_install")return _i(o,e,t).then(function(r){'
    b'if(r&&typeof r==="object"){r.valid=true;r.issue=null}'
    b'return r});return _i(o,e,t)}'
)


def cls():
    os.system("cls" if os.name == "nt" else "clear")


def col(n, s):
    return "\033[%sm%s\033[0m" % (n, s)


def status(msg, kind="INFO"):
    c = {"INFO": "94", "SUCCESS": "92", "WARNING": "93", "ERROR": "91"}.get(kind, "0")
    print("\033[%sm[%s]\033[0m %s" % (c, kind, msg))


def header():
    cls()
    print()
    print(col("95", "  ╔════════════════════════════════════════════╗"))
    print(col("95", "  ║") + col("97", "           MADIUM PATCHER") + col("95", "                ║"))
    print(col("95", "  ║") + col("90", "                 v" + VER) + col("95", "                    ║"))
    print(col("95", "  ╚════════════════════════════════════════════╝"))
    print()


def pick_folder():
    try:
        buf = ctypes.create_unicode_buffer(1024)

        class BI(ctypes.Structure):
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

        bi = BI()
        bi.pszDisplayName = buf
        bi.lpszTitle = "Select Madium.exe"
        bi.ulFlags = 0x0010 | 0x0040
        r = ctypes.windll.shell32.SHBrowseForFolderW(ctypes.byref(bi))
        if not r:
            return None
        ctypes.windll.ole32.CoTaskMemFree(r)
        folder = buf.value
        if not folder:
            return None
        p = os.path.join(folder, "Madium.exe")
        if os.path.exists(p):
            return p
        for f in os.listdir(folder):
            if f.lower() == "madium.exe":
                return os.path.join(folder, f)
    except:
        pass
    return None


def default_exe():
    if os.path.exists(DEFAULT):
        return DEFAULT
    return None


def get_path():
    p = default_exe()
    if p:
        return p
    print("Madium.exe not found.")
    print("[1] Download Madium")
    print("[2] Browse")
    print("[3] Enter path")
    print()
    while True:
        c = input("Select (1-3): ").strip()
        if c == "1":
            p = download_madium()
            if p:
                return p
        elif c == "2":
            p = pick_folder()
            if p and os.path.exists(p):
                return p
        elif c == "3":
            p = input("Path: ").strip().strip('"')
            if os.path.exists(p) and p.lower().endswith(".exe"):
                return p


def download_madium():
    dest = os.path.join(DL_DIR, "Madium.exe")
    urls = [
        "https://cdn.getmadium.me/Madium.exe",
        "https://cdn.getmadium.me/Madium.exe?v=latest",
        "https://cdn.getmadium.me/releases/latest/Madium.exe",
        "https://cdn.getmadium.me/app/latest/Madium.exe",
    ]
    status("Downloading Madium to Downloads...", "INFO")
    os.makedirs(DL_DIR, exist_ok=True)
    for u in urls:
        r = subprocess.run(
            ["curl.exe", "-L", "--fail", "-A", "Mozilla/5.0", "-e", "https://getmadium.me/", "-o", dest, u],
            capture_output=True, text=True,
        )
        if r.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 1000000:
            bin_dir = os.path.dirname(DEFAULT)
            os.makedirs(bin_dir, exist_ok=True)
            try:
                open(DEFAULT, "wb").write(open(dest, "rb").read())
                status("Saved to Downloads and Local\\Madium\\Bin", "SUCCESS")
                return DEFAULT
            except:
                status("Saved to Downloads: " + dest, "SUCCESS")
                return dest
    try:
        os.startfile("https://getmadium.me/")
    except:
        pass
    status("Couldn't grab it automatically, opened getmadium.me", "WARNING")
    return default_exe()


def running():
    try:
        r = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Madium.exe"],
            capture_output=True, text=True, shell=True,
        )
        return "Madium.exe" in r.stdout
    except:
        return False


def kill():
    try:
        if running():
            subprocess.run(["taskkill", "/F", "/IM", "Madium.exe"], capture_output=True, shell=True)
            return True
    except:
        pass
    return False


def launch(p):
    try:
        if running():
            status("Already running!", "WARNING")
            return
        subprocess.Popen([p], shell=True)
        status("Launched!", "SUCCESS")
    except Exception as e:
        status("Failed: %s" % e, "ERROR")


def pe_info(d):
    e = struct.unpack_from("<I", d, 0x3C)[0]
    n = struct.unpack_from("<H", d, e + 6)[0]
    o = struct.unpack_from("<H", d, e + 20)[0]
    p = e + 24
    m = struct.unpack_from("<H", d, p)[0]
    b = struct.unpack_from("<Q" if m == 0x20B else "<I", d, p + (0x18 if m == 0x20B else 0x1C))[0]
    s = p + o
    secs = []
    for i in range(n):
        off = s + i * 40
        secs.append((
            b + struct.unpack_from("<I", d, off + 12)[0],
            struct.unpack_from("<I", d, off + 20)[0],
            max(struct.unpack_from("<I", d, off + 8)[0], struct.unpack_from("<I", d, off + 16)[0]),
        ))
    return b, secs


def va_to_off(v, secs):
    for s, r, sz in secs:
        if s <= v < s + sz:
            return r + (v - s)
    return None


def off_to_va(o, secs):
    for s, r, sz in secs:
        if r <= o < r + sz:
            return s + (o - r)
    return None


def extract(d, p, secs):
    try:
        pb = p.encode("utf-8")
        pi = d.find(pb)
        if pi < 0:
            return None, None, None
        pv = off_to_va(pi, secs)
        if pv is None:
            return None, None, None
        eo = d.find(struct.pack("<QQ", pv, len(pb)))
        if eo < 0:
            return None, None, None
        dp = struct.unpack_from("<Q", d, eo + 16)[0]
        dl = struct.unpack_from("<Q", d, eo + 24)[0]
        bo = va_to_off(dp, secs)
        if bo is None:
            return None, None, None
        return brotli.decompress(bytes(d[bo:bo + dl])), eo, bo
    except:
        return None, None, None


def js_paths(d):
    out = set()
    for pat in (
        rb"/_app/immutable/chunks/[^/\x00]+\.js",
        rb"/_app/immutable/entry/[^/\x00]+\.js",
        rb"/_app/immutable/nodes/[^/\x00]+\.js",
        rb"/_app/immutable/assets/[^/\x00]+\.js",
        rb"/_app/immutable/[^/\x00]+\.js",
        rb"/assets/[^/\x00]+\.js",
    ):
        for m in re.findall(pat, d):
            out.add(m.decode("utf-8", "ignore"))
    return out


def find_chunk(d, secs):
    best = None
    score = -1
    for p in js_paths(d):
        js, _, _ = extract(d, p, secs)
        if not js:
            continue
        s = 0
        if b"function le(" in js or b"const le=" in js or b"const le =" in js:
            s += 80
        if b"__TAURI_INTERNALS__.invoke" in js:
            s += 40
        if b"check_license" in js or b"redeem_key" in js:
            s += 100
        if b"inspect_roblox_install" in js:
            s += 80
        if s > score:
            score = s
            best = p
    return best


def func_span(js, pat):
    m = re.search(pat, js)
    if not m:
        return None
    i = m.start()
    depth = 1
    p = m.end()
    while p < len(js) and depth:
        if js[p:p + 1] == b"{":
            depth += 1
        elif js[p:p + 1] == b"}":
            depth -= 1
        p += 1
    if depth:
        return None
    return i, p


def swap_le(js):
    sp = func_span(js, rb"function le\s*\([^)]*\)\s*\{")
    if sp:
        a, b = sp
        return js[:a] + WRAP + js[b:], "le"

    m = re.search(rb"const\s+le\s*=\s*", js)
    if m:
        end = js.find(b";", m.end())
        if end != -1:
            return js[:m.start()] + b"const le = " + WRAP + js[end + 1:], "const"

    m = re.search(
        rb"function\s+\w+\s*\([^)]*\)\s*\{\s*return\s+window\.__TAURI_INTERNALS__\.invoke\([^)]*\)\s*\}",
        js,
    )
    if m:
        return js[:m.start()] + WRAP + js[m.end():], "invoke"

    return None, None


def already(js):
    return MARK in js or b'if(o==="check_license"||o==="redeem_key"' in js


def file_patched(src):
    try:
        d = open(src, "rb").read() if isinstance(src, str) else src
        _, secs = pe_info(d)
        t = find_chunk(d, secs)
        if not t:
            return False
        js, _, _ = extract(d, t, secs)
        return js is not None and already(js)
    except:
        return False


def write_js(d, js, eo, bo, path):
    nb = brotli.compress(js, quality=11)
    slot = struct.unpack_from("<Q", d, eo + 24)[0]
    if len(nb) > slot:
        for q in (10, 9, 7, 5, 3, 1):
            nb = brotli.compress(js, quality=q)
            if len(nb) <= slot:
                break
        else:
            return False, "too big after compress"
    d[bo:bo + len(nb)] = nb
    struct.pack_into("<Q", d, eo + 24, len(nb))
    open(path, "wb").write(d)
    return True, "ok"


def do_patch(path, force=False):
    try:
        d = bytearray(open(path, "rb").read())
        bak = path + ".bak"
        if not file_patched(bytes(d)):
            open(bak, "wb").write(bytes(d))
        elif force and os.path.exists(bak):
            raw = open(bak, "rb").read()
            if file_patched(raw):
                return False, "bak is already patched, wait for Madium to update itself"
            d = bytearray(raw)
        elif not force:
            _, secs = pe_info(d)
            t = find_chunk(d, secs)
            if t:
                js, _, _ = extract(bytes(d), t, secs)
                if js is not None and already(js):
                    return True, "already patched"

        _, secs = pe_info(d)
        t = find_chunk(d, secs)
        if not t:
            return False, "couldn't find the js chunk"
        js, eo, bo = extract(bytes(d), t, secs)
        if js is None:
            return False, "extract failed"
        if already(js) and not force:
            return True, "already patched"
        js, how = swap_le(js)
        if js is None:
            return False, "no le() to wrap"
        ok, msg = write_js(d, js, eo, bo, path)
        if not ok:
            return False, msg
        return True, "ok (%s)" % how
    except Exception as e:
        return False, str(e)


def restore(path):
    bak = path + ".bak"
    if not os.path.exists(bak):
        status("Backup not found!", "ERROR")
        return
    try:
        kill()
        open(path, "wb").write(open(bak, "rb").read())
        status("Restored!", "SUCCESS")
    except:
        status("Restore failed!", "ERROR")


def ask(s=""):
    try:
        return input(s).strip()
    except:
        return "6"


def wait():
    input("\nPress Enter...")


def main():
    try:
        ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)
    except:
        pass

    try:
        header()
        status("Welcome", "INFO")
        print()
        path = get_path()
        if not path:
            status("Nothing selected", "ERROR")
            wait()
            return

        d0 = default_exe()
        if d0:
            path = d0
        if os.path.exists(path):
            if not file_patched(path):
                status("Found a fresh Madium.exe, patching it...", "INFO")
                if running():
                    kill()
                ok, msg = do_patch(path)
                status(("Success! " if ok else "Failed: ") + msg, "SUCCESS" if ok else "WARNING")
                wait()

        while True:
            d0 = default_exe()
            if d0:
                path = d0
            header()
            print("Target: %s" % path)
            print()
            print("[1] Patch")
            print("[2] Restore")
            print("[3] Launch")
            print("[4] Download Madium")
            print("[5] Change Target")
            print("[6] Exit")
            print()
            print("Made by valkz (inspiration by cloudy)")
            print("-" * 60)
            print()
            if running():
                status("Running - close before patching!", "WARNING")
            else:
                status("Not running", "INFO")
            if os.path.exists(path) and not file_patched(path):
                status("Madium replaced itself - hit Patch", "WARNING")
            print()

            c = ask("Select (1-6): ")
            if c == "1":
                header()
                status("Patching...", "INFO")
                print()
                if running():
                    kill()
                ok, msg = do_patch(path)
                status(("Success! " if ok else "Failed: ") + msg, "SUCCESS" if ok else "WARNING")
                wait()
            elif c == "2":
                header()
                restore(path)
                wait()
            elif c == "3":
                header()
                launch(path)
                wait()
            elif c == "4":
                header()
                p = download_madium()
                if p:
                    path = p
                wait()
            elif c == "5":
                header()
                np = get_path()
                if np:
                    path = np
                    status("Target changed!", "SUCCESS")
                wait()
            elif c == "6":
                header()
                status("Goodbye!", "INFO")
                break
            else:
                status("Invalid!", "ERROR")
                wait()
    except KeyboardInterrupt:
        print()
        status("Exited", "INFO")
    except:
        status("Fatal error!", "ERROR")
        wait()


if __name__ == "__main__":
    main()
