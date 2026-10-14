#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pocbit ULP Checker — private single-pass split of large ulp.txt into categories.

Streams line-by-line (GB-friendly). Each match writes to its category file;
one line may appear in multiple outputs.

Categories: hosting panels, CMS, phpMyAdmin/Adminer (ulp_classify.CATEGORIES).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import TextIO

from colorama import Fore, Style, init
from termcolor import colored

init(autoreset=True)

POCBIT_ULP_VERSION = "1.0.0"
TOOL_TITLE = "Pocbit ULP Checker"
TOOL_TAGLINE = "Private toolkit · panels · CMS · DB admin · GB-scale streaming"

from ulp_classify import (
    CMS_CATEGORIES,
    DEFAULT_CATEGORY_ORDER,
    PANEL_CATEGORIES,
    TOOL_CATEGORIES,
    classify_line,
    expand_category_selection,
)

SCRIPT_DIR = Path(__file__).resolve().parent


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def print_pocbit_banner(*, to_stderr: bool = True) -> None:
    out = sys.stderr if to_stderr else sys.stdout
    print(colored(TOOL_TITLE, "cyan", attrs=["bold"]), file=out, flush=True)
    print(colored(f"  v{POCBIT_ULP_VERSION}  ·  {TOOL_TAGLINE}", "yellow"), file=out, flush=True)
    print(colored("  " + "─" * 52, "blue"), file=out, flush=True)


def _msg_info(text: str) -> None:
    print(colored("● ", "cyan") + Fore.WHITE + text, file=sys.stderr, flush=True)


def _msg_ok(text: str) -> None:
    print(colored("✓ ", "green") + Fore.WHITE + text, file=sys.stderr, flush=True)


def _msg_warn(text: str) -> None:
    print(colored("! ", "yellow", attrs=["bold"]) + Fore.YELLOW + text, file=sys.stderr, flush=True)


def _msg_err(text: str) -> None:
    print(colored("✗ ", "red", attrs=["bold"]) + Fore.RED + text, file=sys.stderr, flush=True)


def _msg_hint(text: str) -> None:
    print(colored("  → ", "magenta") + Style.DIM + text + Style.RESET_ALL, file=sys.stderr, flush=True)


# Periodic flush (Windows Explorer 0 KB) + live terminal output
_FLUSH_EVERY = 256
_live_printed = 0


def _open_out(path: Path) -> TextIO:
    path.parent.mkdir(parents=True, exist_ok=True)
    # line buffering: faster visibility on disk
    return path.open(
        "w",
        encoding="utf-8",
        newline="\n",
        errors="replace",
        buffering=1,
    )


def _write_line(handle: TextIO | None, line: str, *, write_count: list[int]) -> None:
    if handle is None:
        return
    handle.write(line if line.endswith("\n") else line + "\n")
    write_count[0] += 1
    if write_count[0] % _FLUSH_EVERY == 0:
        handle.flush()


def _flush_all(handles: dict[str, TextIO | None]) -> None:
    for h in handles.values():
        if h is not None:
            try:
                h.flush()
            except OSError:
                pass


def _live_print(
    categories: tuple[str, ...],
    line: str,
    *,
    enabled: bool,
    max_lines: int,
    out_stream: TextIO,
) -> None:
    global _live_printed
    if not enabled:
        return
    if max_lines > 0 and _live_printed >= max_lines:
        return
    tags = ",".join(categories)
    text = line.rstrip("\r\n")
    tag_color = "magenta" if "other" in categories else "green"
    prefix = colored(f"[{tags}]", tag_color, attrs=["bold"])
    print(f"{prefix} {Fore.WHITE}{text}", file=out_stream, flush=True)
    _live_printed += 1


