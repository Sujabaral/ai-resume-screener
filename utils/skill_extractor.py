# utils/skill_extractor.py

"""
Universal skill extraction utilities

Purpose:
- extract categorized skills from resume or job description text
- support all job domains, not only tech
- identify matched and missing skills
"""

from utils.constants import SKILL_CATEGORIES
from utils.text_preprocessor import preprocess_text


def extract_skills(text):
    """
    Extract categorized skills from text.

    Returns:
        dict: {
            "technical": [...],
            "business": [...],
            ...
        }
    """
    clean_text = preprocess_text(text)

    extracted = {}

    for category, skills in SKILL_CATEGORIES.items():
        found_skills = []

        for skill in skills:
            if skill in clean_text:
                found_skills.append(skill)

        extracted[category] = sorted(list(set(found_skills)))

    return extracted


def flatten_skills(skill_dict):
    """
    Convert categorized skills into one flat set.
    """
    flat = set()

    if not isinstance(skill_dict, dict):
        return flat

    for _, skills in skill_dict.items():
        for skill in skills:
            flat.add(skill)

    return flat


def extract_domain_skills(text, domain=None):
    """
    Extract all skills, and optionally return only the most relevant domain skills.

    If domain is given, it prioritizes that category plus soft skills.
    """
    all_skills = extract_skills(text)

    if not domain:
        return all_skills

    domain_map = {
        "technology": "technical",
        "marketing": "marketing",
        "sales": "sales",
        "finance": "finance",
        "hr": "hr",
        "education": "education",
        "healthcare": "healthcare",
        "operations": "operations",
        "customer_support": "customer_support",
        "general": "business"
    }

    selected_category = domain_map.get(domain, "business")

    filtered = {
        selected_category: all_skills.get(selected_category, []),
        "soft_skills": all_skills.get("soft_skills", [])
    }

    return filtered


def get_matched_skills(resume_skills, jd_skills):
    """
    Get matched skills between resume and JD.

    Args:
        resume_skills (dict): categorized resume skills
        jd_skills (list): required JD skills

    Returns:
        list
    """
    resume_flat = flatten_skills(resume_skills)
    matched = [skill for skill in jd_skills if skill in resume_flat]
    return sorted(list(set(matched)))


def get_missing_skills(resume_skills, jd_skills):
    """
    Get missing JD skills not found in resume.

    Args:
        resume_skills (dict): categorized resume skills
        jd_skills (list): required JD skills

    Returns:
        list
    """
    resume_flat = flatten_skills(resume_skills)
    missing = [skill for skill in jd_skills if skill not in resume_flat]
    return sorted(list(set(missing)))


def get_skill_match_score(resume_skills, jd_skills):
    """
    Calculate percentage skill match score.

    Args:
        resume_skills (dict): categorized extracted resume skills
        jd_skills (list): required skills from JD

    Returns:
        float
    """
    if not jd_skills:
        return 0.0

    matched = get_matched_skills(resume_skills, jd_skills)
    score = (len(matched) / len(set(jd_skills))) * 100
    return round(score, 2)


def extract_required_skills_from_jd(jd_text):
    """
    Extract JD skills by scanning universal categories.
    Returns a flat sorted list.
    """
    categorized = extract_skills(jd_text)
    flat = flatten_skills(categorized)
    return sorted(list(flat))


def get_skill_summary(resume_skills, jd_skills):
    """
    Return a useful summary for UI / result page.
    """
    matched = get_matched_skills(resume_skills, jd_skills)
    missing = get_missing_skills(resume_skills, jd_skills)
    score = get_skill_match_score(resume_skills, jd_skills)

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "skill_score": score,
        "total_required_skills": len(set(jd_skills)),
        "total_matched_skills": len(matched),
        "total_missing_skills": len(missing)
    }