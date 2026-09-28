from flask import Flask, render_template, request, send_file
from flask import Flask, render_template, request, jsonify
from pypdf import PdfWriter, PdfReader
import os
import shutil
import pikepdf
from PIL import Image
import io
import pymupdf as fitz
import base64
import json

from pdf_tools.compress_engine import compress_to_target
from pdf_tools.image_engine import compress_image_to_target
from pdf_tools.jpg_to_pdf import images_to_pdf
from pdf_tools.pdf_to_jpg import pdf_to_images
from pdf_tools.ocr_engine import process_image_ocr
from pdf_tools.office_convert import (
    convert_with_libreoffice,
    convert_pdf_to_pdfa,
    convert_pdf_to_word,
    convert_pdf_to_excel,
)

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/merge-page")
def merge_page():
    return render_template("merge.html")

@app.route("/split-page")
def split_page():
    return render_template("split.html")

@app.route("/compress-page")
def compress_page():
    return render_template("compress.html")

@app.route("/image-compress-page")
def image_compress_page():
    return render_template("image_compress.html")

@app.route("/jpg-to-pdf-page")
def jpg_to_pdf_page():
    return render_template("jpg_to_pdf.html")

@app.route("/pdf-to-jpg-page")
def pdf_to_jpg_page():
    return render_template("pdf_to_jpg.html")

@app.route("/editor")
def editor():
    return render_template("editor.html")

@app.route('/remove-pages-page')
def remove_pages_page():
    return render_template('remove_pages.html')

@app.route('/rearrange-pages-page')
def rearrange_pages_page():
    return render_template('rearrange_pages.html')

# Page Routes
@app.route('/protect-pdf-page')
def protect_pdf_page():
    return render_template('protect_pdf.html')

@app.route('/unlock-pdf-page')
def unlock_pdf_page():
    return render_template('unlock_pdf.html')

@app.route('/sign-fill-page')
def sign_fill_page():
    return render_template('sign_fill.html')

@app.route('/redact-pdf-page')
def redact_pdf_page():
    return render_template('redact_pdf.html')


@app.route("/merge", methods=["POST"])
def merge_pdf():

    files = request.files.getlist("pdfs")

    writer = PdfWriter()

    for file in files:

        if file.filename == "":
            continue

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)

        file.save(file_path)

        writer.append(file_path)

    output_path = os.path.join(OUTPUT_FOLDER, "merged.pdf")

    with open(output_path, "wb") as output_file:
        writer.write(output_file)

    return send_file(
        output_path,
        as_attachment=True,
        download_name="merged.pdf"
    )

@app.route("/split", methods=["POST"])
def split_pdf():

    file = request.files.get("pdf")
    pages_input = request.form.get("pages", "").strip()

    if not file or file.filename == "":
        return "Please select a PDF file."

    if not pages_input:
        return "Please enter the pages you want to extract."

    input_path = os.path.join(UPLOAD_FOLDER, "split_input.pdf")

    file.save(input_path)

    try:
        reader = PdfReader(input_path)

        total_pages = len(reader.pages)

        selected_pages = set()

        parts = pages_input.split(",")

        for part in parts:

            part = part.strip()

            if "-" in part:

                start, end = part.split("-", 1)

                start = int(start.strip())
                end = int(end.strip())

                if start > end:
                    return "Invalid page range."

                for page_number in range(start, end + 1):
                    selected_pages.add(page_number)

            else:

                selected_pages.add(int(part))

        for page_number in selected_pages:

            if page_number < 1 or page_number > total_pages:
                return f"Page {page_number} does not exist. This PDF has {total_pages} pages."

        writer = PdfWriter()

        for page_number in sorted(selected_pages):

            writer.add_page(reader.pages[page_number - 1])

        output_path = os.path.join(
            OUTPUT_FOLDER,
            "extracted_pages.pdf"
        )

        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        return send_file(
            output_path,
            as_attachment=True,
            download_name="extracted_pages.pdf"
        )

    except ValueError:
        return "Please enter valid page numbers. Examples: 5-6 or 1,3,5-7."

    except Exception as e:
        return f"Something went wrong: {str(e)}"

