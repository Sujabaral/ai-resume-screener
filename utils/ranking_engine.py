def rank_resumes(results: list) -> list:
    return sorted(results, key=lambda x: x.get("match_score", 0), reverse=True)

def assign_ranks(results):
    """
    Improved ATS-like ranking:
    - Prioritizes real relevance (similarity + experience)
    - Prevents fake high skill-only resumes from ranking top
    """

    for r in results:
        # Weighted scoring (tune these weights)
        weighted_score = (
            r["match_score"] * 0.4 +
            r["overall_similarity"] * 0.25 +
            r["skill_coverage"] * 0.2 +
            r["experience_score"] * 0.1 +
            r["project_score"] * 0.05
        )

        # 🚨 Penalty: if similarity is too low → reduce rank
        if r["overall_similarity"] < 15:
            weighted_score *= 0.6

        # 🚨 Penalty: no experience
        if r["experience_score"] == 0:
            weighted_score *= 0.85

        r["final_rank_score"] = round(weighted_score, 2)

    # Sort by smarter score
    sorted_results = sorted(results, key=lambda x: x["final_rank_score"], reverse=True)

    # Assign rank
    for i, r in enumerate(sorted_results, 1):
        r["rank"] = i

    return sorted_results