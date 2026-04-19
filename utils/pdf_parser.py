from PyPDF2 import PdfReader


def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file page by page.

    Args:
        pdf_path (str): Path to the uploaded PDF file.

    Returns:
        str: Combined extracted text from all pages.
    """
    extracted_text = ""

    try:
        reader = PdfReader(pdf_path)

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                extracted_text += page_text + "\n"

    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

    return extracted_text.strip()