def compress_image_data(image_data, quality):
    """
    Compress image data using JPEG compression.
    Returns compressed image bytes.
    """

    image = Image.open(io.BytesIO(image_data))

    # Convert formats that JPEG doesn't support
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    output = io.BytesIO()

    image.save(
        output,
        format="JPEG",
        quality=quality,
        optimize=True
    )

    return output.getvalue()

def try_compress_image(image_data, quality):
    try:
        return compress_image_data(image_data, quality)
    except Exception:
        return None

def recompress_pdf_images(input_path, output_path, quality=60, scale=1.0):
    """
    Recompress images inside a PDF using PyMuPDF + Pillow.
    """

    doc = fitz.open(input_path)

    try:
        for page in doc:

            images = page.get_images(full=True)

            for image in images:

                xref = image[0]

                try:
                    pix = fitz.Pixmap(doc, xref)

                    if pix.width < 50 or pix.height < 50:
                        continue

                    # Get image data as PNG first
                    image_data = pix.tobytes("png")

                    pil_image = Image.open(
                        io.BytesIO(image_data)
                    )

                    # Convert to RGB for JPEG
                    if pil_image.mode != "RGB":
                        pil_image = pil_image.convert("RGB")

                    # Reduce dimensions
                    if scale < 1.0:
                        new_width = max(
                            1,
                            int(pil_image.width * scale)
                        )

                        new_height = max(
                            1,
                            int(pil_image.height * scale)
                        )

                        pil_image = pil_image.resize(
                            (new_width, new_height),
                            Image.Resampling.LANCZOS
                        )

                    # Compress as JPEG
                    output = io.BytesIO()

                    pil_image.save(
                        output,
                        format="JPEG",
                        quality=quality,
                        optimize=True
                    )

                    image_bytes = output.getvalue()

                    page.replace_image(
                        xref,
                        stream=image_bytes
                    )

                except Exception:
                    # Skip images that cannot be safely processed
                    continue

        doc.save(
            output_path,
            garbage=4,
            deflate=True,
            clean=True
        )

    finally:
        doc.close()

