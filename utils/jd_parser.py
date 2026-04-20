# utils/jd_parser.py

import re

from utils.constants import EDUCATION_KEYWORDS, RESPONSIBILITY_VERBS, SENIORITY_KEYWORDS
from utils.domain_classifier import get_domain_confidence
from utils.text_preprocessor import preprocess_text, split_sentences


# ----------------------------
# SMART SKILL EXTRACTION (NEW CORE FIX)
# ----------------------------

def extract_skills_from_sentences(sentences):
    """
    Extract skills dynamically from sentences instead of fixed keyword lists.
    Works for marketing, HR, content, etc.
    """
    skills = set()

    patterns = [
        r"experience in ([a-zA-Z\s,]+)",
        r"knowledge of ([a-zA-Z\s,]+)",
        r"proficiency in ([a-zA-Z\s,]+)",
        r"skills in ([a-zA-Z\s,]+)",
        r"responsible for ([a-zA-Z\s,]+)",
        r"including ([a-zA-Z\s,]+)",
    ]

    for sentence in sentences:
        s = sentence.lower()

        for pattern in patterns:
            matches = re.findall(pattern, s)
            for match in matches:
                parts = re.split(r",|and", match)
                for p in parts:
                    skill = p.strip()
                    if 2 < len(skill) < 40:
                        skills.add(skill)

        # direct keyword fallback
        keywords = [
            "content creation", "copywriting", "editing",
            "social media", "seo", "branding",
            "digital marketing", "communication",
            "research", "teamwork", "creativity",
            "photoshop", "canva"
        ]

        for kw in keywords:
            if kw in s:
                skills.add(kw)

    return list(skills)


# ----------------------------
# RESPONSIBILITY EXTRACTION (IMPROVED)
# ----------------------------

def extract_responsibilities(jd_text):
    sentences = split_sentences(jd_text)
    responsibilities = []

    for sentence in sentences:
        s = sentence.lower().strip()

        if len(s.split()) < 5:
            continue

        if any(verb in s for verb in RESPONSIBILITY_VERBS):
            responsibilities.append(sentence.strip())

    return sorted(list(set(responsibilities)))[:20]


# ----------------------------
# EDUCATION
# ----------------------------

def extract_education_requirement(jd_text):
    text = preprocess_text(jd_text)

    for level, keywords in EDUCATION_KEYWORDS.items():
        if any(k in text for k in keywords):
            return level

    return "unknown"


# ----------------------------
# EXPERIENCE
# ----------------------------

def extract_experience_requirement(jd_text):
    text = preprocess_text(jd_text)

    matches = re.findall(r"(\d+)\+?\s+years", text)
    return int(matches[0]) if matches else 0


# ----------------------------
# SENIORITY
# ----------------------------

def extract_seniority_from_jd(jd_text):
    text = preprocess_text(jd_text)

    for level, keywords in SENIORITY_KEYWORDS.items():
        if any(k in text for k in keywords):
            return level

    return "entry_level"  # default for internships


# ----------------------------
# SOFT SKILLS (NEW)
# ----------------------------

def extract_soft_skills(jd_text):
    soft_keywords = [
        "communication", "teamwork", "collaboration",
        "creativity", "adaptability", "problem solving",
        "time management"
    ]

    text = preprocess_text(jd_text)

    return [s for s in soft_keywords if s in text]


# ----------------------------
# PREFERRED SKILLS
# ----------------------------

def extract_preferred_skills(jd_text):
    markers = ["preferred", "plus", "nice to have"]

    sentences = split_sentences(jd_text)

    preferred = []

    for s in sentences:
        if any(m in s.lower() for m in markers):
            preferred.extend(extract_skills_from_sentences([s]))

    return list(set(preferred))


# ----------------------------
# MAIN PARSER
# ----------------------------

def parse_job_description(jd_text):

    if not jd_text.strip():
        return {}

    clean_text = preprocess_text(jd_text)
    sentences = split_sentences(jd_text)

    domain_info = get_domain_confidence(clean_text)

    required_skills = extract_skills_from_sentences(sentences)
    preferred_skills = extract_preferred_skills(jd_text)
    responsibilities = extract_responsibilities(jd_text)
    soft_skills = extract_soft_skills(jd_text)

    return {
        "raw_text": jd_text,
        "clean_text": clean_text,

        "job_domain": domain_info["domain"],
        "domain_confidence": domain_info["confidence"],

        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "soft_skills": soft_skills,

        "responsibilities": responsibilities,

        "education_requirement": extract_education_requirement(jd_text),
        "experience_required": extract_experience_requirement(jd_text),
        "seniority_level": extract_seniority_from_jd(jd_text),
    }