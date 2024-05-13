"""
command-line tool and Python module
Extracts information from PDFs, mostly text, but potentially also metadata
Run with "-h" for command-line help
Attempts to extract text directly from PDF text stream, fallback to OCR as necessary
"""

from argparse import ArgumentParser, Namespace
from dicttoxml import dicttoxml
from io import IOBase
from os import _exit, linesep, mkdir, path, remove
from pathlib import Path
from pydantic import HttpUrl
from re import compile as _compile, search, split as _split
from shutil import copyfileobj
from socket import setdefaulttimeout
from starlette import datastructures
from sys import argv, stderr, stdout
from tempfile import NamedTemporaryFile

import json
import logging
import ocrmypdf
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

import urllib.error, urllib.parse, urllib.request

# TODO: could this just be handled by one glob for dirs & files?
PDF_RE = _compile(r"\.pdf$")
URL_RE = _compile(r"^https?://")
# may need to revise this if OCRmyPDF output changes
OCR_SKIP_PAGES_RE = _compile(r"^\[OCR skipped on page\(s\) ([0-9-]+)\]$")
_SCRIPT_NAME_ = path.basename(__file__)
OUTPUT_DIR_MODE = 0o755
LOGLEVELS = ["ERROR", "INFO", "QUIET"]
SUPPORTED_FORMATS = ["JSON", "TXT", "XML"]
LANGUAGES = "eng"
TESSERACT_TIMEOUT = 59  # seconds
HTTP_SOCK_TIMEOUT = 15  # seconds

# -----------------------------------------------------------------------------


def parse_params(app_mode: str = "CMDLINE") -> Namespace:
    "parses command-line args, some different for CMDLINE or WEBAPI mode"
    parser = ArgumentParser()

    parser.add_argument(
        "-ll",
        "--log_level",
        choices=LOGLEVELS,
        default="INFO",
        help=f"optional: {', '.join(LOGLEVELS)}. If not specified, defaults to INFO",
    )

    if app_mode == "CMDLINE":
        parser.add_argument(
            "-l",
            "--languages",
            default="eng",
            help="optional: list of languages to try OCR, delimited by '+', e.g.; 'eng+spa'. Defaults to 'eng'",
        )
        parser.add_argument(
            "-m",
            "--metadata",
            action="store_true",
            help="Also extract binary fields (images, source docs), and annotations. If output_path is 'STDOUT',"
            + " binary fields will be Base64-Encoded. *metadata not yet implemented and is ignored",
        )
        parser.add_argument(
            "-of",
            "--output_format",
            choices=SUPPORTED_FORMATS,
            default="TXT",
            help=f"optional: {', '.join(SUPPORTED_FORMATS)}. If not specified, defaults to TXT",
        )
        parser.add_argument(
            "-op",
            "--output_path",
            default="STDOUT",
            help="optional: Directory to write result files to, or stream to STDOUT. Defaults to STDOUT",
        )
        parser.add_argument(
            "-t",
            "--tesseract_timeout",
            type=int,
            default=59,
            help="maximum number of seconds to spend on OCR operation, not including image processing",
        )
        parser.add_argument(
            "input_paths",
            nargs="+",
            help="files, directories, or URLs to process PDFs from",
        )

    if app_mode == "WEBAPI":
        parser.add_argument(
            "-c",
            "--cors-origin",
            nargs="*",
            default="*",
            help='optional: specify 1 or more origins for CORS requests. Origin of "*" (default) means all are allowed',
        )
        parser.add_argument(
            "--host",
            default="127.0.0.1",
            help="optional: run uvicorn/gunicorn as this host. Defaults to '127.0.0.1'",
        )
        parser.add_argument(
            "-p",
            "--port",
            type=int,
            default=8080,
            help="optional: run uvicorn/gunicorn on this port. Defaults to 8080.",
        )
    return parser.parse_args()