@app.route("/compress", methods=["POST"])
def compress_pdf():

    file = request.files.get("pdf")
    target_size = request.form.get("target_size", "")

    if not file or file.filename == "":
        return "Please select a PDF file."

    if target_size == "custom":
        custom_size = request.form.get("custom_size", "").strip()

        if not custom_size:
            return "Please enter a custom target size."

        try:
            target_kb = float(custom_size)
        except ValueError:
            return "Please enter a valid target size."
    else:
        try:
            target_kb = float(target_size)
        except ValueError:
            return "Invalid target size."

    if target_kb < 10:
        return "Please choose a target size of at least 10 KB."

    target_bytes = int(target_kb * 1024)

    input_path = os.path.join(
        UPLOAD_FOLDER,
        "compress_input.pdf"
    )

    file.save(input_path)

    output_path = os.path.join(
    OUTPUT_FOLDER,
    "compressed.pdf"
    )

    compress_to_target(
    input_path,
    output_path,
    int(target_kb)
    )

    # Temporary files for different compression attempts
    attempts = []

    try:

        # -------------------------------------------------
        # Attempt 1: Lossless PDF optimization
        # -------------------------------------------------

        lossless_path = os.path.join(
            OUTPUT_FOLDER,
            "compression_lossless.pdf"
        )

        with pikepdf.open(input_path) as pdf:

            pdf.save(
                lossless_path,
                compress_streams=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate
            )

        lossless_size = os.path.getsize(lossless_path)

        attempts.append(lossless_path)

        # If already below target, use it
        if lossless_size <= target_bytes:

            shutil.copyfile(
                lossless_path,
                os.path.join(
                    OUTPUT_FOLDER,
                    "compressed.pdf"
                )
            )

        else:

            # -------------------------------------------------
            # Attempt 2+: Image recompression
            # -------------------------------------------------

            if target_kb <= 20:
             compression_settings = [
                 (30, 0.60),
                 (25, 0.50),
                 (20, 0.40),
                 (15, 0.35),
                 (10, 0.30),
                 (8, 0.25)
             ]
            elif target_kb <= 50:
             compression_settings = [
                 (40, 0.80),
                 (35, 0.70),
                 (30, 0.60),
                 (25, 0.50),
                 (20, 0.45)
             ]
            else:
             compression_settings = [
                 (80, 1.0),
                 (70, 1.0),
                 (60, 1.0),
                 (50, 1.0),
                 (40, 1.0),
                 (30, 1.0),
                 (25, 0.85),
                 (20, 0.75)
             ]

            best_path = lossless_path
            best_size = lossless_size

            for index, (quality, scale) in enumerate(
                compression_settings
            ):

                attempt_path = os.path.join(
                    OUTPUT_FOLDER,
                    f"compression_attempt_{index}.pdf"
                )

                recompress_pdf_images(
                    input_path,
                    attempt_path,
                    quality=quality,
                    scale=scale
                )

                if not os.path.exists(attempt_path):
                    continue

                attempt_size = os.path.getsize(
                    attempt_path
                )

                attempts.append(attempt_path)

                # Keep the smallest result
                if attempt_size < best_size:

                    best_size = attempt_size
                    best_path = attempt_path

                # Stop as soon as target is reached
                if attempt_size <= target_bytes:
                    best_path = attempt_path
                    best_size = attempt_size
                    break

            # Copy best result to final filename
            shutil.copyfile(
                best_path,
                os.path.join(
                    OUTPUT_FOLDER,
                    "compressed.pdf"
                )
            )

        output_path = os.path.join(
            OUTPUT_FOLDER,
            "compressed.pdf"
        )

        original_size = os.path.getsize(
            input_path
        )

        compressed_size = os.path.getsize(
            output_path
        )

        # -------------------------------------------------
        # Result page
        # -------------------------------------------------

        if compressed_size <= target_bytes:

            message = (
                "<p style='color: green;'>"
                "Target size reached successfully!"
                "</p>"
            )

        else:

            message = (
                "<p style='color: #c0392b;'>"
                "The exact target could not be reached "
                "without potentially damaging the PDF quality."
                "</p>"
            )

        return f"""
        <!DOCTYPE html>
        <html>

        <head>
            <title>Compression Result</title>
        </head>

        <body style="
            font-family: Arial;
            text-align: center;
            padding: 50px;
        ">

            <h1>PDF Compression Complete</h1>

            <p>
                Original size:
                <strong>
                    {original_size / 1024:.1f} KB
                </strong>
            </p>

            <p>
                Final size:
                <strong>
                    {compressed_size / 1024:.1f} KB
                </strong>
            </p>

            <p>
                Target size:
                <strong>
                    {target_kb:g} KB
                </strong>
            </p>

            {message}

            <a href="/download-compressed"
               style="
               display: inline-block;
               background: #e63946;
               color: white;
               padding: 15px 30px;
               text-decoration: none;
               border-radius: 8px;
               ">
                Download Compressed PDF
            </a>

            <br><br>

            <a href="/compress-page">
                Compress another PDF
            </a>

        </body>

        </html>
        """

    except Exception as e:

        return f"""
        <h2>Compression failed</h2>
        <p>{str(e)}</p>
        <a href="/compress-page">
            Try again
        </a>
        """

    finally:

        # Clean up temporary compression attempts
        for path in attempts:

            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

@app.route("/download-compressed")
def download_compressed():
    output_path = os.path.join(
        OUTPUT_FOLDER,
        "compressed.pdf"
    )

    if not os.path.exists(output_path):
        return "Compressed PDF not found."

    return send_file(
        output_path,
        as_attachment=True,
        download_name="compressed.pdf"
    )

