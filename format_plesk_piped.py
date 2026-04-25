#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ulp_plesk.txt satırlarını https://host:8443|user|pass veya http://host:8880|user|pass biçimine çevirir.
Çıktı URL'de yalnızca şema + host + Plesk portu bulunur (path atılır).
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

_PORT_IN_AUTH = re.compile(r":(8443|8880)(?=[/:]|$|:)", re.IGNORECASE)
_TAIL_AFTER_PORT = re.compile(r"^(8443|8880)(.*)$", re.IGNORECASE)

_PLESK_HINTS = (
    "login_up.php",
    "/smb/",
    "://plesk.",
    "/enterprise/control/",
    "/modules/wp-toolkit/",
)


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


def _try_host_user_portpath(work: str) -> tuple[str, str, str, str] | None:
    """host:user:8443/path gibi bozuk satırlar."""
    parts = work.split(":", 2)
    if len(parts) != 3:
        return None
    h, u, tail = parts
    m = _TAIL_AFTER_PORT.match(tail)
    if not m:
        return None
    port, after = m.group(1), m.group(2)
    if after == "":
        pw = ""
    elif after[0] == "/":
        pw = after[1:]
    elif after[0] == ":":
        pw = after[1:]
    else:
        return None
    return h, port, u, pw


def _auth_to_base(auth: str) -> str:
    """auth = host:8443 veya host:8880 — şema seç."""
    if auth.lower().endswith(":8880"):
        return "http://" + auth
    return "https://" + auth


def _parse_with_plesk_port(work: str) -> tuple[str, str, str] | None:
    chosen: re.Match | None = None
    for m in _PORT_IN_AUTH.finditer(work):
        if ":" not in work[: m.start()]:
            chosen = m
            break

    if chosen is not None:
        auth = work[: chosen.end()]
        base = _auth_to_base(auth)
        u, p = _split_user_pass_after_port(work, chosen.end())
        return base, u, p

    bad = _try_host_user_portpath(work)
    if bad is not None:
        h, port, u, pw = bad
        auth = f"{h}:{port}"
        return _auth_to_base(auth), u, pw

    m0 = _PORT_IN_AUTH.search(work)
    if m0 is None:
        return None
    h = work.split(":", 1)[0]
    auth = f"{h}:{m0.group(1)}"
    u, p = _split_user_pass_after_port(work, m0.end())
    return _auth_to_base(auth), u, p


def _canonical_no_explicit_port(url_body: str) -> str:
    """8443/8880 yok; Plesk izi veya genel host → https://host:8443."""
    host = url_body.split("/", 1)[0].split(":", 1)[0]
    if not host:
        host = url_body.split("/", 1)[0]
    return f"https://{host}:8443"


def _has_plesk_hint(work: str) -> bool:
    low = work.lower()
    return any(h in low for h in _PLESK_HINTS)


def format_line(raw: str) -> str | None:
    s = raw.strip("\r\n")
    if not s:
        return None

    work = _strip_scheme(s)
    parsed = _parse_with_plesk_port(work)
    if parsed is not None:
        base, user, pw = parsed
        if not user:
            return None
        return f"{base}|{user}|{pw}"

    parts = work.rsplit(":", 2)
    if len(parts) == 3:
        url_body, user, pw = parts
    elif len(parts) == 2:
        url_body, user = parts
        pw = ""
    else:
        if not _has_plesk_hint(work):
            return None
        return f"{_canonical_no_explicit_port(work)}||"

    if not user:
        return None
    if not _has_plesk_hint(url_body) and not _has_plesk_hint(work):
        return None
    base = _canonical_no_explicit_port(url_body)
    return f"{base}|{user}|{pw}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Plesk listesini host:port|user|pass formatına çevirir.")
    ap.add_argument("-i", "--input", type=Path, default=Path(__file__).resolve().parent / "ulp_plesk.txt")
    ap.add_argument("-o", "--output", type=Path, default=Path(__file__).resolve().parent / "ulp_plesk_piped.txt")
    ap.add_argument("--progress-every", type=int, default=50_000)
    args = ap.parse_args()

    if not args.input.is_file():
        print(f"Hata: {args.input} bulunamadı.", file=sys.stderr)
        return 1

    t0 = time.perf_counter()
    n_in = 0
    pe = args.progress_every

    with args.input.open("r", encoding="utf-8", errors="replace", newline="") as fin, args.output.open(
        "w", encoding="utf-8", newline="\n", errors="replace"
    ) as fout:
        for raw in fin:
            n_in += 1
            out = format_line(raw)
            if out is not None:
                fout.write(out + "\n")
            if pe and n_in % pe == 0:
                print(f"okunan={n_in:,}  gecen_s={time.perf_counter() - t0:.1f}", file=sys.stderr, flush=True)

    print(f"Bitti. satir={n_in:,}\nCikti: {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
