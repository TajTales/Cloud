import type { OcrBox } from "./learning";

export function containedRect(containerWidth: number, containerHeight: number, imageWidth: number, imageHeight: number) {
  if ([containerWidth, containerHeight, imageWidth, imageHeight].some(value => !Number.isFinite(value) || value <= 0)) return null;
  const scale = Math.min(containerWidth / imageWidth, containerHeight / imageHeight);
  const width = imageWidth * scale, height = imageHeight * scale;
  return { left: (containerWidth - width) / 2, top: (containerHeight - height) / 2, width, height };
}

export function boxRect(box: OcrBox, content: NonNullable<ReturnType<typeof containedRect>>) {
  return { left: content.left + (box.center_x - box.width / 2) * content.width, top: content.top + (box.center_y - box.height / 2) * content.height,
    width: box.width * content.width, height: box.height * content.height };
}

export function captureSize(width: number, height: number) {
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) throw new Error("Video chưa có kích thước hợp lệ.");
  const scale = Math.min(1, 1600 / Math.max(width, height), Math.sqrt(4000000 / (width * height)));
  return { width: Math.max(1, Math.round(width * scale)), height: Math.max(1, Math.round(height * scale)) };
}