@app.route("/compress-image", methods=["POST"])
def compress_image():

    image = request.files.get("image")

    if not image or image.filename == "":
        return "Please select an image."

    target = request.form.get("target")

    if target == "custom":
        custom = request.form.get("custom_kb", "").strip()

        if not custom:
            return "Enter custom KB."

        target_kb = int(custom)

    else:
        target_kb = int(target)

    input_path = os.path.join(
        UPLOAD_FOLDER,
        "image_input"
    )

    output_path = os.path.join(
        OUTPUT_FOLDER,
        "compressed_image.jpg"
    )

    image.save(input_path)

    final_size = compress_image_to_target(
        input_path,
        output_path,
        target_kb
    )

    return send_file(
        output_path,
        as_attachment=True,
        download_name=f"image_{target_kb}KB.jpg"
    )

@app.route("/jpg-to-pdf", methods=["POST"])
def jpg_to_pdf():

    files = request.files.getlist("images")

    if len(files) == 0:
        return "Please select images."

    image_paths = []

    for i, file in enumerate(files):

        path = os.path.join(
            UPLOAD_FOLDER,
            f"image_{i}.jpg"
        )

        file.save(path)

        image_paths.append(path)

    output = os.path.join(
        OUTPUT_FOLDER,
        "images.pdf"
    )

    images_to_pdf(image_paths, output)

    return send_file(
        output,
        as_attachment=True,
        download_name="images.pdf"
    )

@app.route("/pdf-to-jpg", methods=["POST"])
def pdf_to_jpg():

    pdf = request.files.get("pdf")

    if not pdf or pdf.filename == "":
        return "Please select a PDF."

    input_pdf = os.path.join(
        UPLOAD_FOLDER,
        "pdf_input.pdf"
    )

    pdf.save(input_pdf)

    zip_file = pdf_to_images(
        input_pdf,
        OUTPUT_FOLDER
    )

    return send_file(
        zip_file,
        as_attachment=True,
        download_name="pdf_pages.zip"
    )

@app.route('/api/ocr', methods=['POST'])
def handle_ocr():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No image file uploaded'}), 400
            
        file = request.files['file']
        image_bytes = file.read()
        
        # Run OCR with line grouping and sorting
        grouped_lines = process_image_ocr(image_bytes)
        
        # Fixed: Standardized key to "lines"
        return jsonify({'success': True, 'lines': grouped_lines})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

import fitz  # PyMuPDF
import io
from flask import Flask, request, send_file, jsonify

@app.route('/remove-pages', methods=['POST'])
def remove_pages():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    pages_str = request.form.get('pages', '')

    if not pages_str:
        return jsonify({"error": "No pages specified"}), 400

    try:
        # Parse comma-separated pages & ranges (e.g., "1, 3, 5-7")
        pages_to_remove = set()
        for part in pages_str.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                pages_to_remove.update(range(start - 1, end))
            else:
                pages_to_remove.add(int(part) - 1)

        doc = fitz.open(stream=file.read(), filetype="pdf")

        # Delete in reverse order to keep indices stable
        for page_num in sorted(pages_to_remove, reverse=True):
            if 0 <= page_num < len(doc):
                doc.delete_page(page_num)

        # Output to memory buffer
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='Pages_Removed.pdf'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/rearrange-pages', methods=['POST'])
def rearrange_pages():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    order_str = request.form.get('order', '')

    if not order_str:
        return jsonify({"error": "No page order specified"}), 400

    try:
        # Parse page sequence numbers (convert 1-indexed input to 0-indexed list)
        new_page_order = []
        for part in order_str.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                if start <= end:
                    new_page_order.extend(range(start - 1, end))
                else:
                    new_page_order.extend(range(start - 1, end - 2, -1))
            else:
                new_page_order.append(int(part) - 1)

        doc = fitz.open(stream=file.read(), filetype="pdf")

        # Validate page indices
        for p in new_page_order:
            if p < 0 or p >= len(doc):
                return jsonify({"error": f"Page index {p + 1} is out of bounds for a {len(doc)}-page document."}), 400

        # Create new PDF with reordered pages
        new_doc = fitz.open()
        for p in new_page_order:
            new_doc.insert_pdf(doc, from_page=p, to_page=p)

        output = io.BytesIO()
        new_doc.save(output)
        output.seek(0)

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='Rearranged_Document.pdf'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Office / HTML <-> PDF conversions
# ---------------------------------------------------------------------------

