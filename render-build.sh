#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Tesseract OCR system packages
apt-get update && apt-get install -y tesseract-ocr libtesseract-dev

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
