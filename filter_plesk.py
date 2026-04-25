#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ulp.txt içinden Plesk paneline işaret eden satırları akışla okuyup ayrı bir .txt dosyasına yazar.
Bellek kullanımı düşük; çok büyük dosyalar için uygundur.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

# Plesk varsayılan web arayüzü portları (:84430 gibi yanlış pozitifleri engellemek için sınır)
_PLESK_PORTS = re.compile(
    r":(?:8443|8880)(?=[/?#:]|$)",
    re.IGNORECASE,
)

# Satırda aranan ek göstergeler (küçük harfle karşılaştırılır)
_PLESK_MARKERS = (
    "login_up.php",  # klasik Plesk giriş
    "/smb/",
    "/smb?",
    "/smb#",
    "/smb:",
    "://plesk.",
    "://www.plesk.",
    "/enterprise/control/",
    "/modules/wp-toolkit/",
    "plesk-siteinstaller",
)


def line_is_plesk(line: str) -> bool:
    if _PLESK_PORTS.search(line):
        return True
    low = line.lower()
    return any(m in low for m in _PLESK_MARKERS)


def main() -> int:
    p = argparse.ArgumentParser(description="ulp.txt içinden Plesk ile ilgili satırları ayırır.")
    p.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path(__file__).resolve().parent / "ulp.txt",
        help="Kaynak txt (varsayılan: script ile aynı dizinde ulp.txt)",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "ulp_plesk.txt",
        help="Çıktı txt (varsayılan: ulp_plesk.txt)",
    )
    p.add_argument(
        "--progress-every",
        type=int,
        default=5_000_000,
        metavar="N",
        help="Her N okunan satırda stderr'e ilerleme yaz (0: kapalı)",
    )
    args = p.parse_args()

    src: Path = args.input
    dst: Path = args.output

    if not src.is_file():
        print(f"Hata: kaynak bulunamadı: {src}", file=sys.stderr)
        return 1

    t0 = time.perf_counter()
    read_n = 0
    write_n = 0

    try:
        with src.open("r", encoding="utf-8", errors="replace", newline="") as fin, dst.open(
            "w", encoding="utf-8", newline="\n", errors="replace"
        ) as fout:
            for line in fin:
                read_n += 1
                if line_is_plesk(line):
                    fout.write(line if line.endswith("\n") else line + "\n")
                    write_n += 1
                pe = args.progress_every
                if pe and read_n % pe == 0:
                    elapsed = time.perf_counter() - t0
                    print(
                        f"okunan={read_n:,}  yazilan={write_n:,}  gecen_s={elapsed:.1f}",
                        file=sys.stderr,
                        flush=True,
                    )
    except BrokenPipeError:
        return 0
    except KeyboardInterrupt:
        print("\nKesildi.", file=sys.stderr)
        return 130

    elapsed = time.perf_counter() - t0
    print(
        f"Bitti. okunan={read_n:,}  plesk_satir={write_n:,}  sure_s={elapsed:.1f}\nCikti: {dst}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
