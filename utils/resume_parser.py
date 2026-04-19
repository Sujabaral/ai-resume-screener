# utils/resume_parser.py

import re

SECTION_PATTERNS = {
    "skills": r"\b(skills|technical skills|core skills|competencies|technologies)\b",
    "experience": r"\b(experience|work experience|employment|professional experience|internship)\b",
    "education": r"\b(education|academic background|qualification|academic qualifications)\b",
    "projects": r"\b(projects|personal projects|academic projects)\b",
    "certifications": r"\b(certifications|licenses|courses|training)\b",
    "summary": r"\b(summary|profile|professional summary|objective|about me)\b",
}


def split_into_sections(text: str) -> dict:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    sections = {}
    current_section = "other"
    sections[current_section] = []

    for line in lines:
        matched = False
        lower_line = line.lower()

        for section_name, pattern in SECTION_PATTERNS.items():
            if re.fullmatch(pattern, lower_line):
                current_section = section_name
                if current_section not in sections:
                    sections[current_section] = []
                matched = True
                break

        if not matched:
            sections.setdefault(current_section, []).append(line)

    return {k: "\n".join(v).strip() for k, v in sections.items() if v}

import re

def extract_contact_info(text: str) -> dict:
    email = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    phone = re.findall(r'(\+?\d[\d\s\-]{7,}\d)', text)
    linkedin = re.findall(r'(https?://(?:www\.)?linkedin\.com/[^\s]+)', text, re.I)
    github = re.findall(r'(https?://(?:www\.)?github\.com/[^\s]+)', text, re.I)

    return {
        "email": email[0] if email else None,
        "phone": phone[0] if phone else None,
        "linkedin": linkedin[0] if linkedin else None,
        "github": github[0] if github else None,
    }