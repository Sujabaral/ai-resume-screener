import re

SECTION_PATTERNS = {
    "summary": r"(summary|profile|professional summary|objective|about me)",
    "skills": r"(skills|technical skills|core skills|competencies|technologies)",
    "experience": r"(experience|work experience|employment|professional experience|internship)",
    "education": r"(education|academic background|qualifications)",
    "projects": r"(projects|personal projects|academic projects)",
    "certifications": r"(certifications|training|courses|licenses)"
}


def split_into_sections(text: str) -> dict:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    sections = {}
    current_section = "other"
    sections[current_section] = []

    for line in lines:
        lower_line = line.lower()
        matched_section = None

        for section, pattern in SECTION_PATTERNS.items():
            if re.fullmatch(pattern, lower_line):
                matched_section = section
                break

        if matched_section:
            current_section = matched_section
            sections.setdefault(current_section, [])
        else:
            sections.setdefault(current_section, []).append(line)

    return {
        key: "\n".join(value).strip()
        for key, value in sections.items()
        if value
    }


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