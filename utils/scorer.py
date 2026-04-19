# utils/scorer.py

"""
Main scoring engine for AI Resume Screener v2.0

Combines:
- semantic similarity
- skill matching
- responsibility matching
- experience fit
- education fit
- keyword alignment
- final weighted scoring
"""

from sentence_transformers import SentenceTransformer, util

from utils.constants import DEFAULT_SCORING_WEIGHTS, DOMAIN_WEIGHT_OVERRIDES
from utils.skill_extractor import (
    get_matched_skills,
    get_missing_skills,
    get_skill_match_score,
)
from utils.text_preprocessor import extract_keywords, split_sentences

# Load once only
semantic_model = SentenceTransformer("all-MiniLM-L6-v2")


def get_scoring_weights(domain="general"):
    """
    Return domain-aware scoring weights.
    Falls back to default weights if no override exists.
    """
    return DOMAIN_WEIGHT_OVERRIDES.get(domain, DEFAULT_SCORING_WEIGHTS)


def get_semantic_score(text1, text2):
    """
    Compute semantic similarity score using sentence embeddings.
    Returns score from 0 to 100.
    """
    if not text1 or not text2:
        return 0.0

    try:
        emb1 = semantic_model.encode(text1, convert_to_tensor=True)
        emb2 = semantic_model.encode(text2, convert_to_tensor=True)
        score = util.cos_sim(emb1, emb2).item()
        score = max(0.0, min(1.0, score))
        return round(score * 100, 2)
    except Exception:
        return 0.0


def get_responsibility_score(resume_experience_text, jd_responsibilities):
    """
    Basic responsibility matching.
    Checks how many JD responsibility sentences are reflected in resume experience text.

    v2.0 approach:
    - if JD responsibility sentence fully appears -> count match
    - else compare by keyword overlap
    """
    if not resume_experience_text or not jd_responsibilities:
        return 0.0

    resume_text_lower = resume_experience_text.lower()
    matched = 0

    for responsibility in jd_responsibilities:
        responsibility = responsibility.strip().lower()
        if not responsibility:
            continue

        # Direct containment
        if responsibility in resume_text_lower:
            matched += 1
            continue

        # Keyword overlap fallback
        responsibility_keywords = set(
            word for word in extract_keywords(responsibility) if len(word) > 3
        )

        if not responsibility_keywords:
            continue

        overlap_count = sum(
            1 for keyword in responsibility_keywords if keyword in resume_text_lower
        )

        overlap_ratio = overlap_count / len(responsibility_keywords)

        if overlap_ratio >= 0.4:
            matched += 1

    score = (matched / len(jd_responsibilities)) * 100
    return round(score, 2)


def get_experience_score(resume_data, jd_data):
    """
    Compare candidate experience against JD expectation.

    Signals used:
    - estimated years of experience
    - seniority level
    """
    resume_years = resume_data.get("estimated_years_experience", 0)
    jd_years = jd_data.get("experience_required", 0)

    resume_seniority = resume_data.get("seniority_level", "unknown")
    jd_seniority = jd_data.get("seniority_level", "unknown")

    score = 50.0  # neutral base

    # Years-based adjustment
    if jd_years == 0:
        score += 10
    else:
        if resume_years >= jd_years:
            score += 30
        elif resume_years == max(jd_years - 1, 0):
            score += 15
        elif resume_years == 0:
            score -= 20
        else:
            score -= 10

    # Seniority-based adjustment
    seniority_rank = {
        "unknown": 0,
        "entry_level": 1,
        "mid_level": 2,
        "senior_level": 3
    }

    resume_rank = seniority_rank.get(resume_seniority, 0)
    jd_rank = seniority_rank.get(jd_seniority, 0)

    if jd_rank == 0:
        score += 5
    else:
        if resume_rank >= jd_rank:
            score += 15
        elif resume_rank == jd_rank - 1:
            score += 5
        else:
            score -= 15

    score = max(0.0, min(100.0, score))
    return round(score, 2)


def get_education_score(resume_data, jd_data):
    """
    Compare resume education level with job requirement.
    """
    resume_education = resume_data.get("education_level", "unknown")
    jd_education = jd_data.get("education_requirement", "unknown")

    rank = {
        "unknown": 0,
        "high_school": 1,
        "diploma": 2,
        "bachelor": 3,
        "master": 4,
        "phd": 5
    }

    resume_rank = rank.get(resume_education, 0)
    jd_rank = rank.get(jd_education, 0)

    if jd_rank == 0:
        return 70.0

    if resume_rank >= jd_rank:
        return 100.0

    if resume_rank == jd_rank - 1:
        return 60.0

    if resume_rank == 0:
        return 30.0

    return 20.0


