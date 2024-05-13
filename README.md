# PDF Text Extraction

[[_TOC_]]

## 1. Installation

To install the Tesseract OCR engine,.. please refer to [Introduction | Tesseract documentation](https://tesseract-ocr.github.io/tessdoc/Installation.html) or [Installing OCRmyPDF](https://ocrmypdf.readthedocs.io/en/latest/installation.html), as this varies between operating systems. You also probably need to have [ghostscript](https://www.ghostscript.com/) installed. PDFToText depends on 
[Poppler](https://poppler.freedesktop.org/) library.

You can install all dependencies with:
```
sudo apt install tesseract-ocr ghostscript build-essential libpoppler-cpp-dev pkg-config
```

It is also necessary to (usually separately) install any required language models. Note that any language specified for either command-line or web-API will be included to be tried in converting PDF to text, and if not found in the available language models, will throw an error. Languages consist of 3-digit codes as used by both OCRmyPDF and Tesseract. Note that in general, the fewer languages the better the chance of getting a good result, because all of them will be tried. Multiple languages are delimited with a "+" symbol, e.g.; `-l eng+spa`

Future versions of the __init.sh__ script may attempt to automatically detect the operating system (among a limited set), then install the Tesseract Engine, as well the language models passed to it as a parameter.

Run __init.sh__ to create a virtual environment (optional), and install required Python modules and dependencies.

## 2. Running the script

Files with a text path will not be OCR'd, text will simply be extracted.

Here are some sample runs. Both applications output a help if called with "-h":

### API

Run as a FastAPI server running on the configured port:

`$ ./venv/bin/python pdfextract_web.py --host 127.0.0.1 -p 1234 -ll QUIET`

Text (and potentially metadata) will be returned as a JSON response.
Navigate to http://127.0.0.1:1234/docs to see the API. It is also possible to test queries here.

The API returns only a JSON response, but future versions may include XML, PAGE XML, or ALTO XML. If the **metadata** parameter is set, binary fields (images, source documents, etc,..) will be Base64-Encoded. Metadata is not yet implemented (*see below).

### Command-Line tool

Process parameters as local files or directories (batch-processing). All output will be written to files named "*PDF_SOURCE_FILE*.*FORMAT*" in the configured output directory, or as a single stream to STDOUT, as defined by the **output_path** parameter. To stream to STDOUT, define output_path as STDOUT (this is the default).

`$ ./venv/bin/python pdfextract.py -l eng+spa -ll ERROR -op /tmp/pdf_output foo.pdf /home/PDFS_DIR/ http://www.foo.org/foo.pdf`

Different formats are supported with the **format** parameter: JSON, TXT, and XML. TXT only applies to the command-line. By default, a log file is written in "append" mode by the web application, and output to STDERR by the command-line application with a log level of "INFO", which can be a bit chatty (especially for OCR). To override this level, set **loglevel** to "ERROR" or "QUIET" (for no logging).

*Future versions of the application may also extract annotations, attempt to preserve structure (as HTML), and store other source objects contained in the PDF (images, original source document, etc,..) for further processing.

