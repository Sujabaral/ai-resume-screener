# utils/jd_parser.py

"""
Job description parsing utilities

Purpose:
- understand the JD in a structured way
- detect domain
- extract required skills
- extract responsibilities
- detect education requirement
- detect experience requirement
- detect seniority level
"""

import re

from utils.constants import EDUCATION_KEYWORDS, RESPONSIBILITY_VERBS, SENIORITY_KEYWORDS
from utils.domain_classifier import detect_job_domain
from utils.skill_extractor import extract_required_skills_from_jd
from utils.text_preprocessor import preprocess_text, split_sentences


def extract_responsibilities(jd_text):
    """
    Extract likely responsibility sentences from the JD.
    Keeps sentences containing action/responsibility verbs.
    """
    sentences = split_sentences(jd_text)
    responsibilities = []

    for sentence in sentences:
        sentence_clean = sentence.strip()
        if not sentence_clean:
            continue

        for verb in RESPONSIBILITY_VERBS:
            if verb in sentence_clean:
                responsibilities.append(sentence_clean)
                break

    return sorted(list(set(responsibilities)))


def extract_education_requirement(jd_text):
    """
    Detect highest education level requested in the JD.
    """
    text = preprocess_text(jd_text)

    detected_levels = []

    for level, keywords in EDUCATION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                detected_levels.append(level)
                break

    priority = ["high_school", "diploma", "bachelor", "master", "phd"]

    highest = None
    highest_index = -1

    for level in detected_levels:
        if level in priority:
            idx = priority.index(level)
            if idx > highest_index:
                highest_index = idx
                highest = level

    return highest if highest else "unknown"


def extract_experience_requirement(jd_text):
    """
    Extract minimum years of experience required from JD.
    Examples:
    - 2 years
    - 3+ years
    - minimum 1 year
    """
    text = preprocess_text(jd_text)

    patterns = [
        r"(\d+)\+?\s+years",
        r"(\d+)\+?\s+year",
        r"minimum\s+(\d+)\s+years",
        r"minimum\s+(\d+)\s+year",
        r"at least\s+(\d+)\s+years",
        r"at least\s+(\d+)\s+year",
        r"(\d+)\s+to\s+\d+\s+years",
        r"(\d+)-\d+\s+years"
    ]

    found_values = []

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                found_values.append(int(match))
            except ValueError:
                continue

    if not found_values:
        return 0

    return min(found_values)


def extract_seniority_from_jd(jd_text):
    """
    Detect likely JD seniority level.
    """
    text = preprocess_text(jd_text)

    scores = {
        "entry_level": 0,
        "mid_level": 0,
        "senior_level": 0
    }

    for level, keywords in SENIORITY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                scores[level] += 1

    best_level = max(scores, key=scores.get)

    if scores[best_level] == 0:
        return "unknown"

    return best_level


def extract_preferred_skills(jd_text, required_skills):
    """
    Try to detect preferred/nice-to-have skill section.
    Basic v2.0 version:
    - find skill mentions in sentences containing 'preferred', 'plus', 'nice to have'
    """
    text = preprocess_text(jd_text)
    sentences = split_sentences(text)

    preferred_markers = [
        "preferred", "nice to have", "plus", "good to have", "added advantage"
    ]

    preferred_text = []

    for sentence in sentences:
        if any(marker in sentence for marker in preferred_markers):
            preferred_text.append(sentence)

    preferred_skills = extract_required_skills_from_jd(" ".join(preferred_text))
    preferred_skills = [skill for skill in preferred_skills if skill not in required_skills]

    return sorted(list(set(preferred_skills)))


def parse_job_description(jd_text):
    """
    Main JD parser.

    Returns structured JD data for scoring.
    """
    if not jd_text or not jd_text.strip():
        return {
            "full_text": "",
            "clean_text": "",
            "domain": "general",
            "required_skills": [],
            "preferred_skills": [],
            "responsibilities": [],
            "education_requirement": "unknown",
            "experience_required": 0,
            "seniority_level": "unknown"
        }

    clean_text = preprocess_text(jd_text)
    required_skills = extract_required_skills_from_jd(clean_text)

    parsed = {
        "full_text": jd_text,
        "clean_text": clean_text,
        "domain": detect_job_domain(clean_text),
        "required_skills": required_skills,
        "preferred_skills": extract_preferred_skills(clean_text, required_skills),
        "responsibilities": extract_responsibilities(clean_text),
        "education_requirement": extract_education_requirement(clean_text),
        "experience_required": extract_experience_requirement(clean_text),
        "seniority_level": extract_seniority_from_jd(clean_text)
    }

    return parsed