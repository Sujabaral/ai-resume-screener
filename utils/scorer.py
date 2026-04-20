import math
from typing import Dict, List, Tuple

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    SentenceTransformer = None
    util = None


# Load model once
MODEL = None


def get_embedding_model():
    global MODEL
    if MODEL is None and SentenceTransformer is not None:
        MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return MODEL


def normalize_text(text: str) -> str:
    return (text or "").strip().lower()


def safe_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value]
    return []


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def average(values: List[float]) -> float:
    values = [v for v in values if v is not None]
    if not values:
        return 0.0
    return sum(values) / len(values)


def unique_clean(items: List[str]) -> List[str]:
    seen = set()
    cleaned = []
    for item in items:
        item = normalize_text(item)
        if item and item not in seen:
            seen.add(item)
            cleaned.append(item)
    return cleaned


def cosine_similarity_text(text1: str, text2: str) -> float:
    """
    Returns similarity score in percentage (0-100).
    Falls back to keyword overlap if sentence-transformers is unavailable.
    """
    text1 = normalize_text(text1)
    text2 = normalize_text(text2)

    if not text1 or not text2:
        return 0.0

    model = get_embedding_model()

    if model is not None and util is not None:
        emb = model.encode([text1, text2], convert_to_tensor=True)
        score = util.cos_sim(emb[0], emb[1]).item()
        return clamp(score * 100)

    # fallback: simple token overlap
    tokens1 = set(text1.split())
    tokens2 = set(text2.split())

    if not tokens1 or not tokens2:
        return 0.0

    overlap = len(tokens1 & tokens2)
    denom = max(len(tokens1 | tokens2), 1)
    return clamp((overlap / denom) * 100)


def best_semantic_match(source_items: List[str], target_items: List[str]) -> float:
    if not source_items or not target_items:
        return 0.0

    scores = []
    for target in target_items:
        target = normalize_text(target)
        if not target:
            continue

        best = 0.0
        for source in source_items:
            source = normalize_text(source)
            if not source:
                continue
            sim = cosine_similarity_text(source, target)
            best = max(best, sim)
        scores.append(best)

    return average(scores)


def extract_resume_experience_text(resume_data: Dict) -> List[str]:
    sections = resume_data.get("sections", {})
    experience_section = sections.get("experience", "")
    projects_section = sections.get("projects", "")

    items = []
    if isinstance(experience_section, str) and experience_section.strip():
        items.append(experience_section)
    if isinstance(projects_section, str) and projects_section.strip():
        items.append(projects_section)

    experience_items = resume_data.get("experience", [])
    project_items = resume_data.get("projects", [])

    items.extend(safe_list(experience_items))
    items.extend(safe_list(project_items))

    return unique_clean(items)


def extract_resume_education_text(resume_data: Dict) -> str:
    sections = resume_data.get("sections", {})
    education_text = sections.get("education", "")

    if isinstance(education_text, str) and education_text.strip():
        return normalize_text(education_text)

    education_items = safe_list(resume_data.get("education", []))
    return normalize_text(" ".join(education_items))


def compute_skill_match_score(resume_skills: List[str], jd_skills: List[str]) -> Tuple[float, List[str], List[str]]:
    resume_skills = unique_clean(resume_skills)
    jd_skills = unique_clean(jd_skills)

    if not jd_skills:
        return 0.0, [], []

    exact_matches = []
    matched = set()

    for jd_skill in jd_skills:
        for resume_skill in resume_skills:
            if jd_skill == resume_skill:
                exact_matches.append(jd_skill)
                matched.add(jd_skill)
                break

    semantic_extra = []
    for jd_skill in jd_skills:
        if jd_skill in matched:
            continue
        best_score = 0.0
        for resume_skill in resume_skills:
            sim = cosine_similarity_text(resume_skill, jd_skill)
            best_score = max(best_score, sim)
        if best_score >= 70:
            semantic_extra.append(jd_skill)
            matched.add(jd_skill)

    matched_skills = unique_clean(exact_matches + semantic_extra)
    missing_skills = [skill for skill in jd_skills if skill not in matched]

    score = (len(matched_skills) / len(jd_skills)) * 100
    return clamp(score), matched_skills, missing_skills


