#!/usr/bin/env python3
"""新規生成した参照PPTXの識別子と作成者メタデータを正規化する。"""

from __future__ import annotations

import argparse
import html
import re
import tempfile
import zipfile
from pathlib import Path


CREATOR = "powerpoint-layout-design"
FIXED_TIMESTAMP = "2026-07-26T00:00:00Z"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--slides", type=int, required=True)
    return parser.parse_args()


def replace_element(xml: str, tag: str, value: str) -> str:
    pattern = re.compile(
        rf"(<{re.escape(tag)}(?:\s[^>]*)?>).*?(</{re.escape(tag)}>)",
        re.DOTALL,
    )
    replacement = rf"\g<1>{html.escape(value)}\g<2>"
    updated, count = pattern.subn(replacement, xml, count=1)
    if count != 1:
        raise ValueError(f"{tag}を一意に更新できません: count={count}")
    return updated


def normalize_core(xml: str) -> str:
    xml = replace_element(xml, "dc:creator", CREATOR)
    xml = replace_element(xml, "lastModifiedBy", CREATOR)
    xml = replace_element(xml, "dcterms:created", FIXED_TIMESTAMP)
    xml = replace_element(xml, "dcterms:modified", FIXED_TIMESTAMP)
    return xml


def normalize_app(xml: str, slides: int) -> str:
    xml = replace_element(xml, "ap:Application", CREATOR)
    xml = replace_element(
        xml,
        "ap:PresentationFormat",
        "Japanese PowerPoint layout reference",
    )
    xml = replace_element(xml, "ap:Slides", str(slides))
    xml = replace_element(xml, "ap:Notes", str(slides))
    xml = replace_element(xml, "ap:HiddenSlides", "0")
    return xml


def normalize_slide(xml: str, slide_number: int) -> str:
    if re.search(r"<a:(?:stCxn|endCxn)\b", xml):
        raise ValueError(
            f"slide{slide_number}: 接続参照があるためIDを安全に再採番できません"
        )
    sequence = 0
    suffix_pattern = re.compile(r"__s\d{3}o\d{3}$")

    def replace_nonvisual(match: re.Match[str]) -> str:
        nonlocal sequence
        sequence += 1
        tag = match.group(0)
        name_match = re.search(r'\bname="([^"]*)"', tag)
        original_name = html.unescape(name_match.group(1)) if name_match else ""
        base_name = suffix_pattern.sub("", original_name).strip()
        if not base_name:
            base_name = "slide-root" if sequence == 1 else "object"
        normalized_name = (
            f"{base_name}__s{slide_number:03d}o{sequence:03d}"
        )
        if re.search(r'\bid="[^"]*"', tag):
            tag = re.sub(r'\bid="[^"]*"', f'id="{sequence}"', tag, count=1)
        else:
            tag = tag[:-1] + f' id="{sequence}">'
        escaped_name = html.escape(normalized_name, quote=True)
        if name_match:
            tag = re.sub(
                r'\bname="[^"]*"',
                f'name="{escaped_name}"',
                tag,
                count=1,
            )
        else:
            tag = tag[:-1] + f' name="{escaped_name}">'
        return tag

    normalized = re.sub(r"<p:cNvPr\b[^>]*>", replace_nonvisual, xml)
    if sequence < 2:
        raise ValueError(
            f"slide{slide_number}: 正規化対象の図形が不足しています"
        )
    return normalized


def main() -> None:
    args = parse_args()
    pptx = args.pptx.resolve()
    if not pptx.is_file():
        raise SystemExit(f"PPTXがありません: {pptx}")

    with zipfile.ZipFile(pptx, "r") as source:
        infos = source.infolist()
        names = {info.filename for info in infos}
        required = {"docProps/core.xml", "docProps/app.xml"}
        if not required <= names:
            raise SystemExit(
                f"必須メタデータがありません: {sorted(required - names)}"
            )
        slide_names = sorted(
            (
                name
                for name in names
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ),
            key=lambda name: int(re.search(r"\d+", name).group()),
        )
        if len(slide_names) != args.slides:
            raise SystemExit(
                f"スライド数が一致しません: expected={args.slides}, "
                f"actual={len(slide_names)}"
            )
        replacements: dict[str, bytes] = {
            "docProps/core.xml": normalize_core(
                source.read("docProps/core.xml").decode("utf-8-sig")
            ).encode("utf-8"),
            "docProps/app.xml": normalize_app(
                source.read("docProps/app.xml").decode("utf-8-sig"),
                args.slides,
            ).encode("utf-8"),
        }
        for index, slide_name in enumerate(slide_names, start=1):
            replacements[slide_name] = normalize_slide(
                source.read(slide_name).decode("utf-8-sig"),
                index,
            ).encode("utf-8")

        with tempfile.NamedTemporaryFile(
            prefix=f"{pptx.stem}-",
            suffix=".pptx",
            dir=pptx.parent,
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
        try:
            with zipfile.ZipFile(
                temporary_path,
                "w",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            ) as target:
                for info in infos:
                    payload = replacements.get(
                        info.filename,
                        source.read(info.filename),
                    )
                    target.writestr(info, payload)
            temporary_path.replace(pptx)
        finally:
            temporary_path.unlink(missing_ok=True)

    print(f"正規化完了: slides={args.slides}, pptx={pptx}")


if __name__ == "__main__":
    main()
