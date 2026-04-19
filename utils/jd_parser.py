# utils/jd_parser.py

from utils.text_preprocessor import preprocess_text
from utils.skill_extractor import extract_skills

def parse_job_description(jd_text: str) -> dict:
    cleaned = preprocess_text(jd_text)
    skills = extract_skills(cleaned)

    return {
        "raw_text": jd_text,
        "cleaned_text": cleaned,
        "skills": skills
    }