# -----------------------------------------------------------------------------
def set_up_logging(loglevel: str, logpath: str):
    "takes loglevel in {QUIET,ERROR,INFO} and a logpath, configures logging module and OCRmyPDF loglevel"
    if loglevel in ["ERROR", "INFO"]:
        if logpath == "STDERR":
            logging.basicConfig(
                format="%(asctime)s %(message)s", level=loglevel, stream=stderr
            )
        else:
            logging.basicConfig(
                format="%(asctime)s %(message)s",
                level=loglevel,
                filename=logpath,
                encoding="utf-8",
            )
    else:
        logging.disable(logging.CRITICAL)

    ocrmypdf.configure_logging(
        ocrmypdf.Verbosity.default if loglevel == "INFO" else ocrmypdf.Verbosity.quiet
    )


# -----------------------------------------------------------------------------
def download_file(url: str) -> None | str:
    """
    takes URL, attempts to download file, returns it as NamedTemporaryFile name or None if failed.
    catches HTTPError, URLError, Value & Type-Error
    """
    # TODO: async?
    req = urllib.request.Request(url)
    try:
        resp = urllib.request.urlopen(req, timeout=HTTP_SOCK_TIMEOUT)
    except urllib.error.HTTPError as e:
        logging.error(f'download "{url}" failed with code {e.code}: "{e.reason}"')
    except urllib.error.URLError as e:
        logging.error(f'download "{url}" failed: "{e.reason}"')
    except (TypeError, ValueError) as e:
        logging.error(f'download "{url}" failed: "{e}"')
    else:
        tmp_file = NamedTemporaryFile(
            prefix=_SCRIPT_NAME_, suffix=".pdf",
            delete=False
        )
        copyfileobj(resp, tmp_file)
        tmp_file.seek(0)
        return tmp_file.name
    return None


# -----------------------------------------------------------------------------
def file_details(
    resource: Path | datastructures.UploadFile | HttpUrl | str,
) -> tuple[Path | IOBase | None, str]:
    "takes local file Path or UploadFile, or URL (calls download_file on it), returns file object, and a basename"
    file_obj = basename = None

    if isinstance(resource, Path):
        file_obj = Path.resolve(resource)
        logging.info(f'Processing "{file_obj}"')
        if not file_obj.is_file():
            file_obj = None
        else:
            basename = resource.name
    elif isinstance(resource, datastructures.UploadFile):
        basename = resource.filename
        tmp_file = NamedTemporaryFile(
            prefix=_SCRIPT_NAME_, suffix=".pdf",
            delete=False
        )
        tmp_file.write(resource.file.read())
        tmp_file.seek(0)
        file_obj = Path(tmp_file.name)
        logging.info(f'Processing uploaded file "{basename}"')
    else:  # assuming URL
        resource = str(resource)
        logging.info(f'Processing "{resource}"')
        url_parts = urllib.parse.urlparse(resource)
        basename = urllib.parse.quote(url_parts.path.split("/")[-1])
        s = url_parts.scheme.lower()
        # other schemes (ftp, etc,..)?
        if (
            (s != "http" and s != "https")
            or len(url_parts.netloc) == 0
            or len(basename) == 0
        ):
            logging.error(f'URL "{resource}" seems to be malformed, not downloading')
            file_obj = None
        else:
            file_obj = download_file(resource)
    return file_obj, basename


# -----------------------------------------------------------------------------
def process_text_path(file_obj: Path | IOBase) -> list[str] | None:
    "takes PDF resource, processes pages containing text, returns list of text str in pages"
    # TODO: tables ( PDFplumber), images, annotations
    pdf_text = []
    try:
        for page_layout in extract_pages(file_obj):
            page_text = ""
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    page_text += linesep + element.get_text().strip() + linesep
            pdf_text.append(page_text)
    except Exception as e:  # TODO: investig8 specific PDFminer exceptions
        logging.error(f"PDFminer oops: {e}")
    return pdf_text


