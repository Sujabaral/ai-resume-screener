# utils/summarizer.py

"""
Result summarization utilities

Purpose:
- generate AI-like explanations
- explain strengths and weaknesses
- provide recommendation labels
"""


def safe_score(scores, key, default=0):
    value = scores.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_recommendation_label(final_score):
    """
    Convert numeric score into recommendation label.
    """
    try:
        final_score = float(final_score)
    except (TypeError, ValueError):
        final_score = 0

    if final_score >= 80:
        return "Excellent Fit"
    if final_score >= 65:
        return "Strong Fit"
    if final_score >= 50:
        return "Moderate Fit"
    if final_score >= 35:
        return "Weak Fit"
    return "Low Fit"


def generate_strengths(scores, resume_data, jd_data):
    """
    Generate a list of strengths based on scoring components and matches.
    """
    strengths = []

    matched_skills = scores.get("matched_skills", [])
    matched_soft_skills = scores.get("matched_soft_skills", [])

    semantic_score = safe_score(scores, "semantic_score")
    skills_score = safe_score(scores, "skills_score")
    responsibilities_score = safe_score(scores, "responsibilities_score")
    experience_score = safe_score(scores, "experience_score")
    education_score = safe_score(scores, "education_score")
    soft_skills_score = safe_score(scores, "soft_skills_score")

    if semantic_score >= 70:
        strengths.append("Strong overall semantic alignment with the job description.")

    if skills_score >= 65:
        strengths.append("Good coverage of required job-related skills.")
    elif len(matched_skills) >= 3:
        strengths.append("Shows several relevant skills required for the role.")

    if responsibilities_score >= 65:
        strengths.append("Past responsibilities align well with the role requirements.")

    if experience_score >= 70:
        strengths.append("Experience level is well aligned with the job expectation.")
    elif experience_score >= 50:
        strengths.append("Experience shows partial relevance to the target role.")

    if education_score >= 75:
        strengths.append("Education background matches the job requirement well.")
    elif education_score >= 45:
        strengths.append("Education background is partially relevant to the target role.")

    if soft_skills_score >= 65:
        strengths.append("Soft skills are well aligned with the job expectations.")
    elif len(matched_soft_skills) >= 2:
        strengths.append("Resume reflects some relevant communication or teamwork strengths.")

    domain = jd_data.get("job_domain", "general")
    if domain != "general":
        strengths.append(f"Profile shows relevant alignment for the {domain.replace('_', ' ')} domain.")

    if not strengths:
        strengths.append("Resume shows some relevant alignment with the job requirements.")

    return strengths[:6]


def generate_weaknesses(scores, resume_data, jd_data):
    """
    Generate a list of weaknesses / missing areas.
    """
    weaknesses = []

    missing_skills = scores.get("missing_skills", [])
    missing_soft_skills = scores.get("missing_soft_skills", [])

    semantic_score = safe_score(scores, "semantic_score")
    skills_score = safe_score(scores, "skills_score")
    responsibilities_score = safe_score(scores, "responsibilities_score")
    experience_score = safe_score(scores, "experience_score")
    education_score = safe_score(scores, "education_score")
    soft_skills_score = safe_score(scores, "soft_skills_score")

    if semantic_score < 50:
        weaknesses.append("Overall resume content is not strongly aligned with the job description.")

    if skills_score < 45:
        weaknesses.append("Several important required skills are missing or not clearly shown.")
    elif len(missing_skills) >= 2:
        weaknesses.append("Some required skills are not clearly demonstrated in the resume.")

    if responsibilities_score < 45:
        weaknesses.append("Relevant responsibilities or achievements are not clearly reflected.")

    if experience_score < 50:
        weaknesses.append("Experience does not strongly match the role’s practical requirements.")

    if education_score < 40:
        weaknesses.append("Education background is not strongly aligned with the stated role.")
    elif education_score < 55:
        weaknesses.append("Education background only partially matches the target role.")

    if soft_skills_score < 45 and len(missing_soft_skills) >= 2:
        weaknesses.append("Some expected communication, teamwork, or adaptability traits are not clearly demonstrated.")

    if not weaknesses:
        weaknesses.append("No major weakness was strongly detected, though some details could be clearer.")

    return weaknesses[:6]


