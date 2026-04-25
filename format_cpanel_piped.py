#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ulp_cpanel.txt satırlarını https://host:port|user|pass biçimine çevirir.
Çıktı URL'de yalnızca https:// + host + cPanel portu bulunur (path atılır).
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

_PORT_IN_AUTH = re.compile(r":(2082|2083|2086|2087|2095|2096)(?=[/:]|$|:)", re.IGNORECASE)
_TAIL_AFTER_PORT = re.compile(r"^(2082|2083|2086|2087|2095|2096)(.*)$", re.IGNORECASE)


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
    """host:user:2083/path gibi bozuk satırlar (ilk iki ':' ile ayrılmış)."""
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


def _parse_with_cp_port(work: str) -> tuple[str, str, str] | None:
    """
    Satırda cPanel portu varsa (https_base, user, pass) döner.
    https_base = 'https://host:port' (path yok).
    """
    chosen: re.Match | None = None
    for m in _PORT_IN_AUTH.finditer(work):
        if ":" not in work[: m.start()]:
            chosen = m
            break

    if chosen is not None:
        auth = work[: chosen.end()]
        u, p = _split_user_pass_after_port(work, chosen.end())
        return f"https://{auth}", u, p

    bad = _try_host_user_portpath(work)
    if bad is not None:
        h, port, u, pw = bad
        return f"https://{h}:{port}", u, pw

    m0 = _PORT_IN_AUTH.search(work)
    if m0 is None:
        return None
    h = work.split(":", 1)[0]
    auth = f"{h}:{m0.group(1)}"
    u, p = _split_user_pass_after_port(work, m0.end())
    return f"https://{auth}", u, p


def _canonical_https_no_port(url_body: str) -> str:
    """Satırda standart port yoksa (ör. /cpanel/): host + varsayılan 2083."""
    host = url_body.split("/", 1)[0].split(":", 1)[0]
    if not host:
        host = url_body.split("/", 1)[0]
    return f"https://{host}:2083"


def format_line(raw: str) -> str | None:
    s = raw.strip("\r\n")
    if not s:
        return None

    work = _strip_scheme(s)
    parsed = _parse_with_cp_port(work)
    if parsed is not None:
        base, user, pw = parsed
        return f"{base}|{user}|{pw}"

    parts = work.rsplit(":", 2)
    if len(parts) == 3:
        url_body, user, pw = parts
    elif len(parts) == 2:
        url_body, user = parts
        pw = ""
    else:
        return f"{_canonical_https_no_port(work)}||"

    base = _canonical_https_no_port(url_body)
    return f"{base}|{user}|{pw}"


def main() -> int:
    ap = argparse.ArgumentParser(description="cPanel listesini https://host:port|user|pass formatına çevirir.")
    ap.add_argument("-i", "--input", type=Path, default=Path(__file__).resolve().parent / "ulp_cpanel.txt")
    ap.add_argument("-o", "--output", type=Path, default=Path(__file__).resolve().parent / "ulp_cpanel_piped.txt")
    ap.add_argument("--progress-every", type=int, default=100_000)
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
