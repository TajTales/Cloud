"""Generate optional original demo videos, never seeded into user sessions."""
from pathlib import Path
import cv2

directory = Path(__file__).resolve().parents[2] / "application-backend/.local-data/ocr-acceptance"
for language, image_name in [("ja", "horizontal.png"), ("zh", "zh_horizontal.png")]:
    image = cv2.imread(str(directory / image_name))
    if image is None:
        raise RuntimeError("Run prepare_ocr_fixtures.py first")
    height, width = image.shape[:2]
    output = directory / (language + "-demo.mp4")
    writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"mp4v"), 10, (width, height))
    if not writer.isOpened():
        raise RuntimeError("No MP4 encoder is available")
    try:
        for frame_index in range(150):
            frame = image.copy()
            cv2.putText(frame, f"OCR TEST {frame_index / 10:.1f}s", (60, 630), cv2.FONT_HERSHEY_SIMPLEX, .8, (80, 80, 80), 1)
            writer.write(frame)
    finally:
        writer.release()
    print(output)
