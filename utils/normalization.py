# utils/normalization.py

"""
Text normalization utilities

Purpose:
- Convert different variations of words into a standard form
- Improve matching accuracy across resumes and job descriptions
"""

import re

# 🔹 Synonym / normalization mapping
NORMALIZATION_MAP = {
    # Excel variations
    "ms excel": "excel",
    "microsoft excel": "excel",

    # Customer support variations
    "customer support": "client support",
    "customer service": "client support",
    "client servicing": "client support",

    # HR variations
    "hr": "human resources",
    "recruiting": "recruitment",
    "talent acquisition": "recruitment",

    # Finance variations
    "book keeping": "bookkeeping",
    "accounts": "accounting",

    # Marketing variations
    "seo writing": "seo",
    "social media marketing": "social media",

    # Sales variations
    "sales and marketing": "sales marketing",
    "business dev": "business development",

    # Tech variations
    "js": "javascript",
    "node": "node.js",
    "reactjs": "react",
    "ml": "machine learning",
    "ai": "artificial intelligence",

    # General
    "team work": "teamwork",
    "problem-solving": "problem solving",
    "time-management": "time management"
}


# 🔹 Clean raw text
def clean_text(text):
    if not text:
        return ""

    text = text.lower()

    # remove special characters (keep words + spaces)
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


# 🔹 Apply normalization map
def normalize_text(text):
    if not text:
        return ""

    text = clean_text(text)

    for key, value in NORMALIZATION_MAP.items():
        text = text.replace(key, value)

    return text


# 🔹 Tokenize into words
def tokenize(text):
    text = normalize_text(text)
    return text.split()


# 🔹 Normalize + deduplicate words
def normalize_and_deduplicate(text):
    tokens = tokenize(text)
    return list(set(tokens))