# -----------------------------------------------------------------------------
def process_ocr_path(file_obj: Path | IOBase, languages: str, tesseract_timeout: int
                     ) -> list[str] | None:
    # TODO: could memory be an issue? https://github.com/ocrmypdf/OCRmyPDF/issues/115
    # TODO: supporting GPUs? see https://github.com/ocrmypdf/OCRmyPDF/issues/221
    # TODO: look into options --rotate-pages, --remove-background, --clean, --invalidate-digital-signatures, --max-image-mpixels, --rotate-pages-threshold, all --tesseract* (see ocrmypdf --help)
    "takes PDF resource, processes OCR pages, returns list of text in pages"
    tmp_file = NamedTemporaryFile(prefix=_SCRIPT_NAME_, suffix=".txt")
    try:
        result = ocrmypdf.ocr(
            file_obj,
            path.devnull,
            continue_on_soft_render_error=True,
            deskew=True,
            language=languages,
            output_type="none",
            progress_bar=False,
            sidecar=tmp_file.name,
            skip_text=True,
            # force_ocr=True,
            tesseract_timeout=tesseract_timeout,
        )
        with open(tmp_file.name, "rb") as rfp:
            text = str(rfp.read(), "utf-8")
    except Exception as e:
        # TODO: some exceptions may be recoverable or have a "workaround"; not
        # necessarily result in "fail"
        logging.error(f"OCRmyPDF oops: {e}")
        return None
    return insert_skipped_pages([p.strip() for p in text.split("\f")])


# -----------------------------------------------------------------------------
def insert_skipped_pages(pages: list) -> list:
    "replaces OCRmyPDF compressed skip pages output with blank pages in list"
    _pages = []
    for page in pages:
        if len(page) < 100:    # otherwise too long to be page skip text
            matched = search(OCR_SKIP_PAGES_RE, _split(r"[\r\n]+", page, maxsplit=1)[0])
            if matched:
                _range = matched.group(1).split("-")
                start = int(_range[0])
                end = int(_range[1]) if len(_range) > 1 else start
                count_skip_page = end - start + 1
                _pages.extend([""] * count_skip_page)
                continue
        _pages.append(page)
    return _pages


# -----------------------------------------------------------------------------
def process_file_or_url(
    resource: Path | datastructures.UploadFile | HttpUrl | str,
    languages: str | None = None,
    tesseract_timeout: int | None = None,
) -> dict:
    "takes PDF resource, tries text extraction through text path, then OCR. returns dict with fail/success status, basename, text, and page count"
    if languages is None:
        languages = LANGUAGES
    if tesseract_timeout is None:
        tesseract_timeout = TESSERACT_TIMEOUT

    resource_temporary = not isinstance(resource, Path)
    file_obj, basename = file_details(resource)
    ret_val = {"name": resource, "status": "fail"}

    if file_obj is None:
        logging.error(f'failed to locate FileOrURL "{resource}"')
        return ret_val
    ret_val["name"] = basename

    pages_text_path = process_text_path(file_obj)  # could be None on Error
    count_page = len(pages_text_path)  # this also applies to OCR-only PDFs
    ret_val["count_page"] = count_page
    pages_ocr_path = process_ocr_path(file_obj, languages, tesseract_timeout)

    if hasattr(file_obj, "close"):
        file_obj.close()
    if (isinstance(file_obj, str) or isinstance(file_obj, Path)) and resource_temporary:
        remove(file_obj)

    pages = []
    for page_ind, page in enumerate(pages_text_path, 1):  # 1-based counting  :-D
        ocr_path = pages_ocr_path[page_ind - 1] if len(pages_ocr_path) >= page_ind else ""
        pages.append({"page_ind": page_ind, "text_path": page,
                     "ocr_path": ocr_path})

    return {
        "name": basename,
        "count_page": count_page,
        "status": "success",
        "pages": pages
    }


# -----------------------------------------------------------------------------
def get_all_text(pdf: dict) -> str:
    "takes processed PDF dictionary and returns OCR & text paths concatenated"
    delim = (linesep + linesep)
    return delim.join([p["text_path"] + p["ocr_path"] for p in pdf["pages"]])


