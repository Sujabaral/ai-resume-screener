# utils/text_preprocessor.py

"""
Text preprocessing utilities

Combines:
- cleaning
- normalization
- sentence splitting
- keyword preparation

This is used across:
- resume parsing
- job description parsing
- scoring
"""

import re
from utils.normalization import normalize_text


# 🔹 Full preprocessing pipeline
def preprocess_text(text):
    if not text:
        return ""

    # normalize (includes cleaning)
    text = normalize_text(text)

    return text


# 🔹 Split into sentences (for responsibility matching)
def split_sentences(text):
    if not text:
        return []

    # normalize first
    text = normalize_text(text)

    # split by ., ?, !, newline
    sentences = re.split(r"[.\n!?]+", text)

    # remove empty + strip
    sentences = [s.strip() for s in sentences if s.strip()]

    return sentences


# 🔹 Extract keywords (simple version)
def extract_keywords(text):
    if not text:
        return []

    text = normalize_text(text)

    # remove numbers
    text = re.sub(r"\d+", "", text)

    words = text.split()

    # remove very small words (like "a", "an", "to")
    keywords = [w for w in words if len(w) > 2]

    return keywords


# 🔹 Clean section text (for resume sections)
def clean_section_text(text):
    if not text:
        return ""

    # normalize first
    text = normalize_text(text)

    # remove excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


# 🔹 Extract lines (useful for experience parsing)
def extract_lines(text):
    if not text:
        return []

    lines = text.split("\n")

    # clean + remove empty
    lines = [line.strip() for line in lines if line.strip()]

    return lines