@app.route("/word-to-pdf-page")
def word_to_pdf_page():
    return render_template(
        "generic-convert.html",
        title="Word to PDF",
        description="Convert a .docx or .doc file into a PDF.",
        action="/word-to-pdf",
        accept=".doc,.docx",
        button_text="Convert to PDF",
        note="Requires LibreOffice to be installed on the server running this app.",
    )


@app.route("/word-to-pdf", methods=["POST"])
def word_to_pdf():
    file = request.files.get("file")
    if not file or file.filename == "":
        return "Please select a Word file."

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(input_path)

    try:
        output_path = convert_with_libreoffice(input_path, OUTPUT_FOLDER, "pdf")
        return send_file(output_path, as_attachment=True, download_name=os.path.basename(output_path))
    except Exception as e:
        return f"Error converting Word to PDF: {str(e)}"


@app.route("/ppt-to-pdf-page")
def ppt_to_pdf_page():
    return render_template(
        "generic-convert.html",
        title="PowerPoint to PDF",
        description="Convert a .pptx or .ppt file into a PDF.",
        action="/ppt-to-pdf",
        accept=".ppt,.pptx",
        button_text="Convert to PDF",
        note="Requires LibreOffice to be installed on the server running this app.",
    )


@app.route("/ppt-to-pdf", methods=["POST"])
def ppt_to_pdf():
    file = request.files.get("file")
    if not file or file.filename == "":
        return "Please select a PowerPoint file."

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(input_path)

    try:
        output_path = convert_with_libreoffice(input_path, OUTPUT_FOLDER, "pdf")
        return send_file(output_path, as_attachment=True, download_name=os.path.basename(output_path))
    except Exception as e:
        return f"Error converting PowerPoint to PDF: {str(e)}"


@app.route("/excel-to-pdf-page")
def excel_to_pdf_page():
    return render_template(
        "generic-convert.html",
        title="Excel to PDF",
        description="Convert a .xlsx or .xls file into a PDF.",
        action="/excel-to-pdf",
        accept=".xls,.xlsx",
        button_text="Convert to PDF",
        note="Requires LibreOffice to be installed on the server running this app.",
    )


@app.route("/excel-to-pdf", methods=["POST"])
def excel_to_pdf():
    file = request.files.get("file")
    if not file or file.filename == "":
        return "Please select an Excel file."

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(input_path)

    try:
        output_path = convert_with_libreoffice(input_path, OUTPUT_FOLDER, "pdf")
        return send_file(output_path, as_attachment=True, download_name=os.path.basename(output_path))
    except Exception as e:
        return f"Error converting Excel to PDF: {str(e)}"


@app.route("/html-to-pdf-page")
def html_to_pdf_page():
    return render_template(
        "generic-convert.html",
        title="HTML to PDF",
        description="Convert an .html file into a PDF.",
        action="/html-to-pdf",
        accept=".html,.htm",
        button_text="Convert to PDF",
        note="Requires LibreOffice to be installed on the server running this app.",
    )


@app.route("/html-to-pdf", methods=["POST"])
def html_to_pdf():
    file = request.files.get("file")
    if not file or file.filename == "":
        return "Please select an HTML file."

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(input_path)

    try:
        output_path = convert_with_libreoffice(input_path, OUTPUT_FOLDER, "pdf")
        return send_file(output_path, as_attachment=True, download_name=os.path.basename(output_path))
    except Exception as e:
        return f"Error converting HTML to PDF: {str(e)}"


