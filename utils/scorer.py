from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.role_profiles import ROLE_PROFILES


def cosine_score(text1: str, text2: str) -> float:
    if not text1 or not text2:
        return 0.0

    if not text1.strip() or not text2.strip():
        return 0.0

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    vectors = vectorizer.fit_transform([text1, text2])
    score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    return round(score * 100, 2)


def overlap_score(source_skills: list, target_skills: list) -> float:
    if not target_skills:
        return 0.0

    source_set = set(source_skills)
    target_set = set(target_skills)
    matched = source_set.intersection(target_set)
    return round((len(matched) / len(target_set)) * 100, 2)


def calculate_final_score(resume_data: dict, jd_data: dict, selected_role: str = None) -> dict:
    role = selected_role or jd_data.get("inferred_role", "backend")
    profile = ROLE_PROFILES.get(role, ROLE_PROFILES["backend"])
    weights = profile["weights"]

    overall_similarity = cosine_score(
        resume_data.get("cleaned_text", ""),
        jd_data.get("cleaned_text", "")
    )

    all_skill_score = overlap_score(
        resume_data.get("skills", []),
        jd_data.get("skills", [])
    )

    required_skill_score = overlap_score(
        resume_data.get("skills", []),
        jd_data.get("required_skills", [])
    )

    preferred_skill_score = overlap_score(
        resume_data.get("skills", []),
        jd_data.get("preferred_skills", [])
    )

    weighted_skill_score = round(
        (0.7 * required_skill_score) + (0.3 * preferred_skill_score),
        2
    ) if jd_data.get("required_skills") or jd_data.get("preferred_skills") else all_skill_score

    experience_score = cosine_score(
        resume_data.get("sections", {}).get("experience", ""),
        jd_data.get("cleaned_text", "")
    )

    project_score = cosine_score(
        resume_data.get("sections", {}).get("projects", ""),
        jd_data.get("cleaned_text", "")
    )

    final_score = round(
        (weights["overall"] * overall_similarity) +
        (weights["skills"] * weighted_skill_score) +
        (weights["experience"] * experience_score) +
        (weights["projects"] * project_score),
        2
    )

    return {
        "role_used": role,
        "overall_similarity": overall_similarity,
        "all_skill_score": all_skill_score,
        "required_skill_score": required_skill_score,
        "preferred_skill_score": preferred_skill_score,
        "weighted_skill_score": weighted_skill_score,
        "experience_score": experience_score,
        "project_score": project_score,
        "final_score": final_score
    }