def compute_responsibility_score(resume_data: Dict, jd_data: Dict) -> float:
    resume_items = extract_resume_experience_text(resume_data)
    jd_responsibilities = unique_clean(
        safe_list(jd_data.get("responsibilities", [])) +
        safe_list(jd_data.get("key_responsibilities", []))
    )

    if not jd_responsibilities:
        return 0.0

    return best_semantic_match(resume_items, jd_responsibilities)


def compute_semantic_score(resume_data: Dict, jd_data: Dict) -> float:
    resume_text = normalize_text(resume_data.get("raw_text", ""))
    jd_text = normalize_text(jd_data.get("raw_text", ""))

    if not resume_text or not jd_text:
        return 0.0

    return cosine_similarity_text(resume_text, jd_text)


def get_domain_degree_map() -> Dict[str, Dict[str, int]]:
    return {
        "software": {
            "computer engineering": 100,
            "computer science": 100,
            "information technology": 95,
            "electronics and communication": 75,
            "electrical engineering": 65,
            "business": 35,
            "marketing": 20,
            "journalism": 15,
        },
        "data": {
            "computer engineering": 95,
            "computer science": 95,
            "information technology": 90,
            "statistics": 95,
            "mathematics": 85,
            "business": 45,
            "marketing": 30,
        },
        "marketing": {
            "marketing": 100,
            "communications": 95,
            "journalism": 90,
            "mass communication": 90,
            "business": 75,
            "management": 70,
            "computer engineering": 30,
            "computer science": 25,
            "information technology": 25,
        },
        "content": {
            "communications": 100,
            "journalism": 95,
            "marketing": 90,
            "english": 85,
            "mass communication": 95,
            "business": 70,
            "computer engineering": 30,
            "computer science": 25,
        },
        "design": {
            "design": 100,
            "multimedia": 90,
            "fine arts": 85,
            "computer engineering": 45,
            "computer science": 40,
        },
        "general": {
            "computer engineering": 65,
            "computer science": 65,
            "business": 65,
            "marketing": 65,
            "communications": 65,
            "journalism": 65,
        }
    }


def classify_degree_match(education_text: str, job_domain: str) -> float:
    education_text = normalize_text(education_text)
    job_domain = normalize_text(job_domain)

    if not education_text:
        return 0.0

    domain_map = get_domain_degree_map()
    mapping = domain_map.get(job_domain, domain_map["general"])

    best_score = 20
    for degree_keyword, degree_score in mapping.items():
        if degree_keyword in education_text:
            best_score = max(best_score, degree_score)

    if "related field" in education_text:
        best_score = max(best_score, 60)

    return float(best_score)


def compute_education_score(resume_data: Dict, jd_data: Dict) -> float:
    education_text = extract_resume_education_text(resume_data)
    job_domain = normalize_text(jd_data.get("job_domain", "general"))
    return classify_degree_match(education_text, job_domain)


def infer_years_from_text(text: str) -> float:
    text = normalize_text(text)
    if not text:
        return 0.0

    score = 0.0
    if "intern" in text:
        score += 10
    if "junior" in text:
        score += 20
    if "associate" in text:
        score += 30
    if "mid" in text:
        score += 50
    if "senior" in text:
        score += 75
    if "lead" in text or "manager" in text:
        score += 90

    return clamp(score)


def compute_experience_score(resume_data: Dict, jd_data: Dict) -> float:
    resume_items = extract_resume_experience_text(resume_data)
    jd_responsibilities = unique_clean(
        safe_list(jd_data.get("responsibilities", [])) +
        safe_list(jd_data.get("key_responsibilities", []))
    )

    exp_semantic = best_semantic_match(resume_items, jd_responsibilities)

    jd_text = normalize_text(jd_data.get("raw_text", ""))
    seniority_hint = infer_years_from_text(jd_text)

    if seniority_hint == 0:
        seniority_score = 70  # neutral default for internships / unclear jobs
    else:
        resume_text = " ".join(resume_items)
        if "intern" in resume_text or "undergraduate" in resume_text or "student" in resume_text:
            candidate_level = 20
        elif "junior" in resume_text:
            candidate_level = 35
        elif "senior" in resume_text or "lead" in resume_text:
            candidate_level = 80
        else:
            candidate_level = 40

        seniority_gap = abs(candidate_level - seniority_hint)
        seniority_score = clamp(100 - seniority_gap)

    final_exp_score = (exp_semantic * 0.7) + (seniority_score * 0.3)
    return clamp(final_exp_score)