def generate_insights(scores, resume_data, jd_data):
    """
    Generate short UI-friendly insights.
    """
    insights = []

    final_score = safe_score(scores, "final_score")
    semantic_score = safe_score(scores, "semantic_score")
    skills_score = safe_score(scores, "skills_score")
    responsibilities_score = safe_score(scores, "responsibilities_score")
    experience_score = safe_score(scores, "experience_score")
    education_score = safe_score(scores, "education_score")

    missing_skills = scores.get("missing_skills", [])
    matched_skills = scores.get("matched_skills", [])

    if final_score >= 65:
        insights.append("Candidate appears to be a strong overall fit for the role.")
    elif final_score >= 50:
        insights.append("Candidate shows moderate fit with some promising alignment.")
    elif final_score >= 35:
        insights.append("Candidate has limited fit and may need stronger role-specific evidence.")
    else:
        insights.append("Candidate currently appears to have a low match for this role.")

    if skills_score >= 60:
        insights.append("Skill alignment is one of the stronger parts of this application.")
    elif missing_skills:
        insights.append(f"Important missing skills include: {', '.join(missing_skills[:4])}.")

    if responsibilities_score < 45:
        insights.append("Resume should show more role-relevant responsibilities, outcomes, or achievements.")

    if education_score < 40:
        insights.append("Education background may not be closely aligned with the target job domain.")

    if semantic_score >= 70:
        insights.append("Overall language and profile framing align well with the job description.")

    if experience_score < 50:
        insights.append("Experience alignment is limited for this specific role.")

    if matched_skills and len(insights) < 6:
        insights.append(f"Matched skills include: {', '.join(matched_skills[:4])}.")

    return insights[:6]


def generate_short_explanation(scores, resume_data, jd_data):
    """
    Generate a short paragraph explaining fit.
    """
    final_score = safe_score(scores, "final_score")
    semantic_score = safe_score(scores, "semantic_score")
    skills_score = safe_score(scores, "skills_score")
    responsibilities_score = safe_score(scores, "responsibilities_score")
    experience_score = safe_score(scores, "experience_score")
    education_score = safe_score(scores, "education_score")
    soft_skills_score = safe_score(scores, "soft_skills_score")

    matched_skills = scores.get("matched_skills", [])
    missing_skills = scores.get("missing_skills", [])
    domain = jd_data.get("job_domain", "general")
    recommendation = get_recommendation_label(final_score)

    if matched_skills:
        matched_preview = ", ".join(matched_skills[:5])
        matched_part = f"The resume demonstrates relevant alignment through skills such as {matched_preview}. "
    else:
        matched_part = "The resume shows limited clearly matched role-specific skills. "

    if missing_skills:
        missing_preview = ", ".join(missing_skills[:4])
        missing_part = f"However, some important areas are not clearly shown, including {missing_preview}. "
    else:
        missing_part = "Most core required skills appear to be covered. "

    if domain != "general":
        domain_part = f"The role appears to belong to the {domain.replace('_', ' ')} domain, and the system evaluated the candidate accordingly. "
    else:
        domain_part = ""

    score_part = (
        f"The final score reflects semantic fit ({semantic_score:.1f}%), "
        f"skills alignment ({skills_score:.1f}%), "
        f"responsibility alignment ({responsibilities_score:.1f}%), "
        f"experience relevance ({experience_score:.1f}%), "
        f"education fit ({education_score:.1f}%), "
        f"and soft skills alignment ({soft_skills_score:.1f}%)."
    )

    return (
        f"This candidate is classified as a {recommendation}. "
        f"{domain_part}"
        f"{matched_part}"
        f"{missing_part}"
        f"{score_part}"
    ).strip()


def generate_result_summary(scores, resume_data, jd_data):
    """
    Full summary payload for UI/templates.
    """
    final_score = safe_score(scores, "final_score")

    return {
        "recommendation": get_recommendation_label(final_score),
        "strengths": generate_strengths(scores, resume_data, jd_data),
        "weaknesses": generate_weaknesses(scores, resume_data, jd_data),
        "insights": generate_insights(scores, resume_data, jd_data),
        "explanation": generate_short_explanation(scores, resume_data, jd_data),
    }