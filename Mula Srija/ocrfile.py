import tempfile
from pdf2image import convert_from_bytes
from paddleocr import PaddleOCR

# ✅ LOAD OCR MODEL ONLY ONCE (VERY IMPORTANT)
ocr = PaddleOCR(use_angle_cls=True, lang='en')


def extract_text_from_image(image_path):
    try:
        result = ocr.ocr(image_path, cls=True)

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