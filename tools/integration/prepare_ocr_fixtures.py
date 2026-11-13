"""Render original test text; no OCR outputs or user records are invented."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

parser = argparse.ArgumentParser()
parser.add_argument("--font", type=Path, default=Path("/System/Library/Fonts/Hiragino Sans GB.ttc"))
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
directory = root / "application-backend/.local-data/ocr-acceptance"
directory.mkdir(parents=True, exist_ok=True)
font = ImageFont.truetype(str(args.font), 54)
cases = []
for name, size, texts in [("horizontal", (1280, 720), ["日本語を勉強しています。", "東京へ旅行に行きます。"]), ("vertical", (720, 1280), ["日本語の勉強"]), ("empty", (1280, 720), []), ("zh_horizontal", (1280, 720), ["欢迎来到北京。", "我们一起学习中文。"]), ("zh_vertical", (720, 1280), ["欢迎来到北京"])]:
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    if name.endswith("vertical"):
        for index, character in enumerate(texts[0]):
            draw.text((500, 90 + index * 64), character, font=font, fill="black")
    else:
        for index, text in enumerate(texts):
            draw.text((55, 130 + index * 110), text, font=font, fill="black")
    image.save(directory / (name + ".png"))
    cases.append({"name": name, "language": "zh" if name.startswith("zh_") else "ja", "image": name + ".png", "expected_text": "".join(texts), "input_kind": "original_rendered_text_fixture"})
(directory / "cases.json").write_text(json.dumps(cases, ensure_ascii=False, indent=2))
print(json.dumps({"status": "GENERATED_TEST_INPUTS", "cases": len(cases), "directory": str(directory)}))
