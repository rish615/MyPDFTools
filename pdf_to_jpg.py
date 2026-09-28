import pymupdf as fitz
import os
import zipfile

def pdf_to_images(input_pdf, output_folder):

    doc = fitz.open(input_pdf)
    image_paths = []

    for i, page in enumerate(doc):

        pix = page.get_pixmap(dpi=200)

        img_path = os.path.join(
            output_folder,
            f"page_{i+1}.jpg"
        )

        pix.save(img_path)
        image_paths.append(img_path)

    doc.close()

    zip_path = os.path.join(
        output_folder,
        "pdf_images.zip"
    )

    with zipfile.ZipFile(zip_path, "w") as zipf:

        for img in image_paths:

            zipf.write(img, os.path.basename(img))

    return zip_path