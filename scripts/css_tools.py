#!/usr/bin/env python3
"""Build and switch CSS assets for this static site.

Commands:
  - build: generate styles/*.min.css from readable styles/*.css
  - mode dev|prod: switch HTML stylesheet links between .css and .min.css
  - status: report current link mode across HTML pages
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLES_DIR = ROOT / "styles"
HTML_GLOB = "*.html"


def css_sources() -> list[Path]:
    return sorted(
        p
        for p in STYLES_DIR.glob("*.css")
        if p.is_file() and not p.name.endswith(".min.css")
    )


def min_path(source: Path) -> Path:
    return source.with_name(f"{source.stem}.min.css")


def _extract_strings(css: str) -> tuple[str, dict[str, str]]:
    out: list[str] = []
    strings: dict[str, str] = {}
    i = 0
    n = len(css)
    token_id = 0

    while i < n:
        ch = css[i]
        if ch not in ("'", '"'):
            out.append(ch)
            i += 1
            continue

        quote = ch
        start = i
        i += 1
        escaped = False
        while i < n:
            c = css[i]
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == quote:
                i += 1
                break
            i += 1

        literal = css[start:i]
        token = f"__CSS_STR_{token_id}__"
        token_id += 1
        strings[token] = literal
        out.append(token)

    return "".join(out), strings


def _restore_strings(css: str, strings: dict[str, str]) -> str:
    for token, literal in strings.items():
        css = css.replace(token, literal)
    return css


def minify_css(css: str) -> str:
    """Conservative CSS minifier that preserves quoted string contents."""
    masked, strings = _extract_strings(css)

    # Remove comments and collapse whitespace.
    masked = re.sub(r"/\*.*?\*/", "", masked, flags=re.S)
    masked = re.sub(r"\s+", " ", masked)

    # Remove safe spacing around structural separators.
    masked = re.sub(r"\s*([{}:;,>~])\s*", r"\1", masked)

    # Remove trailing semicolons before "}".
    masked = re.sub(r";}", "}", masked)

    masked = masked.strip()
    return _restore_strings(masked, strings)


def build_minified() -> int:
    if not STYLES_DIR.exists():
        print("styles directory not found")
        return 1

    total_src = 0
    total_min = 0
    count = 0

    for src in css_sources():
        raw = src.read_text(encoding="utf-8")
        mini = minify_css(raw)
        dest = min_path(src)
        dest.write_text(mini + "\n", encoding="utf-8")

        src_len = len(raw.encode("utf-8"))
        min_len = len((mini + "\n").encode("utf-8"))
        total_src += src_len
        total_min += min_len
        count += 1
        print(f"built {dest.relative_to(ROOT)} ({src_len} -> {min_len} bytes)")

    saved = total_src - total_min
    print(
        f"done: {count} files, {total_src} -> {total_min} bytes "
        f"(saved {saved} bytes)"
    )
    return 0


HREF_RE = re.compile(r'href="styles/([^"]+?)(?:\.min)?\.css"')


def switch_mode(mode: str) -> int:
    html_files = sorted(ROOT.glob(HTML_GLOB))
    changed = 0
    missing_min: set[str] = set()

    for html in html_files:
        text = html.read_text(encoding="utf-8")

        def repl(match: re.Match[str]) -> str:
            base = match.group(1)
            if mode == "prod":
                min_file = STYLES_DIR / f"{base}.min.css"
                if not min_file.exists():
                    missing_min.add(min_file.name)
                return f'href="styles/{base}.min.css"'
            return f'href="styles/{base}.css"'

        updated = HREF_RE.sub(repl, text)
        if updated != text:
            html.write_text(updated, encoding="utf-8")
            changed += 1

    if mode == "prod" and missing_min:
        print("warning: missing minified files:")
        for name in sorted(missing_min):
            print(f"  - styles/{name}")
        print("run: python3 scripts/css_tools.py build")

    print(f"updated {changed} HTML files to {mode} mode")
    return 0


def status() -> int:
    html_files = sorted(ROOT.glob(HTML_GLOB))
    min_links = 0
    dev_links = 0

    for html in html_files:
        text = html.read_text(encoding="utf-8")
        for _base, min_part in re.findall(
            r'href="styles/([^"]+?)(\.min)?\.css"', text
        ):
            if min_part:
                min_links += 1
            else:
                dev_links += 1

    if min_links and not dev_links:
        mode = "prod"
    elif dev_links and not min_links:
        mode = "dev"
    else:
        mode = "mixed"

    print(f"mode: {mode}")
    print(f"links -> dev: {dev_links}, prod(min): {min_links}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CSS build/switch tooling")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("build", help="Generate styles/*.min.css")

    p_mode = sub.add_parser("mode", help="Switch HTML link mode")
    p_mode.add_argument("target", choices=("dev", "prod"))

    sub.add_parser("status", help="Show current HTML CSS link mode")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.cmd == "build":
        return build_minified()
    if args.cmd == "mode":
        return switch_mode(args.target)
    if args.cmd == "status":
        return status()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
