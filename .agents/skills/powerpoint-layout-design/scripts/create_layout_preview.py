#!/usr/bin/env python3
"""参照スライドPNGを、ファイル名付きの一覧画像へ決定的に合成する。"""

from __future__ import annotations

import argparse
import math
import re
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-file", type=Path, required=True)
    parser.add_argument("--columns", type=int, default=5)
    parser.add_argument("--cell-width", type=int, default=320)
    parser.add_argument("--cell-height", type=int, default=180)
    parser.add_argument("--gap", type=int, default=12)
    parser.add_argument("--label-height", type=int, default=24)
    return parser.parse_args()


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def main() -> None:
    args = parse_args()
    def slide_number(path: Path) -> int:
        match = re.search(r"(\d+)$", path.stem)
        return int(match.group(1)) if match else 10**9

    files = sorted(args.input_dir.glob("slide-*.png"), key=slide_number)
    if not files:
        raise SystemExit("slide-*.png が見つかりません")
    if args.columns < 1:
        raise SystemExit("--columns は1以上にしてください")

    rows = math.ceil(len(files) / args.columns)
    canvas_width = (
        args.gap
        + args.columns * (args.cell_width + args.gap)
    )
    canvas_height = (
        args.gap
        + rows * (args.cell_height + args.label_height + args.gap)
    )
    canvas = Image.new("RGB", (canvas_width, canvas_height), "#F2F2F2")
    draw = ImageDraw.Draw(canvas)
    font = load_font(13)

    for index, file_path in enumerate(files):
        row, column = divmod(index, args.columns)
        left = args.gap + column * (args.cell_width + args.gap)
        top = args.gap + row * (
            args.cell_height + args.label_height + args.gap
        )
        with Image.open(file_path) as image:
            thumb = ImageOps.contain(
                image.convert("RGB"),
                (args.cell_width, args.cell_height),
                Image.Resampling.LANCZOS,
            )
        x = left + (args.cell_width - thumb.width) // 2
        y = top + (args.cell_height - thumb.height) // 2
        canvas.paste(thumb, (x, y))
        draw.rectangle(
            (
                left,
                top,
                left + args.cell_width - 1,
                top + args.cell_height - 1,
            ),
            outline="#A7A7A7",
            width=1,
        )
        label = file_path.name
        label_box = draw.textbbox((0, 0), label, font=font)
        label_width = label_box[2] - label_box[0]
        draw.text(
            (
                left + (args.cell_width - label_width) // 2,
                top + args.cell_height + 3,
            ),
            label,
            fill="#1F1F1F",
            font=font,
        )

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f"{args.output_file.stem}-",
        suffix=".png",
        dir=args.output_file.parent,
        delete=False,
    ) as handle:
        temporary_path = Path(handle.name)
    try:
        canvas.save(temporary_path, optimize=True)
        temporary_path.replace(args.output_file)
    finally:
        temporary_path.unlink(missing_ok=True)
    print(f"生成完了: slides={len(files)}, preview={args.output_file}")


if __name__ == "__main__":
    main()
