import os
import tempfile
from pdf2image import convert_from_bytes

# Avoid known Paddle 3.x oneDNN/PIR runtime crashes on some Windows builds.
os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("FLAGS_enable_pir_api", "0")

from paddleocr import PaddleOCR

# ✅ LOAD OCR MODEL ONLY ONCE (VERY IMPORTANT)
def _create_ocr():
    try:
        return PaddleOCR(use_angle_cls=True, lang='en')
    except Exception as e:
        if "ConvertPirAttribute2RuntimeAttribute" in str(e) or "onednn_instruction" in str(e):
            return PaddleOCR(use_angle_cls=False, lang='en')
        raise


ocr = _create_ocr()
_ocr_fallback = None


def _get_fallback_ocr():
    global _ocr_fallback
    if _ocr_fallback is None:
        _ocr_fallback = PaddleOCR(use_angle_cls=False, lang='en')
    return _ocr_fallback


def _run_ocr(image_path):
    try:
        return ocr.ocr(image_path, cls=True)
    except TypeError as e:
        if "unexpected keyword argument 'cls'" not in str(e):
            raise
    except Exception as e:
        if "ConvertPirAttribute2RuntimeAttribute" in str(e) or "onednn_instruction" in str(e):
            return _get_fallback_ocr().ocr(image_path)
        if "cls" not in str(e).lower():
            raise

    return ocr.ocr(image_path)


def extract_text_from_image(image_path):
    try:
        result = _run_ocr(image_path)

        extracted_text = ""
        for line in result:
            for word in line:
                extracted_text += word[1][0] + " "

        return extracted_text.strip()

    except Exception as e:
        return f"OCR FAILED: {str(e)}"


def extract_text_from_scanned_pdf(file):
    images = convert_from_bytes(file.read())
    full_text = ""

    for image in images:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp:
            image.save(temp.name, "PNG")
            full_text += extract_text_from_image(temp.name) + "\n"

    return full_text.strip()