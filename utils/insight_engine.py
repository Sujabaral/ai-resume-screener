def generate_resume_insights(resume_data: dict, jd_data: dict, score_data: dict) -> list:
    """
    Generate intelligent, explainable insights based on:
    - resume structure
    - skill gaps
    - scoring breakdown
    - domain awareness
    """

    insights = []

    sections = resume_data.get("sections", {})
    skills = resume_data.get("skills", {})
    resume_text = resume_data.get("full_text", "").lower()

    jd_required = jd_data.get("required_skills", [])
    jd_preferred = jd_data.get("preferred_skills", [])
    domain = jd_data.get("domain", "general")

    # -----------------------
    # STRUCTURE INSIGHTS
    # -----------------------
    if not sections.get("projects"):
        insights.append("No dedicated projects section detected — adding projects can significantly improve ranking.")

    if not sections.get("experience"):
        insights.append("No experience section detected — even internships or academic work should be included.")

    if not sections.get("skills"):
        insights.append("No clear skills section found — recruiters rely heavily on this.")

    # -----------------------
    # SKILL ANALYSIS
    # -----------------------
    resume_flat_skills = set()
    if isinstance(skills, dict):
        for v in skills.values():
            resume_flat_skills.update(v)

    if len(resume_flat_skills) < 5:
        insights.append("Very few skills detected — consider adding more relevant skills.")

    missing_required = sorted(set(jd_required) - resume_flat_skills)
    if missing_required:
        insights.append(
            f"Missing key required skills: {', '.join(missing_required[:6])}"
        )

    missing_preferred = sorted(set(jd_preferred) - resume_flat_skills)
    if missing_preferred:
        insights.append(
            f"Adding preferred skills could improve ranking: {', '.join(missing_preferred[:6])}"
        )

    # -----------------------
    # SCORE-BASED INSIGHTS
    # -----------------------
    semantic = score_data.get("semantic_score", 0)
    skill_score = score_data.get("skill_score", 0)
    responsibility = score_data.get("responsibility_score", 0)
    experience = score_data.get("experience_score", 0)
    education = score_data.get("education_score", 0)
    soft_skill = score_data.get("soft_skill_score", 0)

    if semantic < 50:
        insights.append("Resume content is not strongly aligned with the job description — consider tailoring it more.")

    if skill_score < 50:
        insights.append("Skill match is low — focus on aligning skills with the job requirements.")

    if responsibility < 40:
        insights.append("Experience descriptions do not reflect job responsibilities clearly — use stronger action verbs and achievements.")

    if experience < 50:
        insights.append("Experience level may not meet job expectations — highlight relevant work or projects.")

    if education < 50:
        insights.append("Education may not fully meet requirements — ensure it is clearly presented.")

    if soft_skill < 40:
        insights.append("Soft skills are not clearly demonstrated — include communication, teamwork, leadership examples.")

    # -----------------------
    # DOMAIN-SPECIFIC INSIGHTS
    # -----------------------
    if domain in ["software_engineer", "backend_developer", "ml_engineer"]:
        if "github" not in resume_text:
            insights.append("Adding GitHub or project links would strengthen technical credibility.")

        if "project" not in resume_text:
            insights.append("Technical roles benefit strongly from showcasing projects.")

    if domain in ["marketing", "sales"]:
        if "campaign" not in resume_text and "client" not in resume_text:
            insights.append("Marketing/Sales roles benefit from mentioning campaigns, clients, or results.")

    if domain in ["hr", "customer_support"]:
        if "communication" not in resume_text:
            insights.append("Communication skills should be clearly demonstrated for this role.")

    # -----------------------
    # FINAL FALLBACK
    # -----------------------
    if not insights:
        insights.append("Resume is well-aligned with the job and shows strong overall fit.")

    return insights