def run_split(
    src: Path,
    out_dir: Path,
    *,
    prefix: str,
    categories: tuple[str, ...],
    write_other: bool,
    progress_every: int,
    stats_only: bool,
    live: bool,
    live_max: int,
    live_other: bool,
) -> dict[str, int | float]:
    global _live_printed
    _live_printed = 0
    if not src.is_file():
        raise FileNotFoundError(src)

    handles: dict[str, TextIO | None] = {}
    if not stats_only:
        for cat in categories:
            handles[cat] = _open_out(out_dir / f"{prefix}{cat}.txt")
        if write_other:
            handles["_other"] = _open_out(out_dir / f"{prefix}other.txt")

    counts: dict[str, int] = {c: 0 for c in categories}
    if write_other:
        counts["other"] = 0
    counts["read"] = 0
    counts["matched_any"] = 0
    counts["multi_label"] = 0

    t0 = time.perf_counter()
    flush_counter = [0]
    live_cap_warned = False

    try:
        with src.open("r", encoding="utf-8", errors="replace", newline="") as fin:
            for raw in fin:
                counts["read"] += 1
                line = raw.lstrip("\ufeff").rstrip("\r\n")
                if not line or line.startswith("#"):
                    continue

                matched = classify_line(line, categories)
                if matched:
                    counts["matched_any"] += 1
                    if len(matched) > 1:
                        counts["multi_label"] += 1
                    for cat in matched:
                        counts[cat] += 1
                        _write_line(handles.get(cat), raw, write_count=flush_counter)
                    _live_print(
                        matched,
                        raw,
                        enabled=live,
                        max_lines=live_max,
                        out_stream=sys.stdout,
                    )
                    if live and live_max > 0 and _live_printed >= live_max and not live_cap_warned:
                        live_cap_warned = True
                        _msg_warn(
                            f"--live-max ({live_max}) reached; still writing to files."
                        )
                elif write_other:
                    counts["other"] += 1
                    _write_line(handles.get("_other"), raw, write_count=flush_counter)
                    if live_other:
                        _live_print(
                            ("other",),
                            raw,
                            enabled=True,
                            max_lines=live_max,
                            out_stream=sys.stdout,
                        )

                pe = progress_every
                if pe and counts["read"] % pe == 0:
                    elapsed = time.perf_counter() - t0
                    _progress_stderr(counts, categories, elapsed, out_dir, prefix, stats_only)
    finally:
        _flush_all(handles)
        for h in handles.values():
            if h is not None:
                h.close()

    elapsed = time.perf_counter() - t0
    return {
        **{k: int(v) for k, v in counts.items()},
        "elapsed_s": round(elapsed, 2),
        "input": str(src),
        "out_dir": str(out_dir.resolve()),
        "live_printed": _live_printed,
    }


def _file_size_hint(path: Path) -> str:
    try:
        if path.is_file():
            n = path.stat().st_size
            if n >= 1_048_576:
                return f"{n / 1_048_576:.1f}MB"
            if n >= 1024:
                return f"{n / 1024:.1f}KB"
            return f"{n}B"
    except OSError:
        pass
    return "?"


def _progress_stderr(
    counts: dict[str, int],
    categories: tuple[str, ...],
    elapsed: float,
    out_dir: Path,
    prefix: str,
    stats_only: bool,
) -> None:
    parts = [f"read={counts['read']:,}", f"matched={counts['matched_any']:,}"]
    # Top 8 categories by count
    ranked = sorted(((c, counts[c]) for c in categories), key=lambda x: -x[1])
    top = ranked[:8]
    for c, n in top:
        if n:
            parts.append(f"{c}={n:,}")
    if len(ranked) > 8:
        rest = sum(n for _, n in ranked[8:])
        if rest:
            parts.append(f"other_cats={rest:,}")
    if "other" in counts and counts["other"]:
        parts.append(f"other={counts['other']:,}")
    parts.append(f"s={elapsed:.1f}")
    if not stats_only:
        best_c, best_n = ranked[0] if ranked else ("", 0)
        if best_n:
            sz = _file_size_hint(out_dir / f"{prefix}{best_c}.txt")
            parts.append(f"sample_file={prefix}{best_c}.txt:{sz}")
    line = colored("[progress]", "blue", attrs=["bold"]) + " " + Fore.CYAN + "  ".join(parts)
    print(line, file=sys.stderr, flush=True)


