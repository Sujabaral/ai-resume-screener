# utils/domain_classifier.py

"""
Job domain classification utilities

Purpose:
- detect likely job domain / role from the job description
- help scorer apply domain-aware matching
- support broader non-tech jobs for Version 2.0
"""

import re
from utils.role_profiles import ROLE_PROFILES
from utils.text_preprocessor import preprocess_text


def _safe_text(text):
    """
    Normalize text safely.
    """
    if not text:
        return ""
    return preprocess_text(text)


def _count_keyword_hits(text, keywords):
    """
    Count keyword hits in text.
    Uses phrase-aware matching.
    """
    if not text or not keywords:
        return 0

    score = 0
    for keyword in keywords:
        keyword = keyword.strip().lower()
        if not keyword:
            continue

        # phrase / substring match
        if keyword in text:
            score += 1

    return score


def _count_weighted_keyword_hits(text, keywords):
    """
    Weighted keyword counting:
    - longer phrases contribute slightly more
    - exact phrase presence still keeps logic simple
    """
    if not text or not keywords:
        return 0.0

    score = 0.0
    for keyword in keywords:
        keyword = keyword.strip().lower()
        if not keyword:
            continue

        if keyword in text:
            word_count = len(keyword.split())
            if word_count >= 3:
                score += 2.0
            elif word_count == 2:
                score += 1.5
            else:
                score += 1.0

    return score


def get_domain_scores(jd_text):
    """
    Return weighted match scores for all domains based on ROLE_PROFILES.

    Returns:
        dict: {domain: score}
    """
    text = _safe_text(jd_text)

    if not text:
        return {"general": 0.0}

    domain_scores = {}

    for domain, profile in ROLE_PROFILES.items():
        score = 0.0

        role_keywords = profile.get("keywords", [])
        required_skills = profile.get("required_skills", [])
        preferred_skills = profile.get("preferred_skills", [])
        soft_skills = profile.get("soft_skills", [])
        education_keywords = profile.get("education_keywords", [])

        # Strongest signal: explicit role/title words in JD
        score += _count_weighted_keyword_hits(text, role_keywords) * 3.0

        # Required skills are strong signals
        score += _count_weighted_keyword_hits(text, required_skills) * 2.0

        # Preferred skills help but slightly less
        score += _count_weighted_keyword_hits(text, preferred_skills) * 1.2

        # Soft skills are weaker because many roles share them
        score += _count_weighted_keyword_hits(text, soft_skills) * 0.6

        # Education hints are useful but weaker
        score += _count_weighted_keyword_hits(text, education_keywords) * 0.8

        domain_scores[domain] = round(score, 2)

    return domain_scores


def detect_job_domain(jd_text):
    """
    Detect the most likely job domain from a job description.

    Returns:
        str: detected domain name
    """
    domain_scores = get_domain_scores(jd_text)

    if not domain_scores:
        return "general"

    best_domain = max(domain_scores, key=domain_scores.get)
    best_score = domain_scores[best_domain]

    if best_score <= 0:
        return "general"

    return best_domain


def get_primary_domain_keywords(domain):
    """
    Return the primary role keywords for a detected domain.
    """
    profile = ROLE_PROFILES.get(domain, {})
    return profile.get("keywords", [])


def get_domain_confidence(jd_text):
    """
    Return a simple confidence estimate for the detected domain.

    Returns:
        dict: {
            "domain": str,
            "confidence": float,
            "scores": dict
        }
    """
    scores = get_domain_scores(jd_text)

    if not scores:
        return {
            "domain": "general",
            "confidence": 0.0,
            "scores": {"general": 0.0}
        }

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_domain, best_score = sorted_scores[0]

    if best_score <= 0:
        return {
            "domain": "general",
            "confidence": 0.0,
            "scores": scores
        }

    second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0.0

    # Confidence based on separation from second-best domain
    confidence = best_score / (best_score + second_score + 1e-6)
    confidence = round(confidence, 3)

    return {
        "domain": best_domain,
        "confidence": confidence,
        "scores": scores
    }


def is_general_domain(domain):
    """
    Check whether the detected domain is general.
    """
    return domain == "general"


def get_top_n_domains(jd_text, n=3):
    """
    Return top N likely domains for debugging / UI display.
    """
    scores = get_domain_scores(jd_text)
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_scores[:n]