def get_keyword_alignment_score(resume_text, jd_text):
    """
    Lightweight keyword overlap score.
    Keeps some explainable lexical alignment in addition to semantic matching.
    """
    if not resume_text or not jd_text:
        return 0.0

    resume_keywords = set(extract_keywords(resume_text))
    jd_keywords = set(extract_keywords(jd_text))

    # remove overly short/noisy words
    resume_keywords = {word for word in resume_keywords if len(word) > 3}
    jd_keywords = {word for word in jd_keywords if len(word) > 3}

    if not jd_keywords:
        return 0.0

    overlap = resume_keywords.intersection(jd_keywords)
    score = (len(overlap) / len(jd_keywords)) * 100
    return round(score, 2)


def get_sentence_semantic_responsibility_score(resume_experience_text, jd_responsibilities):
    """
    Optional semantic-style responsibility score using sentence-level comparison.

    For v2.0, this is used as a helper and blended with keyword responsibility score.
    """
    if not resume_experience_text or not jd_responsibilities:
        return 0.0

    resume_sentences = split_sentences(resume_experience_text)
    resume_sentences = [s for s in resume_sentences if len(s.split()) >= 4]

    if not resume_sentences:
        return 0.0

    matched = 0

    for jd_resp in jd_responsibilities:
        best_similarity = 0.0

        try:
            jd_emb = semantic_model.encode(jd_resp, convert_to_tensor=True)

            for resume_sentence in resume_sentences[:50]:
                resume_emb = semantic_model.encode(resume_sentence, convert_to_tensor=True)
                sim = util.cos_sim(jd_emb, resume_emb).item()
                if sim > best_similarity:
                    best_similarity = sim

            if best_similarity >= 0.45:
                matched += 1

        except Exception:
            continue

    score = (matched / len(jd_responsibilities)) * 100
    return round(score, 2)


def calculate_match_score(resume_data, jd_data):
    """
    Main multi-factor scoring function.
    Returns detailed component scores + final score.
    """
    resume_full_text = resume_data.get("full_text", "")
    resume_experience_text = resume_data.get("experience_text", "")
    resume_skills = resume_data.get("skills", {})

    jd_full_text = jd_data.get("full_text", "")
    jd_required_skills = jd_data.get("required_skills", [])
    jd_responsibilities = jd_data.get("responsibilities", [])
    jd_domain = jd_data.get("domain", "general")

    weights = get_scoring_weights(jd_domain)

    semantic_score = get_semantic_score(resume_full_text, jd_full_text)
    skill_score = get_skill_match_score(resume_skills, jd_required_skills)

    responsibility_keyword_score = get_responsibility_score(
        resume_experience_text,
        jd_responsibilities
    )

    responsibility_semantic_score = get_sentence_semantic_responsibility_score(
        resume_experience_text,
        jd_responsibilities
    )

    if jd_responsibilities:
        responsibility_score = round(
            (responsibility_keyword_score * 0.55) +
            (responsibility_semantic_score * 0.45),
            2
        )
    else:
        responsibility_score = 0.0

    experience_score = get_experience_score(resume_data, jd_data)
    education_score = get_education_score(resume_data, jd_data)
    keyword_alignment_score = get_keyword_alignment_score(resume_full_text, jd_full_text)

    final_score = (
        semantic_score * weights["semantic_score"] +
        skill_score * weights["skill_match_score"] +
        responsibility_score * weights["responsibility_score"] +
        experience_score * weights["experience_score"] +
        education_score * weights["education_score"] +
        keyword_alignment_score * weights["keyword_alignment_score"]
    )

    matched_skills = get_matched_skills(resume_skills, jd_required_skills)
    missing_skills = get_missing_skills(resume_skills, jd_required_skills)

    return {
        "final_score": round(float(final_score), 2),
        "semantic_score": round(float(semantic_score), 2),
        "skill_score": round(float(skill_score), 2),
        "responsibility_score": round(float(responsibility_score), 2),
        "responsibility_keyword_score": round(float(responsibility_keyword_score), 2),
        "responsibility_semantic_score": round(float(responsibility_semantic_score), 2),
        "experience_score": round(float(experience_score), 2),
        "education_score": round(float(education_score), 2),
        "keyword_alignment_score": round(float(keyword_alignment_score), 2),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "domain": jd_domain,
        "weights_used": weights
    }