from typing import Dict, List, Tuple
from utils.embedding_model import compute_similarity, compute_batch_similarity
from utils.domain_classifier import predict_job_domain


def _safe_lower_list(items: List[str]) -> List[str]:
    return [
        str(item).strip().lower()
        for item in items
        if isinstance(item, str) and str(item).strip()
    ]


def _dedupe_keep_order(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        lowered = item.lower()
        if lowered not in seen:
            seen.add(lowered)
            result.append(item)
    return result


def _normalize_text_block(text: str) -> str:
    if not text:
        return ""
    return " ".join(str(text).split()).strip()


def _extract_resume_sections(resume_data: Dict) -> Dict[str, str]:
    sections = resume_data.get("sections", {}) or {}
    return {
        "summary": _normalize_text_block(
            sections.get("summary")
            or sections.get("objective")
            or resume_data.get("summary", "")
        ),
        "experience": _normalize_text_block(
            sections.get("experience")
            or resume_data.get("experience", "")
        ),
        "projects": _normalize_text_block(
            sections.get("projects")
            or resume_data.get("projects", "")
        ),
        "education": _normalize_text_block(
            sections.get("education")
            or resume_data.get("education", "")
        ),
        "full_text": _normalize_text_block(
            resume_data.get("cleaned_text")
            or resume_data.get("text")
            or resume_data.get("raw_text", "")
        ),
    }


def _extract_jd_sections(jd_data: Dict) -> Dict[str, str]:
    responsibilities = jd_data.get("responsibilities", []) or []
    required_skills = jd_data.get("required_skills", []) or []
    preferred_skills = jd_data.get("preferred_skills", []) or []

    return {
        "title": _normalize_text_block(jd_data.get("job_title", "")),
        "summary": _normalize_text_block(jd_data.get("summary", "")),
        "requirements": _normalize_text_block(" ".join(required_skills + preferred_skills)),
        "responsibilities": _normalize_text_block(" ".join(responsibilities)),
        "full_text": _normalize_text_block(
            jd_data.get("cleaned_text")
            or jd_data.get("text", "")
        ),
    }


def _score_exact_skill_match(
    resume_skills: List[str],
    jd_required_skills: List[str],
    jd_preferred_skills: List[str]
) -> Dict:
    resume_set = set(_safe_lower_list(resume_skills))
    required = _dedupe_keep_order(_safe_lower_list(jd_required_skills))
    preferred = _dedupe_keep_order(_safe_lower_list(jd_preferred_skills))

    matched_required = [skill for skill in required if skill in resume_set]
    matched_preferred = [skill for skill in preferred if skill in resume_set]

    required_score = (len(matched_required) / len(required)) if required else 0.0
    preferred_score = (len(matched_preferred) / len(preferred)) if preferred else 0.0

    exact_skill_score = (0.7 * required_score) + (0.3 * preferred_score)

    missing_required = [skill for skill in required if skill not in resume_set]
    missing_preferred = [skill for skill in preferred if skill not in resume_set]

    return {
        "score": round(exact_skill_score, 4),
        "matched_required": matched_required,
        "matched_preferred": matched_preferred,
        "missing_required": missing_required,
        "missing_preferred": missing_preferred,
    }


def _score_semantic_skill_match(
    resume_skills: List[str],
    jd_required_skills: List[str],
    jd_preferred_skills: List[str],
    threshold: float = 0.58
) -> Dict:
    resume_skills = _dedupe_keep_order(_safe_lower_list(resume_skills))
    jd_required_skills = _dedupe_keep_order(_safe_lower_list(jd_required_skills))
    jd_preferred_skills = _dedupe_keep_order(_safe_lower_list(jd_preferred_skills))

    if not resume_skills:
        return {
            "score": 0.0,
            "required_matches": [],
            "preferred_matches": [],
        }

    def match_group(jd_skills: List[str]) -> List[Dict]:
        matches = []
        for jd_skill in jd_skills:
            scores = compute_batch_similarity(jd_skill, resume_skills)
            if not scores:
                continue

            best_idx = max(range(len(scores)), key=lambda i: scores[i])
            best_score = scores[best_idx]

            if best_score >= threshold:
                matches.append({
                    "jd_skill": jd_skill,
                    "resume_skill": resume_skills[best_idx],
                    "score": round(float(best_score), 4)
                })
        return matches

    required_matches = match_group(jd_required_skills)
    preferred_matches = match_group(jd_preferred_skills)

    required_score = (
        sum(item["score"] for item in required_matches) / len(jd_required_skills)
        if jd_required_skills else 0.0
    )
    preferred_score = (
        sum(item["score"] for item in preferred_matches) / len(jd_preferred_skills)
        if jd_preferred_skills else 0.0
    )

    semantic_skill_score = (0.7 * required_score) + (0.3 * preferred_score)

    return {
        "score": round(semantic_skill_score, 4),
        "required_matches": required_matches,
        "preferred_matches": preferred_matches,
    }


def _score_responsibility_match(
    resume_data: Dict,
    jd_responsibilities: List[str],
    threshold: float = 0.55
) -> Dict:
    sections = resume_data.get("sections", {}) or {}

    candidate_lines = []
    for key in ["experience", "projects", "summary", "objective"]:
        value = sections.get(key)
        if isinstance(value, list):
            candidate_lines.extend([str(v).strip() for v in value if str(v).strip()])
        elif isinstance(value, str) and value.strip():
            split_lines = [line.strip("•- ").strip() for line in value.split("\n")]
            candidate_lines.extend([line for line in split_lines if line])

    candidate_lines = _dedupe_keep_order(candidate_lines)
    jd_responsibilities = _dedupe_keep_order(
        [str(item).strip() for item in jd_responsibilities if str(item).strip()]
    )

    if not candidate_lines or not jd_responsibilities:
        return {
            "score": 0.0,
            "matched": [],
            "unmatched": jd_responsibilities,
            "coverage": 0.0,
        }

    matched = []
    unmatched = []

    for resp in jd_responsibilities:
        scores = compute_batch_similarity(resp, candidate_lines)
        best_idx = max(range(len(scores)), key=lambda i: scores[i])
        best_score = scores[best_idx]
        best_text = candidate_lines[best_idx]

        if best_score >= threshold:
            matched.append({
                "responsibility": resp,
                "matched_resume_line": best_text,
                "score": round(float(best_score), 4)
            })
        else:
            unmatched.append(resp)

    coverage = len(matched) / len(jd_responsibilities) if jd_responsibilities else 0.0
    avg_strength = (
        sum(item["score"] for item in matched) / len(matched)
        if matched else 0.0
    )
    final_resp_score = 0.6 * coverage + 0.4 * avg_strength

    return {
        "score": round(final_resp_score, 4),
        "matched": matched,
        "unmatched": unmatched,
        "coverage": round(float(coverage), 4),
    }


def _score_section_similarity(resume_data: Dict, jd_data: Dict) -> Dict:
    resume_sections = _extract_resume_sections(resume_data)
    jd_sections = _extract_jd_sections(jd_data)

    experience_vs_responsibilities = compute_similarity(
        resume_sections["experience"] or resume_sections["full_text"],
        jd_sections["responsibilities"] or jd_sections["full_text"]
    )

    projects_vs_requirements = compute_similarity(
        resume_sections["projects"] or resume_sections["full_text"],
        jd_sections["requirements"] or jd_sections["full_text"]
    )

    summary_vs_title = compute_similarity(
        (resume_sections["summary"] or resume_sections["full_text"])[:1200],
        " ".join([
            jd_sections["title"],
            jd_sections["summary"],
            jd_sections["requirements"]
        ]).strip()[:1200]
    )

    education_vs_requirements = compute_similarity(
        resume_sections["education"] or resume_sections["full_text"],
        jd_sections["requirements"] or jd_sections["full_text"]
    )

    overall_semantic = (
        0.40 * experience_vs_responsibilities +
        0.20 * projects_vs_requirements +
        0.25 * summary_vs_title +
        0.15 * education_vs_requirements
    )

    return {
        "experience_vs_responsibilities": round(float(experience_vs_responsibilities), 4),
        "projects_vs_requirements": round(float(projects_vs_requirements), 4),
        "summary_vs_title": round(float(summary_vs_title), 4),
        "education_vs_requirements": round(float(education_vs_requirements), 4),
        "overall_semantic_score": round(float(overall_semantic), 4),
    }


def _score_education_fit(resume_data: Dict, jd_data: Dict) -> Dict:
    resume_sections = resume_data.get("sections", {}) or {}
    education_text = _normalize_text_block(
        resume_sections.get("education") or resume_data.get("education", "")
    ).lower()

    qualifications = _normalize_text_block(
        " ".join(jd_data.get("qualifications", []) or [])
    ).lower()

    if not qualifications:
        return {
            "score": 0.6,
            "reason": "No explicit education requirement found in JD."
        }

    keywords = [
        "bachelor", "master", "phd", "computer engineering", "computer science",
        "marketing", "business", "finance", "hr", "management", "nursing"
    ]

    matched = [kw for kw in keywords if kw in qualifications and kw in education_text]

    if matched:
        return {
            "score": 1.0,
            "reason": f"Resume education appears aligned with JD requirements via: {', '.join(matched)}"
        }

    if education_text:
        return {
            "score": 0.5,
            "reason": "Education section exists, but direct alignment with JD was not strongly detected."
        }

    return {
        "score": 0.2,
        "reason": "No clear education evidence found in resume."
    }


def _score_experience_fit(resume_data: Dict, jd_data: Dict) -> Dict:
    sections = resume_data.get("sections", {}) or {}
    experience_text = _normalize_text_block(
        sections.get("experience") or resume_data.get("experience", "")
    )

    if not experience_text:
        return {
            "score": 0.25,
            "reason": "No clear experience section detected."
        }

    responsibilities = jd_data.get("responsibilities", []) or []
    if not responsibilities:
        return {
            "score": 0.65,
            "reason": "Experience section exists, but JD responsibility detail is limited."
        }

    semantic_score = compute_similarity(
        experience_text[:2000],
        " ".join(responsibilities)[:2000]
    )

    if semantic_score >= 0.75:
        reason = "Experience content strongly aligns with JD responsibilities."
    elif semantic_score >= 0.55:
        reason = "Experience content partially aligns with JD responsibilities."
    else:
        reason = "Experience section exists, but alignment with JD responsibilities is limited."

    return {
        "score": round(float(semantic_score), 4),
        "reason": reason
    }


def _score_domain_alignment(resume_data: Dict, jd_data: Dict) -> Dict:
    jd_text = _normalize_text_block(
        jd_data.get("cleaned_text") or jd_data.get("text", "")
    )
    resume_text = _normalize_text_block(
        resume_data.get("cleaned_text")
        or resume_data.get("text")
        or resume_data.get("raw_text", "")
    )

    jd_domain = predict_job_domain(jd_text)
    resume_domain = predict_job_domain(resume_text)

    same = jd_domain.get("domain") == resume_domain.get("domain")
    score = 1.0 if same else 0.45

    return {
        "score": round(float(score), 4),
        "jd_domain": jd_domain,
        "resume_domain": resume_domain,
        "aligned": same
    }


def calculate_v3_match_score(resume_data: Dict, jd_data: Dict) -> Dict:
    resume_skills = resume_data.get("skills", []) or []
    jd_required_skills = jd_data.get("required_skills", []) or []
    jd_preferred_skills = jd_data.get("preferred_skills", []) or []
    jd_responsibilities = jd_data.get("responsibilities", []) or []

    section_similarity = _score_section_similarity(resume_data, jd_data)
    exact_skill = _score_exact_skill_match(
        resume_skills,
        jd_required_skills,
        jd_preferred_skills
    )
    semantic_skill = _score_semantic_skill_match(
        resume_skills,
        jd_required_skills,
        jd_preferred_skills
    )
    responsibility_match = _score_responsibility_match(
        resume_data,
        jd_responsibilities
    )
    education_fit = _score_education_fit(resume_data, jd_data)
    experience_fit = _score_experience_fit(resume_data, jd_data)
    domain_alignment = _score_domain_alignment(resume_data, jd_data)

    combined_skill_score = (
        0.55 * exact_skill["score"] +
        0.45 * semantic_skill["score"]
    )

    final_score = (
        0.15 * domain_alignment["score"] +
        0.28 * section_similarity["overall_semantic_score"] +
        0.22 * responsibility_match["score"] +
        0.18 * combined_skill_score +
        0.10 * experience_fit["score"] +
        0.07 * education_fit["score"]
    )

    final_score = max(0.0, min(1.0, final_score))
    final_percentage = round(final_score * 100, 2)

    reasons = []
    if domain_alignment["aligned"]:
        reasons.append(
            f"Resume domain aligns with JD domain: {domain_alignment['jd_domain']['domain']}."
        )
    else:
        reasons.append(
            f"Resume domain ({domain_alignment['resume_domain']['domain']}) differs from JD domain ({domain_alignment['jd_domain']['domain']})."
        )

    reasons.append(
        f"Overall semantic similarity score: {section_similarity['overall_semantic_score']:.2f}"
    )
    reasons.append(
        f"Responsibility coverage: {responsibility_match['coverage']:.2f}"
    )
    reasons.append(
        f"Exact + semantic skill score: {combined_skill_score:.2f}"
    )
    reasons.append(experience_fit["reason"])
    reasons.append(education_fit["reason"])

    return {
        "final_score": final_score,
        "final_percentage": final_percentage,

        "domain_alignment": domain_alignment,
        "section_similarity": section_similarity,
        "exact_skill_match": exact_skill,
        "semantic_skill_match": semantic_skill,
        "combined_skill_score": round(float(combined_skill_score), 4),
        "responsibility_match": responsibility_match,
        "experience_fit": experience_fit,
        "education_fit": education_fit,

        "strengths": [
            f"Matched required skills: {', '.join(exact_skill['matched_required'][:8])}"
            if exact_skill["matched_required"] else "No strong exact required-skill matches detected.",
            f"Matched responsibilities: {len(responsibility_match['matched'])}/{len(jd_responsibilities) if jd_responsibilities else 0}",
            f"Predicted JD domain: {domain_alignment['jd_domain'].get('domain', 'unknown')}",
        ],

        "gaps": [
            f"Missing required skills: {', '.join(exact_skill['missing_required'][:8])}"
            if exact_skill["missing_required"] else "No major required skill gaps detected.",
            f"Unmatched responsibilities: {len(responsibility_match['unmatched'])}",
            "Domain mismatch detected."
            if not domain_alignment["aligned"] else "Domain appears aligned.",
        ],

        "reasons": reasons
    }