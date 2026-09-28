from PIL import Image
import io
import os

def compress_image_to_target(input_path, output_path, target_kb):

    target_bytes = target_kb * 1024

    image = Image.open(input_path)

    if image.mode != "RGB":
        image = image.convert("RGB")

    low = 5
    high = 95

    best_data = None
    best_diff = float("inf")

    while low <= high:

        quality = (low + high) // 2

        buffer = io.BytesIO()

        image.save(
            buffer,
            format="JPEG",
            quality=quality,
            optimize=True
        )

        data = buffer.getvalue()

        diff = abs(len(data) - target_bytes)

        if diff < best_diff:
            best_diff = diff
            best_data = data

        if len(data) > target_bytes:
            high = quality - 1
        else:
            low = quality + 1

    with open(output_path, "wb") as f:
        f.write(best_data)

    return os.path.getsize(output_path)