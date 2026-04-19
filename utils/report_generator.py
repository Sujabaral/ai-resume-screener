def build_report_text(result: dict) -> str:
    lines = [
        "AI Resume Screener & Job Match Scorer — Version 2.0",
        "=" * 55,
        f"Resume File: {result.get('resume_filename', 'N/A')}",
        f"Role Used: {result.get('role_used', 'N/A')}",
        f"Rank: {result.get('rank', 'N/A')}",
        f"Final Score: {result.get('match_score', 0)}%",
        f"Overall Similarity: {result.get('overall_similarity', 0)}%",
        f"Weighted Skill Score: {result.get('skill_coverage', 0)}%",
        f"Required Skill Score: {result.get('required_skill_score', 0)}%",
        f"Preferred Skill Score: {result.get('preferred_skill_score', 0)}%",
        f"Experience Score: {result.get('experience_score', 0)}%",
        f"Project Score: {result.get('project_score', 0)}%",
        "",
        "Matched Skills:",
        ", ".join(result.get("matched_skills", [])) or "None",
        "",
        "Missing Skills:",
        ", ".join(result.get("missing_skills", [])) or "None",
        "",
        "Insights:"
    ]

    for item in result.get("insights", []):
        lines.append(f"- {item}")

    lines.append("")
    lines.append("Suggestions:")
    for item in result.get("suggestions", []):
        lines.append(f"- {item}")

    return "\n".join(lines)