# -----------------------------------------------------------------------------
def process_dir(
    d: Path, languages: str | None = None, tesseract_timeout: int | None = None
) -> list:
    "takes local directory path, PDF batch processes it, returns list of objects returned by process_file_or_url"
    if languages is None:
        languages = LANGUAGES
    if tesseract_timeout is None:
        tesseract_timeout = TESSERACT_TIMEOUT

    results = []
    for filename in d.glob("**/*.pdf"):
        _path = Path(filename)
        if not _path.is_file:
            print(
                f'path "{filename}" is not a regular file, or cannot be read, skipping...'
            )
        results.append(process_file_or_url(_path, languages, tesseract_timeout))
    return results


# -----------------------------------------------------------------------------
def create_output_dir(_path: str) -> bool:
    "attempts to create local directory _path to write extracted text and potentially metadata to separate files"
    outpath = Path(_path)
    if outpath.exists():
        # TODO: but is it accessible?
        if outpath.is_dir():
            logging.info(f'writing results files to "{_path}"')
            return True
        else:
            logging.error(
                f'OUTPUT_PATH "{_path}" exists, but does not appear to be a directory'
            )
            return False
    try:
        mkdir(_path, OUTPUT_DIR_MODE)
    except Exception as e:
        logging.error(f'cannot create output directory "{_path}": {e}')
        return False
    logging.info(f'writing results files to "{_path}"')
    return True


# -----------------------------------------------------------------------------
def main():
    "main function called when running command-line tool"
    global LANGUAGES, TESSERACT_TIMEOUT

    setdefaulttimeout(HTTP_SOCK_TIMEOUT)

    args = parse_params()
    set_up_logging(args.log_level, "STDERR")

    "a little more config validation"
    if args.output_path != "STDOUT" and args.output_format != "TXT":
        logging.error(
            f'format "{args.output_format}" can only be used with STDOUT'
        )  # not yet implemented
        _exit(0)

    "prepare output dir if necessary, and set globals"
    if args.output_path != "STDOUT":
        if not create_output_dir(args.output_path):
            _exit(0)
    LANGUAGES = args.languages
    TESSERACT_TIMEOUT = args.tesseract_timeout

    "process loop"
    results = []
    for arg in args.input_paths:

        if search(URL_RE, arg):
            results.append(process_file_or_url(arg))
            continue
        _path = Path(arg)

        if not _path.exists():
            logging.info(f'path "{arg}" not found, skipping...')
        elif _path.is_file():
            if search(PDF_RE, arg):
                results.append(process_file_or_url(_path))
            else:
                logging.info(f'path "{arg}" does not seem to be a PDF, skipping...')
        elif _path.is_dir():
            results.extend(process_dir(_path))
        else:
            logging.info(
                f'path "{arg}" is neither a regular file, URL, nor directory, or cannot be read; skipping...'
            )

    "output results"
    if args.output_path == "STDOUT":
        "writing results to stdout in some format"
        if args.output_format == "TXT":
            # TODO: find some standard way to delimit these if it even makes sense
            for ii, pdf in enumerate(results, 1):  # 1-based counting
                if pdf["status"] == "success":
                    all_text = get_all_text(pdf)
                    stdout.write(
                        f"--- {ii:03} {pdf['name']} {pdf['count_page']}pages\n{all_text}\n"
                    )
                else:
                    logging.error(f"{ii}: failed to process PDF file \"{pdf['name']}\"")
        elif args.output_format == "JSON":
            stdout.write(json.dumps(results))
        elif args.output_format == "XML":
            stdout.write(dicttoxml(results).decode("utf-8"))
    else:
        "writing separate text files to a directory"
        for ii, pdf in enumerate(results):  # 1-based counting
            if pdf["status"] == "success":
                all_text = get_all_text(pdf)
                outfilepath = path.join(
                    args.output_path, f"{pdf['name']}-pdfextract{ii:03}.txt"
                )
                try:
                    with open(outfilepath, "w", encoding="utf-8") as wfp:
                        wfp.write(all_text)
                except Exception as e:
                    logging.error(
                        f'failed to write extract results file "{outfilepath}": {e}'
                    )
            else:
                logging.error(f"{ii}: failed to process PDF file \"{pdf['name']}\"")


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
