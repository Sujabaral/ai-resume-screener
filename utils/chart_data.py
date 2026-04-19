def build_chart_data(result: dict) -> dict:
    return {
        "score_breakdown": {
            "labels": [
                "Overall Similarity",
                "Weighted Skill Score",
                "Experience Score",
                "Project Score"
            ],
            "values": [
                result.get("overall_similarity", 0),
                result.get("skill_coverage", 0),
                result.get("experience_score", 0),
                result.get("project_score", 0)
            ]
        },
        "skill_match": {
            "matched": len(result.get("matched_skills", [])),
            "missing": len(result.get("missing_skills", []))
        }
    }