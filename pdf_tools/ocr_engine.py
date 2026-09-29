import pytesseract
from PIL import Image
import io
import os

# On Windows, pytesseract needs to know exactly where the Tesseract-OCR
# program is installed, unless its folder has been added to PATH.
# This points at the default install location as a fallback so OCR still
# works even if the PATH step didn't take effect. If you installed it
# somewhere else, update the path below to match.
if os.name == "nt":
    _default_windows_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(_default_windows_path):
        pytesseract.pytesseract.tesseract_cmd = _default_windows_path

# Cap the longest side an image can be before OCR runs. A full-resolution
# scan (often 2000-3000px+) makes Tesseract noticeably slower and more
# memory-hungry, which matters a lot on resource-limited hosting (e.g. a
# free-tier server) - a slow OCR call can exceed the web server's request
# timeout and get killed. 2000px is generous enough that text stays sharp
# for OCR accuracy while capping the worst case.
MAX_OCR_DIMENSION = 2000


def process_image_ocr(image_bytes, lang='eng'):
    """
    Processes image bytes using pytesseract:
    1. Normalizes image color space to RGB.
    2. Downscales large images before OCR (see MAX_OCR_DIMENSION above),
       scaling bounding boxes back up afterward so callers still get
       coordinates in the ORIGINAL image's pixel space.
    3. Filters out low-confidence OCR noise (conf <= 40).
    4. Groups words into complete lines by block & line IDs.
    5. Sorts lines top-to-bottom (y0) and left-to-right (x0).
    """
    # 1. Normalize image mode to RGB for consistent processing
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    original_width, original_height = image.size

    # 2. Downscale for OCR if needed, remembering the scale factor so
    # bounding boxes can be converted back to original-image coordinates.
    scale_factor = 1.0
    largest_dimension = max(original_width, original_height)
    if largest_dimension > MAX_OCR_DIMENSION:
        scale_factor = MAX_OCR_DIMENSION / largest_dimension
        scaled_size = (
            max(1, int(original_width * scale_factor)),
            max(1, int(original_height * scale_factor)),
        )
        ocr_image = image.resize(scaled_size, Image.LANCZOS)
    else:
        ocr_image = image

    # PSM 6 tells Tesseract to treat the image as a single uniform block of
    # text and read it in reading order, which handles table-like rows
    # (side-by-side cells) more sensibly than the default auto-layout mode —
    # the default mode is what was causing side-by-side cells like "Gender"
    # and "Nationality" to sometimes get merged into one oversized line.
    custom_config = "--psm 6"
    data = pytesseract.image_to_data(
        ocr_image, lang=lang, config=custom_config, output_type=pytesseract.Output.DICT
    )

    lines = {}
    n_boxes = len(data['text'])

    for i in range(n_boxes):
        text = data['text'][i].strip()

        # Safely parse confidence rating
        raw_conf = data['conf'][i]
        try:
            conf = int(raw_conf)
        except (ValueError, TypeError):
            conf = -1

        # 3. Filter out empty strings and low-confidence garbage text
        if text and conf > 40:
            line_id = f"{data['block_num'][i]}_{data['par_num'][i]}_{data['line_num'][i]}"

            if line_id not in lines:
                lines[line_id] = {
                    'text_parts': [],
                    'x0': data['left'][i],
                    'y0': data['top'][i],
                    'x1': data['left'][i] + data['width'][i],
                    'y1': data['top'][i] + data['height'][i]
                }

            # 4. Expand line bounding box
            line = lines[line_id]
            line['text_parts'].append(text)
            line['x0'] = min(line['x0'], data['left'][i])
            line['y0'] = min(line['y0'], data['top'][i])
            line['x1'] = max(line['x1'], data['left'][i] + data['width'][i])
            line['y1'] = max(line['y1'], data['top'][i] + data['height'][i])

    # Scale bounding boxes back up to original-image coordinates if we
    # downscaled for OCR.
    inverse_scale = 1.0 / scale_factor if scale_factor != 1.0 else 1.0

    grouped_lines = []
    for line in lines.values():
        grouped_lines.append({
            'text': " ".join(line['text_parts']),
            'bbox': {
                'x0': line['x0'] * inverse_scale,
                'y0': line['y0'] * inverse_scale,
                'x1': line['x1'] * inverse_scale,
                'y1': line['y1'] * inverse_scale,
                'width': (line['x1'] - line['x0']) * inverse_scale,
                'height': (line['y1'] - line['y0']) * inverse_scale
            }
        })

    # 5. Sort top-to-bottom, left-to-right
    grouped_lines.sort(key=lambda item: (item['bbox']['y0'], item['bbox']['x0']))

    return grouped_lines