@app.route("/pdf-to-word-page")
def pdf_to_word_page():
    return render_template(
        "generic-convert.html",
        title="PDF to Word",
        description="Convert a PDF into an editable .docx file.",
        action="/pdf-to-word",
        accept=".pdf",
        button_text="Convert to Word",
        note=None,
    )


@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    file = request.files.get("file")
    if not file or file.filename == "":
        return "Please select a PDF file."

    input_path = os.path.join(UPLOAD_FOLDER, "pdf_to_word_input.pdf")
    file.save(input_path)

    try:
        output_path = os.path.join(OUTPUT_FOLDER, "converted.docx")
        convert_pdf_to_word(input_path, output_path)
        return send_file(output_path, as_attachment=True, download_name="converted.docx")
    except Exception as e:
        return f"Error converting PDF to Word: {str(e)}"


@app.route("/pdf-to-ppt-page")
def pdf_to_ppt_page():
    return render_template(
        "generic-convert.html",
        title="PDF to PowerPoint",
        description="Convert a PDF into a .pptx file, one slide per page.",
        action="/pdf-to-ppt",
        accept=".pdf",
        button_text="Convert to PowerPoint",
        note=(
            "This conversion is inherently rough (true even on iLovePDF/Adobe): each "
            "page becomes an image on a slide rather than editable text/shapes, "
            "since PDFs don't store slide layout information. Requires LibreOffice."
        ),
    )


@app.route("/pdf-to-ppt", methods=["POST"])
def pdf_to_ppt():
    file = request.files.get("file")
    if not file or file.filename == "":
        return "Please select a PDF file."

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(input_path)

    try:
        output_path = convert_with_libreoffice(input_path, OUTPUT_FOLDER, "pptx")
        return send_file(output_path, as_attachment=True, download_name=os.path.basename(output_path))
    except Exception as e:
        return f"Error converting PDF to PowerPoint: {str(e)}"


@app.route("/pdf-to-excel-page")
def pdf_to_excel_page():
    return render_template(
        "generic-convert.html",
        title="PDF to Excel",
        description="Extract tables from a PDF into an .xlsx file.",
        action="/pdf-to-excel",
        accept=".pdf",
        button_text="Convert to Excel",
        note="Works best on PDFs with real tables. Scanned/image-only PDFs need OCR first and won't extract cleanly.",
    )


@app.route("/pdf-to-excel", methods=["POST"])
def pdf_to_excel():
    file = request.files.get("file")
    if not file or file.filename == "":
        return "Please select a PDF file."

    input_path = os.path.join(UPLOAD_FOLDER, "pdf_to_excel_input.pdf")
    file.save(input_path)

    try:
        output_path = os.path.join(OUTPUT_FOLDER, "converted.xlsx")
        convert_pdf_to_excel(input_path, output_path)
        return send_file(output_path, as_attachment=True, download_name="converted.xlsx")
    except Exception as e:
        return f"Error converting PDF to Excel: {str(e)}"


@app.route("/pdf-to-pdfa-page")
def pdf_to_pdfa_page():
    return render_template(
        "generic-convert.html",
        title="PDF to PDF/A",
        description="Convert a PDF into the PDF/A archival format.",
        action="/pdf-to-pdfa",
        accept=".pdf",
        button_text="Convert to PDF/A",
        note=(
            "This is a best-effort conversion via LibreOffice, not a guarantee of full "
            "PDF/A compliance for every document — complex layouts may shift slightly."
        ),
    )


@app.route("/pdf-to-pdfa", methods=["POST"])
def pdf_to_pdfa():
    file = request.files.get("file")
    if not file or file.filename == "":
        return "Please select a PDF file."

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(input_path)

    try:
        output_path = convert_pdf_to_pdfa(input_path, OUTPUT_FOLDER)
        return send_file(output_path, as_attachment=True, download_name=os.path.basename(output_path))
    except Exception as e:
        return f"Error converting PDF to PDF/A: {str(e)}"

