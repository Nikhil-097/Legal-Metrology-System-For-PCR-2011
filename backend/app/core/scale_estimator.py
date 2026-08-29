import cv2
import numpy as np
from typing import Tuple, Optional
from pyzbar.pyzbar import decode as decode_barcode

class ScaleEstimator:
    """Computes real-world physical pixel scaling (Pixels Per Millimeter)."""

    # Standard EAN-13 nominal physical width is 37.29 mm
    STANDARD_EAN13_WIDTH_MM = 37.29

    @classmethod
    def estimate_ppm(cls, image: np.ndarray) -> Tuple[float, Optional[str]]:
        """
        Detects 1D Barcode or QR code to deduce the Pixel-per-Millimeter (PPM) scaling factor.
        Returns: (ppm_scale, detected_barcode_value)
        """
        barcodes = decode_barcode(image)
        if barcodes:
            for b in barcodes:
                barcode_str = b.data.decode("utf-8")
                rect = b.rect
                if b.type == "EAN13" or len(barcode_str) == 13:
                    # Calculate PPM using horizontal pixel bounding width
                    ppm = rect.width / cls.STANDARD_EAN13_WIDTH_MM
                    return round(ppm, 3), barcode_str
                elif rect.width > 0:
                    # Standard QR Code base assumption: 20 mm nominal width
                    ppm = rect.width / 20.0
                    return round(ppm, 3), barcode_str

        # Fallback baseline: 300 DPI mobile image capture standard (11.81 pixels per mm)
        fallback_dpi = 300
        fallback_ppm = fallback_dpi / 25.4
        return round(fallback_ppm, 3), None