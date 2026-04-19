# utils/resume_parser.py

"""
Resume parsing utilities

Purpose:
- structure raw resume text into useful sections
- extract skills from the resume
- detect education clues
- detect experience/seniority clues
- prepare data for scoring
"""

import re

from utils.constants import EDUCATION_KEYWORDS, SECTION_HEADERS, SENIORITY_KEYWORDS
from utils.skill_extractor import extract_skills
from utils.text_preprocessor import clean_section_text, extract_lines, preprocess_text


def extract_candidate_name(raw_text):
    """
    Best-effort candidate name extraction.
    Uses the first meaningful line from the raw resume text.
    """
    lines = extract_lines(raw_text)

    if not lines:
        return "Unknown Candidate"

    for line in lines[:5]:
        stripped = line.strip()

        # skip lines that are probably headings or contact lines
        if not stripped:
            continue

        lower_line = stripped.lower()

        if "@" in stripped:
            continue
        if any(char.isdigit() for char in stripped):
            continue
        if len(stripped.split()) > 5:
            continue
        if lower_line in {
            "resume", "curriculum vitae", "cv", "profile", "summary", "objective"
        }:
            continue

        return stripped.title()

    return "Unknown Candidate"


def detect_sections(raw_text):
    """
    Detect resume sections using common section headers.
    Returns a dict of section_name -> section_text.
    """
    lines = extract_lines(raw_text)
    sections = {
        "summary": "",
        "skills": "",
        "experience": "",
        "education": "",
        "certifications": "",
        "projects": "",
        "other": ""
    }

    current_section = "other"

    for line in lines:
        line_clean = line.strip()
        line_lower = line_clean.lower()

        detected_section = None

        for section_name, header_variants in SECTION_HEADERS.items():
            if line_lower in header_variants:
                detected_section = section_name
                break

        if detected_section:
            current_section = detected_section
            continue

        sections[current_section] += line_clean + "\n"

    for key in sections:
        sections[key] = clean_section_text(sections[key])

    return sections


def extract_education_level(text):
    """
    Detect highest education level mentioned in the resume.
    """
    text = preprocess_text(text)

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


def extract_seniority_level(text):
    """
    Detect likely seniority level from resume text.
    """
    text = preprocess_text(text)

    seniority_scores = {
        "entry_level": 0,
        "mid_level": 0,
        "senior_level": 0
    }

    for level, keywords in SENIORITY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                seniority_scores[level] += 1

    best_level = max(seniority_scores, key=seniority_scores.get)

    if seniority_scores[best_level] == 0:
        return "unknown"

    return best_level


def estimate_years_of_experience(raw_text):
    """
    Very rough heuristic to estimate years of experience.
    Looks for patterns like:
    - 2 years
    - 3+ years
    - 1 year
    """
    text = preprocess_text(raw_text)

    patterns = [
        r"(\d+)\+?\s+years",
        r"(\d+)\+?\s+year",
        r"(\d+)\+?\s+yrs",
        r"(\d+)\+?\s+yr"
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

    return max(found_values)


def parse_resume(raw_text):
    """
    Main resume parser.

    Returns structured resume data for scoring.
    """
    if not raw_text or not raw_text.strip():
        return {
            "name": "Unknown Candidate",
            "full_text": "",
            "clean_text": "",
            "sections": {},
            "skills": {},
            "experience_text": "",
            "education_text": "",
            "projects_text": "",
            "summary_text": "",
            "certifications_text": "",
            "education_level": "unknown",
            "seniority_level": "unknown",
            "estimated_years_experience": 0
        }

    clean_text = preprocess_text(raw_text)
    sections = detect_sections(raw_text)

    # combine important areas for better extraction
    skills_source_text = "\n".join([
        sections.get("skills", ""),
        sections.get("summary", ""),
        sections.get("experience", ""),
        sections.get("projects", "")
    ]).strip()

    experience_text = "\n".join([
        sections.get("experience", ""),
        sections.get("projects", "")
    ]).strip()

    education_text = "\n".join([
        sections.get("education", ""),
        sections.get("certifications", "")
    ]).strip()

    parsed = {
        "name": extract_candidate_name(raw_text),
        "full_text": raw_text,
        "clean_text": clean_text,
        "sections": sections,
        "skills": extract_skills(skills_source_text if skills_source_text else raw_text),
        "experience_text": preprocess_text(experience_text if experience_text else raw_text),
        "education_text": preprocess_text(education_text),
        "projects_text": preprocess_text(sections.get("projects", "")),
        "summary_text": preprocess_text(sections.get("summary", "")),
        "certifications_text": preprocess_text(sections.get("certifications", "")),
        "education_level": extract_education_level(education_text if education_text else raw_text),
        "seniority_level": extract_seniority_level(raw_text),
        "estimated_years_experience": estimate_years_of_experience(raw_text)
    }

    return parsed