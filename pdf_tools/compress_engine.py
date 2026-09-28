
import pymupdf as fitz
from PIL import Image
import io
import os
import tempfile

def _render_pdf(input_pdf, output_pdf, dpi, quality):
    doc = fitz.open(input_pdf)
    out = fitz.open()

    for page in doc:
        pix = page.get_pixmap(dpi=dpi)

        img = Image.open(io.BytesIO(pix.tobytes("png")))

        if img.mode != "RGB":
            img = img.convert("RGB")

        buffer = io.BytesIO()
        img.save(
            buffer,
            format="JPEG",
            quality=quality,
            optimize=True
        )

        new_page = out.new_page(
            width=page.rect.width,
            height=page.rect.height
        )

        new_page.insert_image(
            page.rect,
            stream=buffer.getvalue()
        )

    out.save(output_pdf, garbage=4, deflate=True)
    out.close()
    doc.close()


def compress_to_target(input_pdf, output_pdf, target_kb):

    target = target_kb * 1024

    # Fast preset based on target
    if target_kb <= 20:
        dpi = 72
    elif target_kb <= 50:
        dpi = 96
    elif target_kb <= 100:
        dpi = 120
    else:
        dpi = 150

    low = 5
    high = 95

    best_file = None
    best_diff = 10**18

    for _ in range(7):     # only 7 attempts

        quality = (low + high) // 2

        temp = tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False
        )

        temp.close()

        _render_pdf(
            input_pdf,
            temp.name,
            dpi,
            quality
        )

        size = os.path.getsize(temp.name)
        diff = abs(size - target)

        if diff < best_diff:

            if best_file and os.path.exists(best_file):
                os.remove(best_file)

            best_file = temp.name
            best_diff = diff

        else:
            os.remove(temp.name)

        if size > target:
            high = quality - 1
        else:
            low = quality + 1

    os.replace(best_file, output_pdf)

    return os.path.getsize(output_pdf)