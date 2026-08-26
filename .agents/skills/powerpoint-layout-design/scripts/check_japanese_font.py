#!/usr/bin/env python3
"""日本語フォントが実行環境に存在するか、外部依存なしで確認する。"""

from __future__ import annotations

import argparse
import json
import os
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOKENS_PATH = ROOT / "assets/design-tokens.json"
FONT_SUFFIXES = {".ttf", ".otf", ".ttc"}
MAX_FONT_BYTES = 64 * 1024 * 1024


def normalized(name: str) -> str:
    return "".join(char for char in name.casefold() if char.isalnum())


def default_font_directories() -> list[Path]:
    directories = [
        ROOT / "assets/fonts",
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
        Path("/System/Library/Fonts"),
        Path("/Library/Fonts"),
    ]
    user = Path.home()
    directories.extend(
        [
            user / ".fonts",
            user / ".local/share/fonts",
            user / "Library/Fonts",
            user / "AppData/Local/Microsoft/Windows/Fonts",
        ]
    )
    windows_root = os.environ.get("WINDIR")
    if windows_root:
        directories.append(Path(windows_root) / "Fonts")
    result: list[Path] = []
    seen: set[Path] = set()
    for directory in directories:
        try:
            resolved = directory.resolve()
        except OSError:
            continue
        if resolved not in seen and resolved.is_dir():
            seen.add(resolved)
            result.append(resolved)
    return result


def decode_name(platform_id: int, encoding_id: int, payload: bytes) -> str:
    try:
        if platform_id in {0, 3}:
            return payload.decode("utf-16-be").strip("\x00 ")
        if platform_id == 1:
            return payload.decode("mac_roman").strip("\x00 ")
        if encoding_id in {1, 10}:
            return payload.decode("utf-16-be").strip("\x00 ")
    except UnicodeError:
        return ""
    return ""


def sfnt_offsets(payload: bytes) -> list[int]:
    if payload[:4] != b"ttcf":
        return [0]
    if len(payload) < 12:
        return []
    count = struct.unpack(">I", payload[8:12])[0]
    if count > 128 or len(payload) < 12 + count * 4:
        return []
    return [
        struct.unpack(">I", payload[12 + index * 4 : 16 + index * 4])[0]
        for index in range(count)
    ]


def font_family_names(path: Path) -> set[str]:
    try:
        if path.stat().st_size > MAX_FONT_BYTES:
            return set()
        payload = path.read_bytes()
    except OSError:
        return set()
    names: set[str] = set()
    for sfnt_offset in sfnt_offsets(payload):
        if sfnt_offset < 0 or sfnt_offset + 12 > len(payload):
            continue
        table_count = struct.unpack(
            ">H", payload[sfnt_offset + 4 : sfnt_offset + 6]
        )[0]
        if table_count > 4096:
            continue
        name_offset = None
        for index in range(table_count):
            record_offset = sfnt_offset + 12 + index * 16
            if record_offset + 16 > len(payload):
                break
            if payload[record_offset : record_offset + 4] == b"name":
                name_offset = struct.unpack(
                    ">I", payload[record_offset + 8 : record_offset + 12]
                )[0]
                break
        if name_offset is None or name_offset + 6 > len(payload):
            continue
        record_count, string_offset = struct.unpack(
            ">HH", payload[name_offset + 2 : name_offset + 6]
        )
        if record_count > 8192:
            continue
        strings_base = name_offset + string_offset
        for index in range(record_count):
            record_offset = name_offset + 6 + index * 12
            if record_offset + 12 > len(payload):
                break
            platform_id, encoding_id, _language_id, name_id, length, offset = (
                struct.unpack(">HHHHHH", payload[record_offset : record_offset + 12])
            )
            if name_id not in {1, 16}:
                continue
            start = strings_base + offset
            end = start + length
            if start < 0 or end > len(payload):
                continue
            name = decode_name(platform_id, encoding_id, payload[start:end])
            if name:
                names.add(name)
    return names


def discover_fonts(directories: list[Path]) -> dict[str, tuple[str, Path]]:
    discovered: dict[str, tuple[str, Path]] = {}
    for directory in directories:
        try:
            paths = directory.rglob("*")
            for path in paths:
                if (
                    path.is_symlink()
                    or not path.is_file()
                    or path.suffix.lower() not in FONT_SUFFIXES
                ):
                    continue
                for family in font_family_names(path):
                    discovered.setdefault(normalized(family), (family, path))
        except OSError:
            continue
    return discovered


def load_candidates() -> list[str]:
    try:
        tokens = json.loads(TOKENS_PATH.read_text(encoding="utf-8"))
        candidates = tokens["typography"]["fontFamilies"]["japanese"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError):
        return []
    return [
        candidate
        for candidate in candidates
        if isinstance(candidate, str) and candidate.strip()
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="日本語フォントの実在をローカルのフォントファイルから確認します。"
    )
    parser.add_argument(
        "--require",
        action="append",
        default=[],
        help="必須フォント名。複数回指定した場合はすべて必要です。",
    )
    parser.add_argument(
        "--font-dir",
        action="append",
        default=[],
        help="追加で検査するフォントディレクトリ。",
    )
    args = parser.parse_args()

    directories = default_font_directories()
    for raw_directory in args.font_dir:
        candidate = Path(raw_directory)
        if candidate.is_dir():
            directories.append(candidate.resolve())
    discovered = discover_fonts(directories)
    required = args.require or load_candidates()
    if not required:
        print("エラー: 検査対象の日本語フォントが定義されていません")
        return 2

    if args.require:
        missing = [
            family for family in required if normalized(family) not in discovered
        ]
        if missing:
            print("エラー: 必須フォントがありません: " + ", ".join(missing))
            return 1
        for family in required:
            actual, path = discovered[normalized(family)]
            print(f"確認: {family} -> {actual} ({path})")
        return 0

    for family in required:
        match = discovered.get(normalized(family))
        if match:
            actual, path = match
            print(f"確認: {family} -> {actual} ({path})")
            return 0
    print(
        "エラー: 候補の日本語フォントが一つもありません: "
        + ", ".join(required)
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
