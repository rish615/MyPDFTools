FROM python:3.11-slim

# System dependencies:
# - tesseract-ocr: required by pytesseract for the OCR tool
# - libreoffice-writer/calc/impress: required by office_convert.py for
#   Word/Excel/PowerPoint <-> PDF conversions (the full "libreoffice"
#   package pulls in far more than needed and makes the image much larger
#   and slower to build, so only the specific apps are installed here)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads output

# --timeout 180: OCR and LibreOffice conversions can take a while,
# especially on a resource-limited server - gunicorn's default 30s timeout
# was killing the worker mid-OCR before, which is what caused the
# "WORKER TIMEOUT" + "Perhaps out of memory?" errors.
# --workers 2: keep worker count modest since each one loads the full app
# (PyMuPDF, PIL, etc.) into memory - too many workers on a low-RAM plan
# competes for the same limited memory instead of helping.
# Render sets $PORT itself; falls back to 10000 for local testing.
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-10000} --timeout 180 --workers 2
