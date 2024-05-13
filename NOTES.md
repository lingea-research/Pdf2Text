# Plaintext (and other content; structure, annotations, etc,..) extraction from PDF (with or without text path)

[[_TOC_]]

## 1. Plaintext extraction from text PDF

### Text extraction / structural PDF analysis and output to text or "markup" formats (HTML, DOCX,...)
* OpenOffice (LibreOffice) command-line converter (in headless mode)
  - Conversion of "pdftosrc.pdf" to DOCX, ODT, and even RTF was *flawless*, but did not see good results with HTML (garbled - bad settings?), or TXT (empty - user error? =)). LibreOffice version 7.0.1.1 was used on Linux\
`$ swriter --infilter="writer_pdf_import" --convert-to docx pdftosrc.pdf`\
`$ swriter --infilter="writer_pdf_import" --convert-to odt pdftosrc.pdf`\
`$ swriter --infilter="writer_pdf_import" --convert-to rtf pdftosrc.pdf`

* pdf2txt (pdfminer.six python command-line script _also does HTML output_) _MIT_ license
  - please see "text_html_annot_test.pdf"
* pdftotext / pdftohtml (poppler/Xpdf command-line tools) _GPL-2_ license
  - please see "text_html_annot_test.pdf"
* PDFBox (command-line + Java API) _Apache-2.0_ license
  - t.b.d.
* python modules
  - pdfminer.six (_MIT_ license) / slate3k (_GPL-3.0_ license)
  - pdfplumber _MIT_ license
  - PyMuPDF _GNU Affero General Public_ license
  - PyPDF / PyPDF2 [license](https://github.com/py-pdf/pypdf/blob/main/LICENSE)
  - PDFQuery _MIT_ license

### Annotations
* [pdfannotextractor](https://www.ctan.org/tex-archive/macros/latex/contrib/pax/) _The LaTeX Project Public_ & _GPL_ licenses
  - t.b.d.
  - uses Java PDFBox
  - "does not work with the recent versions of PDFBox, currently only the older versions 0.7.2 or 0.7.3 are supported"
* [leela](https://github.com/TrilbyWhite/Leela) _GPLv3_ license
  - please see "text_html_annot_test.pdf", leela is CLI frontend to poppler-glib library
* PyPDF / PyPDF2
  - [Parse annotations from a pdf](https://stackoverflow.com/questions/1106098/parse-annotations-from-a-pdf)

### Extraction of embedded streams
* pdftosrc (part of pdfTex) _GPL-2_ license
  - please see "pdftosrc.pdf"

## 2. Plaintext extraction from image PDF (OCR)

Try using open OCR libraries (or tools) to extract plaintext from image pdfs (typically scanned documents)

* OCR, possibly after _pdftoppm_ or _pdf2image_ (python wrapper, adds _pdftocairo_) conversion (and processing w / OpenCV, etc,..)
  - Tesseract Optical Character Recognition engine (command-line & python wrapper) _Apache-2.0_ license
    + please see "tesseract_test.pdf" for a sample run
  - [PERO-OCR](https://pero-ocr.fit.vutbr.cz/) (from VÚT) _BSD 3-Clause_ license
  - python: easyocr (_Apache-2.0_ license), NANONETSOCR (_MIT_ license), NoelOCR (_MIT_ license), ocrmypdf (_Mozilla Public License 2.0_), pypdfocr (_Apache-2.0_ license)

To install Tesseract OCR, please refer to [Introduction | Tesseract documentation](https://tesseract-ocr.github.io/tessdoc/Installation.html) or [Installing OCRmyPDF](https://ocrmypdf.readthedocs.io/en/latest/installation.html). It is necessary to install the OCR engine as well as any required language models. In general, Tesseract extracts plain-text content.

To install Pero-OCR, please refer to [DCGM / pero-ocr](https://github.com/DCGM/pero-ocr). It will be necessary to install any python dependencies separately, and set up your PYTHON_PATH, either on the command-line, or user/system-wide as explained in their documentation. You can use the **requirements.txt** file through **init.sh** to install most (all?) Pero-OCR dependencies. In general, Pero-OCR extracts XML content. If you clone this repository, Pero-OCR source code is included (as of January 15, 2024).

Running **init.sh** (above) does not install PyTorch. If you want to support Nvidia or AMD GPUs (and possibly Mac M1 GPUs), install your platform-specific version of PyTorch. It's also possible to run in CPU-only mode. Refer to [Get Started | PyTorch](https://pytorch.org/get-started/) for further instructions, as the following seems to change:

**AMD ROCm**

`./venv/bin/pip3 install torch --index-url https://download.pytorch.org/whl/rocm5.6`

**Nvidia CUDA**

`./venv/bin/pip3 install torch`

**CPU-only**

`./venv/bin/pip3 install torch --index-url https://download.pytorch.org/whl/cpu`

Due to their size, PyTorch language models (.pt extension), are not included here, but can be downloaded from [pero_eu_cz_print_newspapers_2022-09-26.zip](https://nextcloud.fit.vutbr.cz/s/NtAbHTNkZFpapdJ), and should be unzipped to the **pero-ocr-master/engines** directory.

If you are running PyTorch in CPU-only mode, use the **config_cpu.ini** config file, otherwise use the **config.ini** configuration to take advantage of CUDA GPU acceleration. Here is a sample run:

`PYTHONPATH=$PWD/pero-ocr-master:$PYTHONPATH venv/bin/python ./pero-ocr-master/user_scripts/parse_folder.py -c pero-ocr-master/engines/config_cpu.ini --device cpu -i pero-ocr-master/images --output-xml-path pero-ocr-master/output`

## 3. Hybrid Approaches
* extract text & images (maybe use OCR to extract text from them)
* preserve layout, either with whitespace in text, or output to HTML / DOCX / XML / TSV (for tables)

### GROBID
* _Apache-2.0_ license
* _a machine learning library for extracting, parsing, and re-structuring raw documents_
* [How GROBID works](https://grobid.readthedocs.io/en/latest/Principles/)
### Hugging Face _DocumentAI_ transformers
* Microsoft TrOCR
* Donut
* LayoutLM
* LiLT

