# utils/jd_parser.py

"""
Job description parsing utilities (Version 2.0)

Purpose:
- structured JD understanding
- domain detection
- skill extraction (required + preferred)
- responsibility extraction (stronger logic)
- education & experience detection
- seniority detection
"""

import re

from utils.constants import EDUCATION_KEYWORDS, RESPONSIBILITY_VERBS, SENIORITY_KEYWORDS
from utils.domain_classifier import detect_job_domain, get_domain_confidence
from utils.skill_extractor import extract_required_skills_from_jd
from utils.text_preprocessor import preprocess_text, split_sentences


# ----------------------------
# RESPONSIBILITY EXTRACTION
# ----------------------------

def extract_responsibilities(jd_text):
    """
    Extract likely responsibility sentences.

    Improved logic:
    - detects action verbs
    - prioritizes longer sentences
    - removes noise
    """
    sentences = split_sentences(jd_text)
    responsibilities = []

    for sentence in sentences:
        sentence_clean = sentence.strip().lower()

        if not sentence_clean or len(sentence_clean.split()) < 5:
            continue

        # Must contain responsibility verb
        if any(verb in sentence_clean for verb in RESPONSIBILITY_VERBS):
            responsibilities.append(sentence.strip())

    # Keep top meaningful ones (avoid overload)
    responsibilities = sorted(list(set(responsibilities)))

    return responsibilities[:25]


# ----------------------------
# EDUCATION EXTRACTION
# ----------------------------

def extract_education_requirement(jd_text):
    text = preprocess_text(jd_text)

    detected_levels = []

    for level, keywords in EDUCATION_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            detected_levels.append(level)

    priority = ["high_school", "diploma", "bachelor", "master", "phd"]

    for level in reversed(priority):
        if level in detected_levels:
            return level

    return "unknown"


# ----------------------------
# EXPERIENCE EXTRACTION
# ----------------------------

def extract_experience_requirement(jd_text):
    text = preprocess_text(jd_text)

    patterns = [
        r"(\d+)\+?\s+years",
        r"minimum\s+(\d+)\s+years",
        r"at least\s+(\d+)\s+years",
        r"(\d+)\s+to\s+\d+\s+years",
        r"(\d+)-\d+\s+years"
    ]

    values = []

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                values.append(int(match))
            except:
                continue

    if not values:
        return 0

    return min(values)


# ----------------------------
# SENIORITY DETECTION
# ----------------------------

def extract_seniority_from_jd(jd_text):
    text = preprocess_text(jd_text)

    scores = {
        "entry_level": 0,
        "mid_level": 0,
        "senior_level": 0
    }

    for level, keywords in SENIORITY_KEYWORDS.items():
        scores[level] = sum(1 for kw in keywords if kw in text)

    best = max(scores, key=scores.get)

    return best if scores[best] > 0 else "unknown"


# ----------------------------
# PREFERRED SKILLS
# ----------------------------

def extract_preferred_skills(jd_text, required_skills):
    """
    Improved preferred skill detection:
    - detects marker sentences
    - extracts skills from them
    """
    text = preprocess_text(jd_text)
    sentences = split_sentences(text)

    markers = [
        "preferred", "nice to have", "plus", "good to have",
        "added advantage", "bonus"
    ]

    preferred_sentences = [
        s for s in sentences if any(m in s for m in markers)
    ]

    preferred_text = " ".join(preferred_sentences)

    extracted = extract_required_skills_from_jd(preferred_text)

    return sorted(list(set([s for s in extracted if s not in required_skills])))


# ----------------------------
# JD QUALITY CHECK (NEW)
# ----------------------------

def get_jd_quality_score(jd_data):
    """
    Rough estimate of how detailed the JD is.
    Helps debugging.
    """
    score = 0

    if jd_data["required_skills"]:
        score += 25
    if jd_data["responsibilities"]:
        score += 25
    if jd_data["experience_required"] > 0:
        score += 15
    if jd_data["education_requirement"] != "unknown":
        score += 10
    if jd_data["preferred_skills"]:
        score += 10
    if jd_data["seniority_level"] != "unknown":
        score += 15

    return min(score, 100)


# ----------------------------
# MAIN PARSER
# ----------------------------

def parse_job_description(jd_text):
    """
    Main JD parser (Version 2.0)
    """

    if not jd_text or not jd_text.strip():
        return {
            "full_text": "",
            "clean_text": "",
            "domain": "general",
            "domain_confidence": 0.0,
            "required_skills": [],
            "preferred_skills": [],
            "responsibilities": [],
            "education_requirement": "unknown",
            "experience_required": 0,
            "seniority_level": "unknown",
            "jd_quality": 0
        }

    clean_text = preprocess_text(jd_text)

    domain_info = get_domain_confidence(clean_text)
    domain = domain_info["domain"]

    required_skills = extract_required_skills_from_jd(clean_text)
    preferred_skills = extract_preferred_skills(clean_text, required_skills)
    responsibilities = extract_responsibilities(clean_text)

    parsed = {
        "full_text": jd_text,
        "clean_text": clean_text,
        "domain": domain,
        "domain_confidence": domain_info["confidence"],
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "responsibilities": responsibilities,
        "education_requirement": extract_education_requirement(clean_text),
        "experience_required": extract_experience_requirement(clean_text),
        "seniority_level": extract_seniority_from_jd(clean_text)
    }

    parsed["jd_quality"] = get_jd_quality_score(parsed)

    return parsed