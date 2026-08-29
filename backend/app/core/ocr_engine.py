import logging
from typing import Any, Dict, List
import cv2
import numpy as np
import torch

logger = logging.getLogger(__name__)

_READER_INSTANCE = None


def get_ocr_reader():
    global _READER_INSTANCE
    if _READER_INSTANCE is None:
        try:
            import easyocr

            use_gpu = torch.cuda.is_available()
            logger.info(f"[*] Initializing EasyOCR engine (GPU={use_gpu})...")
            _READER_INSTANCE = easyocr.Reader(
                ["en"],
                gpu=use_gpu,
                download_enabled=True,
            )
            logger.info("[✓] EasyOCR engine ready.")
        except Exception as e:
            logger.error(f"[!] Failed to initialize EasyOCR: {e}")
            _READER_INSTANCE = None
    return _READER_INSTANCE


class OCREngine:
    def __init__(self):
        self.reader = get_ocr_reader()

    @staticmethod
    def resize_for_fast_ocr(image: np.ndarray, max_dim: int = 1280):
        h, w = image.shape[:2]
        if max(h, w) <= max_dim:
            return image, 1.0

        scale = max_dim / float(max(h, w))
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return resized, scale

    def extract_text_and_boxes(
        self, image: np.ndarray, ppm_scale: float = 1.0
    ) -> List[Dict[str, Any]]:
        if self.reader is None:
            self.reader = get_ocr_reader()
            if self.reader is None:
                return []

        resized_img, resize_scale = self.resize_for_fast_ocr(image, max_dim=1280)

        results = self.reader.readtext(
            resized_img,
            paragraph=False,
            decoder="greedy",
            beamWidth=1,
            batch_size=4,
            mag_ratio=1.0,
            canvas_size=1280,
            workers=0,
        )

        tokens = []
        for bbox, text, conf in results:
            if conf < 0.25 or not text.strip():
                continue

            scaled_bbox = np.array(bbox) / resize_scale
            pts = scaled_bbox.astype(np.float32)
            h1 = np.linalg.norm(pts[0] - pts[3])
            h2 = np.linalg.norm(pts[1] - pts[2])
            height_px = float(max(h1, h2))
            height_mm = height_px / ppm_scale if ppm_scale > 0 else height_px * 0.264

            tokens.append(
                {
                    "text": text.strip(),
                    "confidence": float(conf),
                    "bbox": scaled_bbox.tolist(),
                    "height_px": height_px,
                    "height_mm": height_mm,
                }
            )

        return tokens

    def extract_tokens(self, image: np.ndarray, ppm_scale: float = 1.0) -> List[Dict[str, Any]]:
        return self.extract_text_and_boxes(image, ppm_scale=ppm_scale)