# utils/domain_classifier.py

"""
Job domain classification utilities

Purpose:
- detect likely job domain from the job description
- help scorer apply domain-aware matching
"""

from utils.constants import DOMAIN_KEYWORDS
from utils.text_preprocessor import preprocess_text


def detect_job_domain(jd_text):
    """
    Detect the most likely job domain from a job description.
    Returns:
        str: domain name
    """
    text = preprocess_text(jd_text)

    if not text:
        return "general"

    domain_scores = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        if domain == "general":
            continue

        score = 0
        for keyword in keywords:
            if keyword in text:
                score += 1

        domain_scores[domain] = score

    if not domain_scores:
        return "general"

    best_domain = max(domain_scores, key=domain_scores.get)
    best_score = domain_scores[best_domain]

    if best_score == 0:
        return "general"

    return best_domain


def get_domain_scores(jd_text):
    """
    Return keyword hit counts for all domains.
    Useful for debugging and UI display.
    """
    text = preprocess_text(jd_text)

    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if domain == "general":
            continue
        scores[domain] = sum(1 for keyword in keywords if keyword in text)

    return scores


def get_primary_domain_keywords(domain):
    """
    Return keywords for a detected domain.
    """
    return DOMAIN_KEYWORDS.get(domain, [])


def is_general_domain(domain):
    """
    Check whether the detected domain is general.
    """
    return domain == "general"