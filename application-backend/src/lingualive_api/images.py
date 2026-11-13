"""Bound decoding before a frame can enter the OCR queue."""
import io
import warnings

from PIL import Image, UnidentifiedImageError

from .errors import ApiError


def validate_image(content, content_type, *, expected_size=None):
    if not content or len(content) > 1048576:
        raise ApiError(413 if content else 422, "IMAGE_TOO_LARGE" if content else "INVALID_IMAGE", "Ảnh rỗng hoặc vượt giới hạn 1 MiB.")
    if content_type not in {"image/png", "image/jpeg"}:
        raise ApiError(415, "UNSUPPORTED_IMAGE_TYPE", "Chỉ nhận ảnh PNG hoặc JPEG.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as image:
                size = image.size
                if min(size) < 1 or max(size) > 1600 or size[0] * size[1] > 4000000:
                    raise ApiError(413, "IMAGE_TOO_LARGE", "Ảnh vượt giới hạn kích thước pixel.")
                if image.format != {"image/png": "PNG", "image/jpeg": "JPEG"}[content_type] or getattr(image, "n_frames", 1) != 1:
                    raise ApiError(415, "UNSUPPORTED_IMAGE_TYPE", "Định dạng ảnh không khớp hoặc ảnh có nhiều frame.")
                if expected_size and tuple(expected_size) != size:
                    raise ApiError(422, "INVALID_IMAGE", "Kích thước ảnh khác metadata đã đăng ký.")
                image.verify()
            with Image.open(io.BytesIO(content)) as image:
                if image.getexif().get(274, 1) != 1:
                    raise ApiError(422, "INVALID_IMAGE", "Frame phải được xoay đúng hướng trước khi tải lên.")
                image.load()
                return size
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ApiError(422, "INVALID_IMAGE", "Không đọc được ảnh. Vui lòng gửi một frame PNG/JPEG hợp lệ.") from None
