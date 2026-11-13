"""Local Chinese PP-OCR models through RapidOCR; same raw wire schema."""
import numpy as np
from rapidocr_onnxruntime import RapidOCR

from ...interface import BoundingBox, OcrProvider, Paragraph, Word


class RapidChineseProvider(OcrProvider):
    NAME = "rapidocr-ppocr (local Chinese)"
    SUPPORTED_LANGUAGES = ("zh",)

    def __init__(self):
        # The pinned wheel includes its ONNX models. No image/network API.
        self.engine = RapidOCR()

    def scan(self, image):
        width, height = image.size
        results, _ = self.engine(np.asarray(image.convert("RGB"))[:, :, ::-1].copy())
        paragraphs = []
        for points, text, score in results or []:
            if not text.strip():
                continue
            left = max(0, min(width, min(point[0] for point in points)))
            right = max(left, min(width, max(point[0] for point in points)))
            top = max(0, min(height, min(point[1] for point in points)))
            bottom = max(top, min(height, max(point[1] for point in points)))
            box = BoundingBox(float((left + right) / 2 / width), float((top + bottom) / 2 / height), float((right - left) / width), float((bottom - top) / height))
            # No invented character boxes: the model returns one quadrilateral
            # per detected line, so this raw Word represents the complete line.
            paragraphs.append(Paragraph(text, [Word(text, "", box)], box, box.height > box.width * 1.5))
        return paragraphs
