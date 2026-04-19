# utils/scorer.py

"""
Main scoring engine for AI Resume Screener v2.0

Combines:
- semantic similarity
- role-aware skill matching
- soft skill matching
- responsibility matching
- experience fit
- education fit
- keyword alignment
- final weighted scoring
"""

from sentence_transformers import SentenceTransformer, util

from utils.constants import DEFAULT_SCORING_WEIGHTS, DOMAIN_WEIGHT_OVERRIDES
from utils.role_profiles import ROLE_PROFILES
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
    valid_responsibilities = 0

    for responsibility in jd_responsibilities:
        responsibility = responsibility.strip().lower()
        if not responsibility:
            continue

        valid_responsibilities += 1

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

    if valid_responsibilities == 0:
        return 0.0

    score = (matched / valid_responsibilities) * 100
    return round(score, 2)


def get_sentence_semantic_responsibility_score(resume_experience_text, jd_responsibilities):
    """
    Semantic responsibility score using sentence-level comparison.
    """
    if not resume_experience_text or not jd_responsibilities:
        return 0.0

    resume_sentences = split_sentences(resume_experience_text)
    resume_sentences = [s for s in resume_sentences if len(s.split()) >= 4]

    valid_responsibilities = [r for r in jd_responsibilities if r and r.strip()]
    if not resume_sentences or not valid_responsibilities:
        return 0.0

    matched = 0

    try:
        resume_embeddings = semantic_model.encode(resume_sentences[:50], convert_to_tensor=True)

        for jd_resp in valid_responsibilities:
            jd_embedding = semantic_model.encode(jd_resp, convert_to_tensor=True)
            similarities = util.cos_sim(jd_embedding, resume_embeddings)[0]
            best_similarity = float(similarities.max().item())

            if best_similarity >= 0.45:
                matched += 1

    except Exception:
        return 0.0

    score = (matched / len(valid_responsibilities)) * 100
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


def get_education_score(resume_data, jd_data, domain="general"):
    """
    Compare resume education level with job requirement.
    Also lightly boosts if role profile education keywords appear in resume.
    """
    resume_education = resume_data.get("education_level", "unknown")
    jd_education = jd_data.get("education_requirement", "unknown")
    resume_full_text = resume_data.get("full_text", "").lower()

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
        base_score = 70.0
    elif resume_rank >= jd_rank:
        base_score = 100.0
    elif resume_rank == jd_rank - 1:
        base_score = 60.0
    elif resume_rank == 0:
        base_score = 30.0
    else:
        base_score = 20.0

    profile = ROLE_PROFILES.get(domain, {})
    education_keywords = profile.get("education_keywords", [])

    keyword_bonus = 0
    for keyword in education_keywords:
        if keyword.lower() in resume_full_text:
            keyword_bonus += 5

    final_score = min(100.0, base_score + min(keyword_bonus, 15))
    return round(final_score, 2)


def get_keyword_alignment_score(resume_text, jd_text):
    """
    Lightweight keyword overlap score.
    Keeps some explainable lexical alignment in addition to semantic matching.
    """
    if not resume_text or not jd_text:
        return 0.0

    resume_keywords = set(extract_keywords(resume_text))
    jd_keywords = set(extract_keywords(jd_text))

    resume_keywords = {word for word in resume_keywords if len(word) > 3}
    jd_keywords = {word for word in jd_keywords if len(word) > 3}

    if not jd_keywords:
        return 0.0

    overlap = resume_keywords.intersection(jd_keywords)
    score = (len(overlap) / len(jd_keywords)) * 100
    return round(score, 2)


def get_soft_skill_score(resume_text, soft_skills):
    """
    Measure how many role soft skills appear in resume text.
    """
    if not resume_text or not soft_skills:
        return 0.0

    resume_text = resume_text.lower()
    matched = sum(1 for skill in soft_skills if skill.lower() in resume_text)

    score = (matched / len(soft_skills)) * 100 if soft_skills else 0.0
    return round(score, 2)


def merge_role_and_jd_skills(jd_required_skills, jd_preferred_skills, domain):
    """
    Merge JD skills with role profile skills for stronger domain-aware scoring.
    """
    profile = ROLE_PROFILES.get(domain, ROLE_PROFILES.get("general", {}))

    role_required = profile.get("required_skills", [])
    role_preferred = profile.get("preferred_skills", [])

    combined_required = list(dict.fromkeys(
        [skill.lower() for skill in (jd_required_skills + role_required) if skill]
    ))
    combined_preferred = list(dict.fromkeys(
        [skill.lower() for skill in (jd_preferred_skills + role_preferred) if skill]
    ))

    return combined_required, combined_preferred, role_required, role_preferred


