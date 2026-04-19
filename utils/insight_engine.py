def generate_resume_insights(resume_data: dict, jd_data: dict) -> list:
    insights = []

    sections = resume_data.get("sections", {})
    skills = resume_data.get("skills", [])

    if not sections.get("projects"):
        insights.append("No dedicated projects section detected.")

    if not sections.get("experience"):
        insights.append("No dedicated experience section detected.")

    if not sections.get("skills"):
        insights.append("No dedicated skills section detected.")

    if len(skills) < 5:
        insights.append("Very few skills were detected in the resume.")

    missing_required = sorted(set(jd_data.get("required_skills", [])) - set(skills))
    if missing_required:
        insights.append(
            "Important required skills missing from resume: " + ", ".join(missing_required)
        )

    missing_preferred = sorted(set(jd_data.get("preferred_skills", [])) - set(skills))
    if missing_preferred:
        insights.append(
            "Preferred skills not detected: " + ", ".join(missing_preferred)
        )

    if not insights:
        insights.append("The resume appears structurally strong with reasonable alignment.")

    return insights