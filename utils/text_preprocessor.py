import re


def clean_text(text):
    """
    Cleans extracted text by:
    - converting to lowercase
    - removing extra spaces
    - removing special characters except basic punctuation

    Args:
        text (str): Raw text

    Returns:
        str: Cleaned text
    """
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9,.+#/ ]", "", text)

    return text.strip()