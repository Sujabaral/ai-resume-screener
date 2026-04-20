# utils/resume_parser.py

import re

from utils.constants import EDUCATION_KEYWORDS, SECTION_HEADERS, SENIORITY_KEYWORDS
from utils.text_preprocessor import clean_section_text, extract_lines, preprocess_text


# ----------------------------
# NAME EXTRACTION
# ----------------------------

def extract_candidate_name(raw_text):
    lines = extract_lines(raw_text)

    for line in lines[:5]:
        line = line.strip()

        if not line:
            continue
        if "@" in line:
            continue
        if any(char.isdigit() for char in line):
            continue
        if len(line.split()) > 5:
            continue

        return line.title()

    return "Unknown Candidate"


# ----------------------------
# SECTION DETECTION
# ----------------------------

def detect_sections(raw_text):
    lines = extract_lines(raw_text)

    sections = {
        "summary": "",
        "skills": "",
        "experience": "",
        "education": "",
        "projects": "",
        "certifications": "",
        "other": ""
    }

    current = "other"

    for line in lines:
        line_clean = line.strip()
        line_lower = line_clean.lower()

        found = False

        for section_name, variants in SECTION_HEADERS.items():
            if line_lower in variants:
                current = section_name
                found = True
                break

        if not found:
            sections[current] += line_clean + "\n"

    for k in sections:
        sections[k] = clean_section_text(sections[k])

    return sections


# ----------------------------
# SKILL EXTRACTION (IMPROVED)
# ----------------------------

def extract_skills_from_text(text):
    text = text.lower()

    base_skills = [
        "python", "java", "c++", "sql", "excel",
        "machine learning", "data analysis",
        "communication", "teamwork", "leadership",
        "problem solving", "creativity",
        "content creation", "copywriting",
        "social media", "seo", "branding",
        "digital marketing", "research",
        "canva", "photoshop", "figma"
    ]

    found = []

    for skill in base_skills:
        if skill in text:
            found.append(skill)

    return list(set(found))


# ----------------------------
# SOFT SKILLS (NEW)
# ----------------------------

def extract_soft_skills(text):
    soft_keywords = [
        "communication", "teamwork", "collaboration",
        "leadership", "adaptability", "creativity",
        "time management", "problem solving"
    ]

    text = text.lower()

    return [s for s in soft_keywords if s in text]


# ----------------------------
# EXPERIENCE EXTRACTION
# ----------------------------

def extract_experience_items(sections):
    experience_text = sections.get("experience", "")
    projects_text = sections.get("projects", "")

    combined = experience_text + "\n" + projects_text

    lines = combined.split("\n")

    items = []

    for line in lines:
        line = line.strip()

        if len(line.split()) > 4:
            items.append(line)

    return items[:25]


# ----------------------------
# EDUCATION LEVEL
# ----------------------------

def extract_education_level(text):
    text = preprocess_text(text)

    for level, keywords in EDUCATION_KEYWORDS.items():
        if any(k in text for k in keywords):
            return level

    return "unknown"


# ----------------------------
# SENIORITY
# ----------------------------

def extract_seniority_level(text):
    text = preprocess_text(text)

    for level, keywords in SENIORITY_KEYWORDS.items():
        if any(k in text for k in keywords):
            return level

    return "entry_level"


# ----------------------------
# EXPERIENCE YEARS
# ----------------------------

def estimate_years_of_experience(text):
    text = preprocess_text(text)

    matches = re.findall(r"(\d+)\+?\s+years", text)

    if matches:
        return max(int(m) for m in matches)

    return 0


# ----------------------------
# MAIN PARSER
# ----------------------------

def parse_resume(raw_text):

    if not raw_text.strip():
        return {}

    clean_text = preprocess_text(raw_text)
    sections = detect_sections(raw_text)

    # Combine important text
    skill_text = " ".join([
        sections.get("skills", ""),
        sections.get("summary", ""),
        sections.get("experience", ""),
        sections.get("projects", "")
    ])

    experience_items = extract_experience_items(sections)

    skills = extract_skills_from_text(skill_text)
    soft_skills = extract_soft_skills(skill_text)

    return {
        "name": extract_candidate_name(raw_text),

        "raw_text": raw_text,
        "clean_text": clean_text,

        "sections": sections,

        "skills": skills,
        "soft_skills": soft_skills,

        "experience": experience_items,
        "projects": sections.get("projects", "").split("\n"),

        "education": sections.get("education", ""),

        "education_level": extract_education_level(raw_text),
        "seniority_level": extract_seniority_level(raw_text),
        "estimated_years_experience": estimate_years_of_experience(raw_text),
    }