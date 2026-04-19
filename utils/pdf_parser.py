# utils/pdf_parser.py

"""
PDF parsing utilities

Primary extractor:
- PyMuPDF (fitz)

Fallback extractor:
- PyPDF2

Why this file matters:
- resumes often have messy formatting
- PyMuPDF usually extracts cleaner text than PyPDF2
"""

from io import BytesIO

import fitz  # PyMuPDF
from PyPDF2 import PdfReader


def extract_text_with_pymupdf(file_stream):
    """
    Extract text using PyMuPDF.
    Accepts bytes or a file-like object.
    """
    text_chunks = []

    if hasattr(file_stream, "read"):
        file_bytes = file_stream.read()
    else:
        file_bytes = file_stream

    if not file_bytes:
        return ""

    pdf_document = fitz.open(stream=file_bytes, filetype="pdf")

    for page in pdf_document:
        page_text = page.get_text("text")
        if page_text:
            text_chunks.append(page_text)

    pdf_document.close()
    return "\n".join(text_chunks).strip()


def extract_text_with_pypdf2(file_stream):
    """
    Fallback extraction using PyPDF2.
    Accepts bytes or a file-like object.
    """
    text_chunks = []

    if hasattr(file_stream, "read"):
        file_bytes = file_stream.read()
    else:
        file_bytes = file_stream

    if not file_bytes:
        return ""

    pdf_reader = PdfReader(BytesIO(file_bytes))

    for page in pdf_reader.pages:
        try:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)
        except Exception:
            continue

    return "\n".join(text_chunks).strip()


def extract_text_from_pdf(uploaded_file):
    """
    Main PDF extraction function.

    Tries PyMuPDF first, then falls back to PyPDF2.
    Works with Flask uploaded files.
    """
    try:
        file_bytes = uploaded_file.read()
    except Exception:
        return ""

    if not file_bytes:
        return ""

    # Reset pointer if possible
    try:
        uploaded_file.seek(0)
    except Exception:
        pass

    text = ""

    # Try PyMuPDF first
    try:
        text = extract_text_with_pymupdf(file_bytes)
    except Exception:
        text = ""

    # Fallback to PyPDF2 if needed
    if not text.strip():
        try:
            text = extract_text_with_pypdf2(file_bytes)
        except Exception:
            text = ""

    return text.strip()


def is_pdf_file(filename):
    """
    Basic PDF filename validation.
    """
    return bool(filename) and filename.lower().endswith(".pdf")