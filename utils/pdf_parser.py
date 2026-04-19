# utils/pdf_parser.py

import re
import fitz  # PyMuPDF
from PyPDF2 import PdfReader


def clean_extracted_text(text: str) -> str:
    if not text:
        return ""

    # Fix unicode spaces and bullets
    text = text.replace("\u2022", " ")
    text = text.replace("\u00a0", " ")

    # Remove repeated spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Fix broken words across line breaks: "develop-\nment" -> "development"
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

    # Convert single line breaks inside sentences into spaces
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    # Keep paragraph breaks
    text = re.sub(r"\n{2,}", "\n\n", text)

    return text.strip()


def extract_text_pymupdf(pdf_path: str) -> str:
    text_chunks = []
    doc = fitz.open(pdf_path)

    for page in doc:
        blocks = page.get_text("blocks")
        # sort top-to-bottom, left-to-right
        blocks = sorted(blocks, key=lambda b: (b[1], b[0]))

        page_text = []
        for block in blocks:
            block_text = block[4].strip()
            if block_text:
                page_text.append(block_text)

        text_chunks.append("\n".join(page_text))

    doc.close()
    return "\n\n".join(text_chunks)


def extract_text_pypdf2(pdf_path: str) -> str:
    text_chunks = []
    reader = PdfReader(pdf_path)

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_chunks.append(page_text)

    return "\n\n".join(text_chunks)


def extract_resume_text(pdf_path: str) -> str:
    text = ""

    try:
        text = extract_text_pymupdf(pdf_path)
    except Exception:
        pass

    if not text or len(text.strip()) < 100:
        try:
            text = extract_text_pypdf2(pdf_path)
        except Exception:
            pass

    return clean_extracted_text(text)