def generate_score_summary(
    semantic_score,
    skill_score,
    responsibility_score,
    experience_score,
    education_score,
    soft_skill_score
):
    """
    Generate short explanation summary for UI.
    """
    strengths = []
    weaknesses = []

    if semantic_score >= 75:
        strengths.append("strong overall semantic alignment with the job description")
    elif semantic_score < 45:
        weaknesses.append("low overall semantic alignment with the job description")

    if skill_score >= 70:
        strengths.append("good skill match for the role")
    elif skill_score < 40:
        weaknesses.append("limited skill match for the role")

    if responsibility_score >= 65:
        strengths.append("resume experience reflects key job responsibilities")
    elif responsibility_score < 35:
        weaknesses.append("experience does not strongly reflect the required responsibilities")

    if experience_score >= 70:
        strengths.append("experience level is a good fit")
    elif experience_score < 40:
        weaknesses.append("experience level appears weaker than the job expectation")

    if education_score >= 80:
        strengths.append("education background aligns well")
    elif education_score < 40:
        weaknesses.append("education fit appears limited")

    if soft_skill_score >= 70:
        strengths.append("resume reflects relevant soft skills")
    elif soft_skill_score < 35:
        weaknesses.append("soft skill evidence is limited in the resume")

    return {
        "strengths": strengths,
        "weaknesses": weaknesses
    }


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
    jd_preferred_skills = jd_data.get("preferred_skills", [])
    jd_responsibilities = jd_data.get("responsibilities", [])
    jd_domain = jd_data.get("domain", "general")

    weights = get_scoring_weights(jd_domain)
    profile = ROLE_PROFILES.get(jd_domain, ROLE_PROFILES.get("general", {}))
    soft_skills = profile.get("soft_skills", [])

    combined_required_skills, combined_preferred_skills, role_required, role_preferred = merge_role_and_jd_skills(
        jd_required_skills,
        jd_preferred_skills,
        jd_domain
    )

    semantic_score = get_semantic_score(resume_full_text, jd_full_text)

    required_skill_score = get_skill_match_score(resume_skills, combined_required_skills)
    preferred_skill_score = get_skill_match_score(resume_skills, combined_preferred_skills)

    if combined_preferred_skills:
        skill_score = round((required_skill_score * 0.75) + (preferred_skill_score * 0.25), 2)
    else:
        skill_score = round(required_skill_score, 2)

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
    education_score = get_education_score(resume_data, jd_data, jd_domain)
    keyword_alignment_score = get_keyword_alignment_score(resume_full_text, jd_full_text)
    soft_skill_score = get_soft_skill_score(resume_full_text, soft_skills)

    final_score = (
        semantic_score * weights.get("semantic_score", 0.25) +
        skill_score * weights.get("skill_match_score", 0.30) +
        responsibility_score * weights.get("responsibility_score", 0.15) +
        experience_score * weights.get("experience_score", 0.10) +
        education_score * weights.get("education_score", 0.10) +
        keyword_alignment_score * weights.get("keyword_alignment_score", 0.05) +
        soft_skill_score * weights.get("soft_skill_score", 0.05)
    )

    matched_skills = get_matched_skills(resume_skills, combined_required_skills)
    missing_skills = get_missing_skills(resume_skills, combined_required_skills)

    summary = generate_score_summary(
        semantic_score=semantic_score,
        skill_score=skill_score,
        responsibility_score=responsibility_score,
        experience_score=experience_score,
        education_score=education_score,
        soft_skill_score=soft_skill_score
    )

    return {
        "final_score": round(float(final_score), 2),
        "semantic_score": round(float(semantic_score), 2),
        "skill_score": round(float(skill_score), 2),
        "required_skill_score": round(float(required_skill_score), 2),
        "preferred_skill_score": round(float(preferred_skill_score), 2),
        "responsibility_score": round(float(responsibility_score), 2),
        "responsibility_keyword_score": round(float(responsibility_keyword_score), 2),
        "responsibility_semantic_score": round(float(responsibility_semantic_score), 2),
        "experience_score": round(float(experience_score), 2),
        "education_score": round(float(education_score), 2),
        "keyword_alignment_score": round(float(keyword_alignment_score), 2),
        "soft_skill_score": round(float(soft_skill_score), 2),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "domain": jd_domain,
        "role_detected": jd_domain,
        "role_required_skills": role_required,
        "role_preferred_skills": role_preferred,
        "combined_required_skills": combined_required_skills,
        "combined_preferred_skills": combined_preferred_skills,
        "weights_used": weights,
        "strengths": summary["strengths"],
        "weaknesses": summary["weaknesses"],
    }