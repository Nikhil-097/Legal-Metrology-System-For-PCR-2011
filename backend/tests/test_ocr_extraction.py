import numpy as np
import cv2
from app.core.preprocessor import ImagePreprocessor
from app.core.scale_estimator import ScaleEstimator


def test_image_preprocessor_pipeline():
    # Create a synthetic high-contrast RGB image with an artificial bright spot
    synthetic_img = np.full((500, 500, 3), 120, dtype=np.uint8)
    cv2.circle(synthetic_img, (250, 250), 40, (255, 255, 255), -1)  # Specular glare spot

    preprocessor = ImagePreprocessor()
    deglared = preprocessor.remove_glare(synthetic_img)
    enhanced = preprocessor.enhance_contrast(deglared)

    assert deglared.shape == synthetic_img.shape
    assert enhanced.shape == synthetic_img.shape
    assert enhanced.dtype == np.uint8


def test_scale_estimator_fallback():
    # When no barcode or QR code is detected, it should safely return the 300 DPI baseline scale
    blank_canvas = np.zeros((400, 400, 3), dtype=np.uint8)
    ppm_scale, detected_barcode = ScaleEstimator.estimate_ppm(blank_canvas)

    expected_fallback_ppm = round(300 / 25.4, 3)  # 11.811 pixels per mm
    assert ppm_scale == expected_fallback_ppm
    assert detected_barcode is None