# utils/text_preprocessor.py

import re

SKILL_SYNONYMS = {
    "js": "javascript",
    "py": "python",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "tf": "tensorflow",
}


def normalize_skill_terms(text: str) -> str:
    text = text.lower()

    for short, full in SKILL_SYNONYMS.items():
        text = re.sub(rf"\b{re.escape(short)}\b", full, text)

    return text


def preprocess_text(text: str) -> str:
    text = normalize_skill_terms(text)
    text = re.sub(r"[^a-z0-9\s\-\+#\.]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text