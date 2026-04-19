# utils/summarizer.py

"""
Result summarization utilities

Purpose:
- generate AI-like explanations
- explain strengths and weaknesses
- provide recommendation labels
"""


def get_recommendation_label(final_score):
    """
    Convert numeric score into recommendation label.
    """
    if final_score >= 80:
        return "Excellent Fit"
    if final_score >= 65:
        return "Strong Fit"
    if final_score >= 50:
        return "Moderate Fit"
    return "Weak Fit"


def generate_strengths(scores, resume_data, jd_data):
    """
    Generate a list of strengths based on scoring components and matches.
    """
    strengths = []

    matched_skills = scores.get("matched_skills", [])
    semantic_score = scores.get("semantic_score", 0)
    responsibility_score = scores.get("responsibility_score", 0)
    experience_score = scores.get("experience_score", 0)
    education_score = scores.get("education_score", 0)

    if semantic_score >= 70:
        strengths.append("Strong overall semantic alignment with the job description.")

    if len(matched_skills) >= 5:
        strengths.append("Good coverage of required job-related skills.")
    elif len(matched_skills) >= 2:
        strengths.append("Shows several relevant skills required for the role.")

    if responsibility_score >= 65:
        strengths.append("Past responsibilities align well with the role requirements.")

    if experience_score >= 70:
        strengths.append("Experience level is well aligned with the job expectation.")

    if education_score >= 70:
        strengths.append("Education background matches the job requirement.")

    domain = jd_data.get("domain", "general")
    if domain != "general":
        strengths.append(f"Profile shows relevant alignment for the {domain.replace('_', ' ')} domain.")

    if not strengths:
        strengths.append("Resume shows some relevant alignment with the job requirements.")

    return strengths


def generate_weaknesses(scores, resume_data, jd_data):
    """
    Generate a list of weaknesses / missing areas.
    """
    weaknesses = []

    missing_skills = scores.get("missing_skills", [])
    semantic_score = scores.get("semantic_score", 0)
    responsibility_score = scores.get("responsibility_score", 0)
    experience_score = scores.get("experience_score", 0)
    education_score = scores.get("education_score", 0)

    if semantic_score < 50:
        weaknesses.append("Overall resume content is not strongly aligned with the job description.")

    if len(missing_skills) >= 5:
        weaknesses.append("Several important required skills are missing or not clearly shown.")
    elif len(missing_skills) >= 2:
        weaknesses.append("Some required skills are not clearly demonstrated in the resume.")

    if responsibility_score < 45:
        weaknesses.append("Relevant responsibilities or achievements are not clearly reflected.")

    if experience_score < 50:
        weaknesses.append("Experience level may be below the job requirement.")

    if education_score < 50:
        weaknesses.append("Education background may not fully match the stated requirement.")

    if not weaknesses:
        weaknesses.append("No major weakness was strongly detected, though some details could be clearer.")

    return weaknesses


def generate_short_explanation(scores, resume_data, jd_data):
    """
    Generate a short paragraph explaining fit.
    """
    final_score = scores.get("final_score", 0)
    matched_skills = scores.get("matched_skills", [])
    missing_skills = scores.get("missing_skills", [])
    domain = jd_data.get("domain", "general")
    recommendation = get_recommendation_label(final_score)

    matched_part = ""
    if matched_skills:
        matched_preview = ", ".join(matched_skills[:5])
        matched_part = f"The resume demonstrates relevant alignment through skills such as {matched_preview}. "
    else:
        matched_part = "The resume shows limited clearly matched role-specific skills. "

    missing_part = ""
    if missing_skills:
        missing_preview = ", ".join(missing_skills[:4])
        missing_part = f"However, some important areas are not clearly shown, including {missing_preview}. "
    else:
        missing_part = "Most core required skills appear to be covered. "

    domain_part = ""
    if domain != "general":
        domain_part = f"The role appears to belong to the {domain.replace('_', ' ')} domain, and the system evaluated the candidate accordingly. "

    return (
        f"This candidate is classified as a {recommendation}. "
        f"{domain_part}"
        f"{matched_part}"
        f"{missing_part}"
        f"The final score is based on semantic fit, skills, responsibilities, experience, and education alignment."
    ).strip()


def generate_result_summary(scores, resume_data, jd_data):
    """
    Full summary payload for UI/templates.
    """
    final_score = scores.get("final_score", 0)

    return {
        "recommendation": get_recommendation_label(final_score),
        "strengths": generate_strengths(scores, resume_data, jd_data),
        "weaknesses": generate_weaknesses(scores, resume_data, jd_data),
        "explanation": generate_short_explanation(scores, resume_data, jd_data)
    }