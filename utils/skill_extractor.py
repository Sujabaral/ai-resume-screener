# utils/skill_extractor.py

"""
Universal skill extraction utilities

Purpose:
- extract categorized skills from resume or job description text
- support all job domains, not only tech
- normalize skill variants and synonyms
- identify matched and missing skills more accurately
"""

from utils.constants import SKILL_CATEGORIES
from utils.text_preprocessor import preprocess_text


SKILL_SYNONYMS = {
    "js": "javascript",
    "javascript es6": "javascript",
    "nodejs": "node.js",
    "node js": "node.js",
    "py": "python",
    "python3": "python",
    "postgres": "postgresql",
    "postgre": "postgresql",
    "restful api": "rest api",
    "restful apis": "rest api",
    "apis": "api",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "dl": "deep learning",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "powerbi": "power bi",
    "ms excel": "excel",
    "microsoft excel": "excel",
    "figma design": "figma",
    "ux/ui": "ui/ux",
    "ui ux": "ui/ux",
    "seo writing": "seo",
    "social media marketing": "social media",
    "digital campaigns": "campaign management",
    "client relations": "client relationship",
    "customer support": "customer service",
    "customer servicing": "customer service",
    "issue handling": "issue resolution",
    "recruiting": "recruitment",
    "talent sourcing": "talent acquisition",
    "teaching assistant": "teaching",
    "academic mentoring": "mentoring",
    "financial statements": "financial reporting",
    "account reconciliation": "reconciliation",
}


def normalize_skill(skill):
    """
    Normalize a skill into a standard comparable form.
    """
    if not skill:
        return ""

    skill = preprocess_text(skill).strip().lower()
    skill = SKILL_SYNONYMS.get(skill, skill)
    return skill


def normalize_skill_list(skills):
    """
    Normalize a list of skills.
    """
    normalized = []
    for skill in skills:
        norm = normalize_skill(skill)
        if norm:
            normalized.append(norm)
    return sorted(list(set(normalized)))


def build_skill_lookup():
    """
    Build normalized skill lookup from SKILL_CATEGORIES.
    Returns:
        dict: normalized_skill -> (canonical_skill, category)
    """
    lookup = {}

    for category, skills in SKILL_CATEGORIES.items():
        for skill in skills:
            canonical = skill.strip().lower()
            normalized = normalize_skill(skill)
            lookup[normalized] = (canonical, category)

    for alias, canonical in SKILL_SYNONYMS.items():
        normalized_alias = normalize_skill(alias)
        normalized_canonical = normalize_skill(canonical)

        for category, skills in SKILL_CATEGORIES.items():
            if normalized_canonical in [normalize_skill(s) for s in skills]:
                lookup[normalized_alias] = (normalized_canonical, category)
                break

    return lookup


SKILL_LOOKUP = build_skill_lookup()


def _contains_phrase(text, phrase):
    """
    Safe phrase match helper.
    """
    if not text or not phrase:
        return False
    return phrase in text


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

    extracted = {category: [] for category in SKILL_CATEGORIES.keys()}

    if not clean_text:
        return extracted

    # Direct canonical skill matching
    for category, skills in SKILL_CATEGORIES.items():
        for skill in skills:
            normalized_skill = normalize_skill(skill)
            if _contains_phrase(clean_text, normalized_skill):
                extracted[category].append(normalized_skill)

    # Synonym/alias matching
    for alias, canonical in SKILL_SYNONYMS.items():
        normalized_alias = normalize_skill(alias)
        normalized_canonical = normalize_skill(canonical)

        if _contains_phrase(clean_text, normalized_alias):
            canonical_info = SKILL_LOOKUP.get(normalized_canonical)
            if canonical_info:
                canonical_skill, category = canonical_info
                extracted[category].append(canonical_skill)

    # Deduplicate and sort
    for category in extracted:
        extracted[category] = sorted(list(set(extracted[category])))

    return extracted


def flatten_skills(skill_dict):
    """
    Convert categorized skills into one flat set.
    """
    flat = set()

    if not isinstance(skill_dict, dict):
        return flat

    for _, skills in skill_dict.items():
        if not isinstance(skills, list):
            continue
        for skill in skills:
            norm = normalize_skill(skill)
            if norm:
                flat.add(norm)

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
        "software_engineer": "technical",
        "backend_developer": "technical",
        "frontend_developer": "technical",
        "full_stack_developer": "technical",
        "data_analyst": "technical",
        "ml_engineer": "technical",
        "qa_engineer": "technical",
        "marketing": "marketing",
        "sales": "sales",
        "finance": "finance",
        "accountant": "finance",
        "hr": "hr",
        "teacher": "education",
        "education": "education",
        "healthcare": "healthcare",
        "operations": "operations",
        "project_manager": "business",
        "business_analyst": "business",
        "customer_support": "customer_support",
        "content_writer": "marketing",
        "graphic_designer": "technical",
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
    normalized_jd_skills = normalize_skill_list(jd_skills)

    matched = [skill for skill in normalized_jd_skills if skill in resume_flat]
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
    normalized_jd_skills = normalize_skill_list(jd_skills)

    missing = [skill for skill in normalized_jd_skills if skill not in resume_flat]
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
    normalized_jd_skills = normalize_skill_list(jd_skills)

    if not normalized_jd_skills:
        return 0.0

    matched = get_matched_skills(resume_skills, normalized_jd_skills)
    score = (len(matched) / len(set(normalized_jd_skills))) * 100
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
        "total_required_skills": len(set(normalize_skill_list(jd_skills))),
        "total_matched_skills": len(matched),
        "total_missing_skills": len(missing)
    }