def compute_soft_skills_score(resume_data: Dict, jd_data: Dict) -> Tuple[float, List[str], List[str]]:
    resume_soft = unique_clean(safe_list(resume_data.get("soft_skills", [])))
    jd_soft = unique_clean(safe_list(jd_data.get("soft_skills", [])))

    if not jd_soft:
        return 0.0, [], []

    matched = []
    missing = []

    for jd_skill in jd_soft:
        found = False
        for resume_skill in resume_soft:
            if jd_skill == resume_skill or cosine_similarity_text(resume_skill, jd_skill) >= 70:
                matched.append(jd_skill)
                found = True
                break
        if not found:
            missing.append(jd_skill)

    score = (len(matched) / len(jd_soft)) * 100 if jd_soft else 0.0
    return clamp(score), matched, missing


def generate_score_label(score: float) -> str:
    if score >= 80:
        return "Excellent Match"
    if score >= 65:
        return "Strong Match"
    if score >= 50:
        return "Moderate Match"
    if score >= 35:
        return "Weak Fit"
    return "Low Match"


def calculate_match_score(resume_data: Dict, jd_data: Dict) -> Dict:
    resume_skills = unique_clean(safe_list(resume_data.get("skills", [])))
    jd_skills = unique_clean(
        safe_list(jd_data.get("required_skills", [])) +
        safe_list(jd_data.get("preferred_skills", []))
    )

    semantic_score = compute_semantic_score(resume_data, jd_data)
    skills_score, matched_skills, missing_skills = compute_skill_match_score(resume_skills, jd_skills)
    responsibilities_score = compute_responsibility_score(resume_data, jd_data)
    experience_score = compute_experience_score(resume_data, jd_data)
    education_score = compute_education_score(resume_data, jd_data)
    soft_skills_score, matched_soft_skills, missing_soft_skills = compute_soft_skills_score(resume_data, jd_data)

    # Better balanced weights
    final_score = (
        semantic_score * 0.25 +
        skills_score * 0.25 +
        responsibilities_score * 0.20 +
        experience_score * 0.15 +
        education_score * 0.10 +
        soft_skills_score * 0.05
    )

    final_score = clamp(final_score)

    strengths = []
    weaknesses = []

    if semantic_score >= 65:
        strengths.append("Resume content is semantically well aligned with the job description.")
    else:
        weaknesses.append("Overall resume content is not strongly aligned with the job description.")

    if skills_score >= 60:
        strengths.append("Good coverage of required job-related skills.")
    else:
        weaknesses.append("Several important required skills are missing or not clearly shown.")

    if responsibilities_score >= 60:
        strengths.append("Resume reflects responsibilities similar to the target role.")
    else:
        weaknesses.append("Relevant responsibilities or achievements are not clearly reflected.")

    if experience_score >= 60:
        strengths.append("Experience level is reasonably aligned with the job expectation.")
    else:
        weaknesses.append("Experience does not strongly match the role’s practical requirements.")

    if education_score >= 70:
        strengths.append("Education background matches the job domain well.")
    elif education_score >= 40:
        strengths.append("Education background is partially relevant to the target role.")
    else:
        weaknesses.append("Education background is not strongly aligned with the job domain.")

    if soft_skills_score >= 60:
        strengths.append("Soft skills alignment is strong for this role.")
    else:
        weaknesses.append("Some expected communication or collaboration traits are not clearly demonstrated.")

    return {
        "final_score": round(final_score, 2),
        "score_label": generate_score_label(final_score),

        "semantic_score": round(semantic_score, 2),
        "skills_score": round(skills_score, 2),
        "responsibilities_score": round(responsibilities_score, 2),
        "experience_score": round(experience_score, 2),
        "education_score": round(education_score, 2),
        "soft_skills_score": round(soft_skills_score, 2),

        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "matched_soft_skills": matched_soft_skills,
        "missing_soft_skills": missing_soft_skills,

        "strengths": strengths,
        "weaknesses": weaknesses,
    }