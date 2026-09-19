import cv2
import numpy as np


DARK_PIXEL_THRESHOLD = 50
BRIGHT_PIXEL_THRESHOLD = 235


def _to_bgr_array(image):
    array = np.array(image.convert("RGB"))
    return cv2.cvtColor(array, cv2.COLOR_RGB2BGR)


def analyze_technical_metrics(image):

    bgr = _to_bgr_array(image)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    total_pixels = gray.size

    mean_brightness = float(gray.mean())

    dark_pixels_percent = float((gray < DARK_PIXEL_THRESHOLD).sum() / total_pixels * 100)

    overexposed_pixels_percent = float((gray > BRIGHT_PIXEL_THRESHOLD).sum() / total_pixels * 100)

    low_percentile, high_percentile = np.percentile(gray, [5, 95])
    contrast_range = float(high_percentile - low_percentile)

    laplacian_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    median_filtered = cv2.medianBlur(gray, 5)
    noise_level = float(
        np.mean(
            np.abs(gray.astype(np.float32) - median_filtered.astype(np.float32)))
    )

    mean_saturation = float(hsv[:, :, 1].mean() / 255 * 100)

    return {
        "mean_brightness": round(mean_brightness, 2),
        "dark_pixels_percent": round(dark_pixels_percent, 2),
        "overexposed_pixels_percent": round(overexposed_pixels_percent, 2),
        "contrast_range": round(contrast_range, 2),
        "laplacian_variance": round(laplacian_variance, 2),
        "noise_level": round(noise_level, 2),
        "mean_saturation": round(mean_saturation, 2),
    }