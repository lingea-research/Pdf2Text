"""
web API for PDF text & OCR extraction
Uses pdfextract module to provide features similar to command-line tool
visit http://host:port/docs for API documentation
Run with "-h" for usage
"""

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from os import path
from pathlib import Path
from pydantic import BaseModel, HttpUrl, field_validator
from sys import stderr
from tempfile import TemporaryDirectory
import logging
import uvicorn

import pdfextract

_SCRIPT_NAME_ = path.basename(__file__)
args = pdfextract.parse_params(app_mode="WEBAPI")

pdfextract.set_up_logging(
    args.log_level, "STDERR"
)  # TODO: also log to a file if so configured

# TODO: return meaningful error for bad langs or Tesseract timeout (from pdfextract module)


# -----------------------------------------------------------------------------
class Location(BaseModel):
    "takes a Pydantic HttpUrl or pathlib Path and validates it as a resource Location. Will be used as a PDF"
    url_or_path: HttpUrl | Path

    @field_validator("url_or_path")
    def validate_location(cls, v, values, **kwargs):
        if isinstance(v, Path):
            if not v.exists or (not v.is_dir() and not v.is_file()):
                raise ValueError(
                    f'cannot access file path "{v}" and it doesn\'t look like a valid URL'
                )
        return v  # validating URLs more than pydantic already did seems expensive this early


# -----------------------------------------------------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/location")
async def pdfextract_list(
    locations: list[Location], timeout: int | None = None, langs: str | None = None
):
    "takes a list of strings, initializes them as Location objects, then processes them as PDFs to extract text, etc,.. returns JSON HTTP response"
    # TODO: should this be limited to localhost or certain dirs? for now filesystem perms are per user running this script
    results = []
    for loc in [l.url_or_path for l in locations]:
        if isinstance(loc, Path):
            if loc.is_file():
                results.append(
                    pdfextract.process_file_or_url(
                        loc, languages=langs, tesseract_timeout=timeout
                    )
                )
            elif loc.is_dir():
                results.extend(
                    pdfextract.process_dir(
                        loc, languages=langs, tesseract_timeout=timeout
                    )
                )
        else:  # assuming HttpUrl
            results.append(
                pdfextract.process_file_or_url(
                    loc, languages=langs, tesseract_timeout=timeout
                )
            )
    return results


# -----------------------------------------------------------------------------
@app.post("/upload")
async def pdfextract_upload(
    file: UploadFile, timeout: int | None = None, langs: str | None = None
):
    "takes PDF file upload as HTTP multi-part request, extracts text, etc,.. returns JSON HTTP response"
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=422, detail="upload must be a PDF file")
    return pdfextract.process_file_or_url(
        file, languages=langs, tesseract_timeout=timeout
    )


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    "main function called when script is run, parsed cmdline args, inits logging, then starts app with uvicorn"
    uvicorn_loglevel = (
        "critical" if args.log_level == "QUIET" else args.log_level.lower()
    )

    print(f"uvicorn_loglevel: {uvicorn_loglevel}", file=stderr)

    # TODO: this is a dev server... use with Gunicorn or ? ( and reload=False) in production
    uvicorn.run(
        "pdfextract_web:app",
        host=args.host,
        port=args.port,
        log_level=uvicorn_loglevel,
        reload=True,
    )
