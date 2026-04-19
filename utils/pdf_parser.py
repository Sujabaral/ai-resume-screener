import re

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PdfReader = None
    PYPDF2_AVAILABLE = False


def clean_extracted_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\u2022", " ")
    text = text.replace("\u00a0", " ")

    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract_text_pymupdf(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    page_texts = []

    for page in doc:
        blocks = page.get_text("blocks")
        blocks = sorted(blocks, key=lambda b: (b[1], b[0]))
        page_text = "\n".join(block[4].strip() for block in blocks if block[4].strip())
        page_texts.append(page_text)

    doc.close()
    return "\n\n".join(page_texts)


def extract_text_pypdf2(pdf_path: str) -> str:
    if not PYPDF2_AVAILABLE:
        return ""

    reader = PdfReader(pdf_path)
    texts = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            texts.append(page_text)

    return "\n\n".join(texts)


def extract_resume_text(pdf_path: str) -> str:
    text = ""

    if PYMUPDF_AVAILABLE:
        try:
            text = extract_text_pymupdf(pdf_path)
        except Exception:
            text = ""

    if not text or len(text.strip()) < 100:
        try:
            text = extract_text_pypdf2(pdf_path)
        except Exception:
            text = ""

    return clean_extracted_text(text)
