#!/bin/bash

[ -d venv ] || python3 -m venv venv
venv/bin/pip3 install -r requirements.txt
# mkdir -pv pero-ocr-master/images pero-ocr-master/output
which tesseract &>/dev/null || echo "tesseract executable not found, please refer to the README"

