import re
from utils.text_preprocessor import preprocess_text
from utils.skill_extractor import extract_skills
from utils.role_profiles import ROLE_PROFILES


def infer_role_from_jd(jd_text: str) -> str:
    jd_lower = jd_text.lower()

    role_keywords = {
        "backend": ["backend", "api", "server", "flask", "fastapi"],
        "frontend": ["frontend", "ui", "react", "javascript", "css"],
        "data_analyst": ["data analyst", "analytics", "sql", "dashboard", "reporting"],
        "ml_engineer": ["machine learning", "ml", "nlp", "model", "pytorch", "tensorflow"]
    }

    scores = {}
    for role, keywords in role_keywords.items():
        scores[role] = sum(1 for keyword in keywords if keyword in jd_lower)

    best_role = max(scores, key=scores.get)
    return best_role if scores[best_role] > 0 else "backend"


def extract_required_preferred_skills(jd_text: str, all_skills: list) -> dict:
    jd_lower = jd_text.lower()

    required_section = ""
    preferred_section = ""

    required_match = re.search(
        r"(required|requirements|must have|mandatory)(.*?)(preferred|nice to have|bonus|good to have|$)",
        jd_lower,
        re.DOTALL
    )
    if required_match:
        required_section = required_match.group(2)

    preferred_match = re.search(
        r"(preferred|nice to have|bonus|good to have)(.*)",
        jd_lower,
        re.DOTALL
    )
    if preferred_match:
        preferred_section = preferred_match.group(2)

    required_skills = []
    preferred_skills = []

    for skill in all_skills:
        if skill in required_section:
            required_skills.append(skill)
        elif skill in preferred_section:
            preferred_skills.append(skill)

    return {
        "required_skills": sorted(set(required_skills)),
        "preferred_skills": sorted(set(preferred_skills))
    }


def parse_job_description(jd_text: str) -> dict:
    cleaned_text = preprocess_text(jd_text)
    all_skills = extract_skills(cleaned_text)
    inferred_role = infer_role_from_jd(jd_text)

    skill_sections = extract_required_preferred_skills(cleaned_text, all_skills)

    if not skill_sections["required_skills"] and inferred_role in ROLE_PROFILES:
        skill_sections["required_skills"] = ROLE_PROFILES[inferred_role]["required_skills"]

    if not skill_sections["preferred_skills"] and inferred_role in ROLE_PROFILES:
        skill_sections["preferred_skills"] = ROLE_PROFILES[inferred_role]["preferred_skills"]

    return {
        "raw_text": jd_text,
        "cleaned_text": cleaned_text,
        "skills": all_skills,
        "required_skills": skill_sections["required_skills"],
        "preferred_skills": skill_sections["preferred_skills"],
        "inferred_role": inferred_role
    }