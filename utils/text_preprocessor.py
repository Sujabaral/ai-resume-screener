import re

SKILL_SYNONYMS = {
    "js": "javascript",
    "py": "python",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "nlp",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "tf": "tensorflow",
    "nodejs": "node.js",
    "postgres": "postgresql",
    "problem-solving": "problem solving"
}


def normalize_skill_terms(text: str) -> str:
    text = text.lower()

    for short, full in SKILL_SYNONYMS.items():
        text = re.sub(rf"(?<!\w){re.escape(short)}(?!\w)", full, text)

    return text


def preprocess_text(text: str) -> str:
    if not text:
        return ""

    text = normalize_skill_terms(text)
    text = re.sub(r"[^a-z0-9\s\-\+#\.]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text