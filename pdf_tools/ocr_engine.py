import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

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

def process_image_ocr(image_bytes, lang='eng'):
    """
    Processes image bytes using pytesseract:
    1. Normalizes image color space to RGB.
    2. Filters out low-confidence OCR noise (conf <= 40).
    3. Groups words into complete lines by block & line IDs.
    4. Sorts lines top-to-bottom (y0) and left-to-right (x0).
    """
    # 1. Normalize image mode to RGB for consistent processing
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # PSM 6 tells Tesseract to treat the image as a single uniform block of
    # text and read it in reading order, which handles table-like rows
    # (side-by-side cells) more sensibly than the default auto-layout mode —
    # the default mode is what was causing side-by-side cells like "Gender"
    # and "Nationality" to sometimes get merged into one oversized line.
    custom_config = "--psm 6"
    data = pytesseract.image_to_data(
        image, lang=lang, config=custom_config, output_type=pytesseract.Output.DICT
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

        # 2. Filter out empty strings and low-confidence garbage text
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
            
            # 3. Expand line bounding box
            line = lines[line_id]
            line['text_parts'].append(text)
            line['x0'] = min(line['x0'], data['left'][i])
            line['y0'] = min(line['y0'], data['top'][i])
            line['x1'] = max(line['x1'], data['left'][i] + data['width'][i])
            line['y1'] = max(line['y1'], data['top'][i] + data['height'][i])

    grouped_lines = []
    for line in lines.values():
        grouped_lines.append({
            'text': " ".join(line['text_parts']),
            'bbox': {
                'x0': line['x0'],
                'y0': line['y0'],
                'x1': line['x1'],
                'y1': line['y1'],
                'width': line['x1'] - line['x0'],
                'height': line['y1'] - line['y0']
            }
        })
            
    # 4. Sort top-to-bottom, left-to-right
    grouped_lines.sort(key=lambda item: (item['bbox']['y0'], item['bbox']['x0']))
    
    return grouped_lines