# Backend: Protect PDF with Password
@app.route('/protect-pdf', methods=['POST'])
def protect_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    password = request.form.get('password', '')

    if not password:
        return jsonify({"error": "Password cannot be empty"}), 400

    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        output = io.BytesIO()

        # Save with user/owner encryption
        doc.save(
            output,
            encryption=fitz.PDF_ENCRYPT_AES_256,
            user_pw=password,
            owner_pw=password
        )
        output.seek(0)

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='Protected_Document.pdf'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Backend: Unlock PDF (Remove Password)
@app.route('/unlock-pdf', methods=['POST'])
def unlock_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    password = request.form.get('password', '')

    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")

        if doc.is_encrypted:
            authenticated = doc.authenticate(password)
            if not authenticated:
                return jsonify({"error": "Incorrect password. Failed to unlock PDF."}), 400

        # Save clean copy without encryption
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='Unlocked_Document.pdf'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sign-fill', methods=['POST'])
def sign_fill():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    page_num = int(request.form.get('page_num', 1)) - 1
    sig_data_url = request.form.get('signature_img', '')
    
    # Get relative dragged coordinates from frontend
    x = float(request.form.get('x', 0))
    y = float(request.form.get('y', 0))
    width = float(request.form.get('width', 150))
    height = float(request.form.get('height', 60))

    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")

        if page_num < 0 or page_num >= len(doc):
            return jsonify({"error": "Page number out of bounds."}), 400

        page = doc[page_num]

        # Insert decoded PNG signature at the user's placed box coordinates: Rect(x0, y0, x1, y1)
        if sig_data_url and "data:image/png;base64," in sig_data_url:
            img_data = base64.b64decode(sig_data_url.split(",")[1])
            rect = fitz.Rect(x, y, x + width, y + height)
            page.insert_image(rect, stream=img_data)

        output = io.BytesIO()
        doc.save(output)
        output.seek(0)

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='Signed_Document.pdf'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/redact-pdf', methods=['POST'])
def redact_pdf():
    file = request.files.get('file')
    redactions_json = request.form.get('redactions')

    if not file or file.filename == '':
        return "Please select a PDF file.", 400

    if not redactions_json:
        return "Please mark at least one area to redact.", 400

    try:
        redactions = json.loads(redactions_json)
    except Exception:
        return "Invalid redaction data.", 400

    if not redactions:
        return "Please mark at least one area to redact.", 400

    input_path = os.path.join(UPLOAD_FOLDER, "redact_input.pdf")
    file.save(input_path)

    try:
        doc = fitz.open(input_path)

        # Mark every rectangle first, then apply per page. add_redact_annot
        # only stages the redaction; apply_redactions() is what actually
        # strips the underlying text/image data - a real, permanent
        # removal, not just drawing a box on top like the Editor's Whiteout.
        touched_pages = set()
        for r in redactions:
            page_index = int(r.get("page", -1))
            if page_index < 0 or page_index >= len(doc):
                continue

            page = doc[page_index]
            rect = fitz.Rect(
                float(r["x"]),
                float(r["y"]),
                float(r["x"]) + float(r["width"]),
                float(r["y"]) + float(r["height"]),
            )
            page.add_redact_annot(rect, fill=(0, 0, 0))
            touched_pages.add(page_index)

        for page_index in touched_pages:
            doc[page_index].apply_redactions()

        output_path = os.path.join(OUTPUT_FOLDER, "redacted.pdf")
        doc.save(output_path)
        doc.close()

        return send_file(output_path, as_attachment=True, download_name="redacted.pdf")

    except Exception as e:
        return f"Error redacting PDF: {str(e)}", 500


if __name__ == "__main__":
    app.run(debug=True)