def _parse_categories(s: str) -> tuple[str, ...]:
    try:
        return expand_category_selection(s)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e)) from e


def _print_categories() -> None:
    print_pocbit_banner(to_stderr=False)
    print()
    print(colored("Category groups", "white", attrs=["bold"]), file=sys.stdout, flush=True)
    print(
        colored("  panels", "green")
        + Fore.WHITE
        + " · "
        + colored("cms", "blue")
        + Fore.WHITE
        + " · "
        + colored("tools", "magenta")
        + Fore.WHITE
        + " · "
        + colored("all", "yellow"),
        file=sys.stdout,
        flush=True,
    )
    print()
    print(
        colored(f"══ Hosting panels ({len(PANEL_CATEGORIES)}) ══", "green", attrs=["bold"]),
        file=sys.stdout,
        flush=True,
    )
    print(Fore.GREEN + ", ".join(PANEL_CATEGORIES), file=sys.stdout, flush=True)
    print()
    print(
        colored(f"══ CMS / sites ({len(CMS_CATEGORIES)}) ══", "blue", attrs=["bold"]),
        file=sys.stdout,
        flush=True,
    )
    print(Fore.CYAN + ", ".join(CMS_CATEGORIES), file=sys.stdout, flush=True)
    print()
    print(
        colored(f"══ Tools ({len(TOOL_CATEGORIES)}) ══", "magenta", attrs=["bold"]),
        file=sys.stdout,
        flush=True,
    )
    print(Fore.MAGENTA + ", ".join(TOOL_CATEGORIES), file=sys.stdout, flush=True)
    print()
    print(colored("Examples", "yellow", attrs=["bold"]), file=sys.stdout, flush=True)
    print(
        colored("  python main.py -i ulp.txt -d ./out", "white"),
        file=sys.stdout,
        flush=True,
    )
    print(
        colored("  --categories panels,cms", "white")
        + Fore.WHITE
        + "  "
        + colored("|", "blue")
        + Fore.WHITE
        + "  "
        + colored("--categories cpanel,wordpress,joomla", "white"),
        file=sys.stdout,
        flush=True,
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="pocbit-ulp",
        description=f"{TOOL_TITLE} — single-pass ULP split (panels, CMS, tools).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=f"{TOOL_TAGLINE}",
    )
    ap.add_argument(
        "-i",
        "--input",
        type=Path,
        default=SCRIPT_DIR / "ulp.txt",
        help="Source ULP txt (GB-sized; streamed)",
    )
    ap.add_argument(
        "-d",
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory (default: same as input file)",
    )
    ap.add_argument(
        "--prefix",
        default="ulp_",
        help="Output filename prefix (e.g. ulp_cpanel.txt)",
    )
    ap.add_argument(
        "--categories",
        type=_parse_categories,
        default=DEFAULT_CATEGORY_ORDER,
        metavar="LIST",
        help="Comma-separated categories or groups: panels, cms, tools, all, ...",
    )
    ap.add_argument(
        "--list-categories",
        action="store_true",
        help="List supported categories and exit",
    )
    ap.add_argument(
        "--other",
        action="store_true",
        help="Write unmatched lines to ulp_other.txt",
    )
    ap.add_argument(
        "--progress-every",
        type=int,
        default=1_000_000,
        metavar="N",
        help="Progress on stderr every N lines (0: off)",
    )
    ap.add_argument(
        "--stats-only",
        action="store_true",
        help="Count only; do not write category files",
    )
    ap.add_argument(
        "--json-summary",
        type=Path,
        default=None,
        help="Write summary statistics to JSON file",
    )
    ap.add_argument(
        "--live",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Print matching lines to stdout. Disable with --no-live",
    )
    ap.add_argument(
        "--live-max",
        type=int,
        default=5000,
        metavar="N",
        help="Max lines printed with --live (0 = unlimited)",
    )
    ap.add_argument(
        "--live-other",
        action="store_true",
        help="With --other, also print unmatched lines to terminal",
    )
    args = ap.parse_args()
    _configure_stdio()

    if args.list_categories:
        _print_categories()
        return 0

    print_pocbit_banner()

    src: Path = args.input
    out_dir: Path = args.out_dir if args.out_dir is not None else src.parent

    if not args.stats_only:
        _msg_info(f"Input:  {src.resolve()}")
        _msg_info(f"Output: {out_dir.resolve()}")
        _msg_info(f"Prefix: {args.prefix!r}  ·  categories: {len(args.categories)}")
        if args.live:
            cap = "unlimited" if args.live_max == 0 else str(args.live_max)
            _msg_info(f"Live terminal (--live): on, max={cap}")
        else:
            _msg_info("Live terminal (--live): off")
        if args.other:
            _msg_ok("Unmatched lines → ulp_other.txt (--other)")
        print(file=sys.stderr, flush=True)

    try:
        summary = run_split(
            src,
            out_dir,
            prefix=args.prefix,
            categories=args.categories,
            write_other=args.other,
            progress_every=args.progress_every,
            stats_only=args.stats_only,
            live=args.live,
            live_max=args.live_max,
            live_other=args.live_other,
        )
    except FileNotFoundError:
        _msg_err(f"Input not found: {src}")
        _msg_hint("Place ulp.txt here or run: python main.py -i C:\\path\\to\\ulp.txt -d .\\out")
        _msg_hint("List rules: python main.py --list-categories")
        return 1
    except KeyboardInterrupt:
        print()
        _msg_warn("Interrupted by user.")
        return 130

    cats = args.categories
    print()
    _msg_ok(
        f"Done — read={summary['read']:,}  matched={summary['matched_any']:,}  "
        f"multi_label={summary['multi_label']:,}  elapsed={summary['elapsed_s']}s"
    )
    print(colored("  Per category:", "white", attrs=["bold"]), file=sys.stderr, flush=True)
    for c in cats:
        n = summary[c]
        if n:
            print(
                colored("    • ", "green") + Fore.WHITE + f"{c}: " + colored(f"{n:,}", "cyan"),
                file=sys.stderr,
                flush=True,
            )
        else:
            print(
                colored("    · ", "blue") + Style.DIM + f"{c}: 0" + Style.RESET_ALL,
                file=sys.stderr,
                flush=True,
            )
    if args.other:
        print(
            colored("    • ", "yellow") + Fore.WHITE + f"other: {summary.get('other', 0):,}",
            file=sys.stderr,
            flush=True,
        )
    if not args.stats_only:
        print()
        _msg_info(f"Output directory: {out_dir.resolve()}")
        written = []
        for c in cats:
            p = out_dir / (args.prefix + c + ".txt")
            n = summary.get(c, 0)
            if n:
                written.append((c, n, _file_size_hint(p)))
        written.sort(key=lambda x: -x[1])
        print(colored("  Files written (lines>0):", "white", attrs=["bold"]), file=sys.stderr, flush=True)
        for c, n, sz in written[:25]:
            print(
                colored("    ", "green")
                + Fore.GREEN
                + f"{args.prefix}{c}.txt"
                + Fore.WHITE
                + f"  lines={colored(f'{n:,}', 'cyan')}  size={colored(sz, 'yellow')}",
                file=sys.stderr,
                flush=True,
            )
        if len(written) > 25:
            _msg_hint(f"+{len(written) - 25} more files with matches")
        lp = summary.get("live_printed", 0)
        if lp:
            _msg_info(f"Printed to terminal (--live): {lp:,} lines")

    if args.json_summary:
        args.json_summary.parent.mkdir(parents=True, exist_ok=True)
        with args.json_summary.open("w", encoding="utf-8") as jf:
            json.dump(summary, jf, indent=2, ensure_ascii=False)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
