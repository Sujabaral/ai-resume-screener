# utils/scorer.py

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def cosine_score(text1: str, text2: str) -> float:
    if not text1.strip() or not text2.strip():
        return 0.0

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    vectors = vectorizer.fit_transform([text1, text2])
    score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    return round(score * 100, 2)


def skill_match_score(resume_skills: list, jd_skills: list) -> float:
    if not jd_skills:
        return 0.0

    resume_set = set(resume_skills)
    jd_set = set(jd_skills)

    matched = resume_set.intersection(jd_set)
    return round((len(matched) / len(jd_set)) * 100, 2)


def calculate_final_score(resume_data: dict, jd_data: dict) -> dict:
    overall_similarity = cosine_score(
        resume_data.get("cleaned_text", ""),
        jd_data.get("cleaned_text", "")
    )

    skill_score = skill_match_score(
        resume_data.get("skills", []),
        jd_data.get("skills", [])
    )

    experience_score = cosine_score(
        resume_data.get("sections", {}).get("experience", ""),
        jd_data.get("cleaned_text", "")
    )

    project_score = cosine_score(
        resume_data.get("sections", {}).get("projects", ""),
        jd_data.get("cleaned_text", "")
    )

    final_score = round(
        (0.50 * overall_similarity) +
        (0.30 * skill_score) +
        (0.10 * experience_score) +
        (0.10 * project_score),
        2
    )

    return {
        "overall_similarity": overall_similarity,
        "skill_score": skill_score,
        "experience_score": experience_score,
        "project_score": project_score,
        "final_score": final_score
    }