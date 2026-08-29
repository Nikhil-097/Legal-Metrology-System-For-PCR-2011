import cv2
import numpy as np


class ImagePreprocessor:
    """Packaging Image Preprocessor with Dot-Matrix Closing."""

    @staticmethod
    def enhance_for_ocr(image: np.ndarray) -> np.ndarray:
        if image is None:
            return None

        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # CLAHE Contrast Enhancement
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        contrast_enhanced = clahe.apply(gray)

        # Connect dot-matrix inkjet dots
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        dot_closed = cv2.morphologyEx(contrast_enhanced, cv2.MORPH_CLOSE, kernel)

        return cv2.cvtColor(dot_closed, cv2.COLOR_GRAY2BGR)