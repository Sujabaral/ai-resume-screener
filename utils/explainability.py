import re
from difflib import SequenceMatcher


def safe_text(text):
    return text if isinstance(text, str) else ""


def split_into_sentences(text):
    text = safe_text(text).strip()
    if not text:
        return []

    sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
    cleaned = [s.strip() for s in sentences if s and len(s.strip()) > 20]
    return cleaned


def similarity(a, b):
    a = safe_text(a).lower()
    b = safe_text(b).lower()
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def extract_best_sentence_matches(resume_text, job_text, top_n=5, min_score=0.25):
    resume_sentences = split_into_sentences(resume_text)
    job_sentences = split_into_sentences(job_text)

    matches = []

    for jd_sentence in job_sentences:
        best_resume_sentence = None
        best_score = 0.0

        for resume_sentence in resume_sentences:
            score = similarity(jd_sentence, resume_sentence)
            if score > best_score:
                best_score = score
                best_resume_sentence = resume_sentence

        if best_resume_sentence and best_score >= min_score:
            matches.append({
                "job_sentence": jd_sentence,
                "resume_sentence": best_resume_sentence,
                "score": round(best_score * 100, 2)
            })

    matches = sorted(matches, key=lambda x: x["score"], reverse=True)
    return matches[:top_n]


def build_explainable_summary(result):
    score = result.get("match_score", 0)
    semantic = result.get("semantic_score", 0)
    skills = result.get("skill_coverage", 0)
    responsibility = result.get("responsibility_score", 0)
    experience = result.get("experience_score", 0)
    education = result.get("education_score", 0)

    strengths = result.get("strengths", [])
    weaknesses = result.get("weaknesses", [])
    missing_skills = result.get("missing_skills", [])

    summary_parts = []

    if score >= 75:
        summary_parts.append("This resume shows strong overall fit for the job.")
    elif score >= 55:
        summary_parts.append("This resume shows moderate fit for the job with some good alignment.")
    else:
        summary_parts.append("This resume currently shows limited fit for the job.")

    if semantic >= 70:
        summary_parts.append("The resume language is strongly aligned with the job description.")
    elif semantic >= 50:
        summary_parts.append("The resume language is partially aligned with the job description.")
    else:
        summary_parts.append("The resume language does not strongly align with the job description.")

    if skills >= 70:
        summary_parts.append("Most required skills are covered.")
    elif skills >= 50:
        summary_parts.append("Some required skills are covered, but more could be added.")
    else:
        summary_parts.append("There are major required skill gaps.")

    if responsibility >= 60:
        summary_parts.append("Experience content reflects several job responsibilities.")
    else:
        summary_parts.append("Responsibility alignment is limited and should be strengthened.")

    if experience >= 60:
        summary_parts.append("Experience level appears relevant for the role.")
    if education >= 60:
        summary_parts.append("Education background supports the role reasonably well.")

    if strengths:
        summary_parts.append("Top strengths include: " + ", ".join(strengths[:3]) + ".")

    if weaknesses:
        summary_parts.append("Main weaknesses include: " + ", ".join(weaknesses[:3]) + ".")

    if missing_skills:
        summary_parts.append("Important missing skills include: " + ", ".join(missing_skills[:5]) + ".")

    return " ".join(summary_parts)


def build_score_reasoning(result):
    reasoning = []

    score_map = [
        ("Semantic alignment", result.get("semantic_score", 0)),
        ("Skill coverage", result.get("skill_coverage", 0)),
        ("Responsibility match", result.get("responsibility_score", 0)),
        ("Experience fit", result.get("experience_score", 0)),
        ("Education fit", result.get("education_score", 0)),
        ("Soft skill fit", result.get("soft_skill_score", 0)),
    ]

    for label, value in score_map:
        if value >= 70:
            reasoning.append(f"{label} is a strong area ({round(value, 2)}%).")
        elif value >= 50:
            reasoning.append(f"{label} is moderate ({round(value, 2)}%).")
        else:
            reasoning.append(f"{label} is weak ({round(value, 2)}%).")

    return reasoning