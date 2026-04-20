from flask import Flask, render_template, request, Response
import os
from io import BytesIO
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from utils.explainability import (
    extract_best_sentence_matches,
    build_explainable_summary,
    build_score_reasoning,
)
from config import Config
from utils.v3_scorer import calculate_v3_match_score
from utils.pdf_parser import extract_text_from_pdf
from utils.resume_parser import parse_resume
from utils.jd_parser import parse_job_description
from utils.summarizer import generate_result_summary
app = Flask(__name__)
app.config.from_object(Config)

latest_result = []


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def round_score(value, digits=2):
    return round(safe_float(value), digits)


def get_relative_label(score, rank):
    """
    Rank is relative to uploaded batch.
    Label reflects absolute fit.
    """
    score = safe_float(score)

    if score >= 80:
        return "Excellent Match"
    if score >= 65:
        return "Strong Match"
    if score >= 50:
        return "Moderate Match"
    if score >= 35:
        return "Weak Fit"
    if rank == 1:
        return "Low Match (Top in batch)"
    return "Low Match"


def build_weights(scores):
    """
    Build clean component snapshot for UI.
    """
    return {
        "semantic_score": round_score(scores.get("semantic_score", 0.0)),
        "skill_match_score": round_score(scores.get("skills_score", 0.0)),
        "responsibility_score": round_score(scores.get("responsibilities_score", 0.0)),
        "experience_score": round_score(scores.get("experience_score", 0.0)),
        "education_score": round_score(scores.get("education_score", 0.0)),
        "soft_skill_score": round_score(scores.get("soft_skills_score", 0.0)),
    }


def normalize_result_structure(result):
    result.setdefault("semantic_score", 0.0)
    result.setdefault("skill_coverage", 0.0)
    result.setdefault("responsibility_score", 0.0)
    result.setdefault("experience_score", 0.0)
    result.setdefault("education_score", 0.0)
    result.setdefault("soft_skill_score", 0.0)
    result.setdefault("matched_skills", [])
    result.setdefault("missing_skills", [])
    result.setdefault("responsibility_matches", [])
    result.setdefault("suggestions", [])
    result.setdefault("sentence_matches", [])
    result.setdefault("score_reasoning", [])
    result.setdefault("matched_soft_skills", [])
    result.setdefault("missing_soft_skills", [])
    result.setdefault("strengths", [])
    result.setdefault("weaknesses", [])
    result.setdefault("insights", [])
    result.setdefault("badges", [])
    result.setdefault("ai_explanation", "")
    result.setdefault("resume_preview", "")
    result.setdefault("job_domain", "general")
    result.setdefault(
        "candidate_name",
        result.get("resume_filename", "Unknown Candidate")
    )
    result.setdefault("match_label", "Low Match")
    result.setdefault("weights", {
        "semantic_score": result.get("semantic_score", 0.0),
        "skill_match_score": result.get("skill_coverage", 0.0),
        "responsibility_score": result.get("responsibility_score", 0.0),
        "experience_score": result.get("experience_score", 0.0),
        "education_score": result.get("education_score", 0.0),
        "soft_skill_score": result.get("soft_skill_score", 0.0),
    })
    return result


def generate_badges(result, all_results):
    badges = []

    if result.get("rank") == 1:
        badges.append("Top Candidate")

    max_skill = max((safe_float(r.get("skill_coverage", 0)) for r in all_results), default=0)
    max_semantic = max((safe_float(r.get("semantic_score", 0)) for r in all_results), default=0)
    max_experience = max((safe_float(r.get("experience_score", 0)) for r in all_results), default=0)
    max_responsibility = max((safe_float(r.get("responsibility_score", 0)) for r in all_results), default=0)
    max_education = max((safe_float(r.get("education_score", 0)) for r in all_results), default=0)
    max_soft_skill = max((safe_float(r.get("soft_skill_score", 0)) for r in all_results), default=0)

    if safe_float(result.get("skill_coverage", 0)) == max_skill and max_skill > 0:
        badges.append("Best Skill Coverage")

    if safe_float(result.get("semantic_score", 0)) == max_semantic and max_semantic > 0:
        badges.append("Best Semantic Match")

    if safe_float(result.get("experience_score", 0)) == max_experience and max_experience > 0:
        badges.append("Best Experience Fit")

    if safe_float(result.get("responsibility_score", 0)) == max_responsibility and max_responsibility > 0:
        badges.append("Best Responsibility Match")

    if safe_float(result.get("education_score", 0)) == max_education and max_education > 0:
        badges.append("Best Education Fit")

    if safe_float(result.get("soft_skill_score", 0)) == max_soft_skill and max_soft_skill > 0:
        badges.append("Best Soft Skills")

    if safe_float(result.get("match_score", 0)) >= 80:
        badges.append("Excellent Overall Fit")
    elif safe_float(result.get("match_score", 0)) >= 65:
        badges.append("Strong Overall Fit")
    elif safe_float(result.get("match_score", 0)) >= 50:
        badges.append("Moderate Overall Fit")

    return badges


def build_report_text(result):
    report_lines = [
        "AI Resume Screener & Job Match Report",
        "=" * 45,
        f"Resume File: {result.get('resume_filename', 'Unknown')}",
        f"Candidate Name: {result.get('candidate_name', 'Unknown')}",
        f"Job Domain: {result.get('job_domain', 'general')}",
        f"Final Match Score: {result.get('match_score', 0)}%",
        f"Match Label: {result.get('match_label', 'N/A')}",
        f"Semantic Score: {result.get('semantic_score', 0)}%",
        f"Skill Score: {result.get('skill_coverage', 0)}%",
        f"Responsibility Score: {result.get('responsibility_score', 0)}%",
        f"Experience Score: {result.get('experience_score', 0)}%",
        f"Education Score: {result.get('education_score', 0)}%",
        f"Soft Skill Score: {result.get('soft_skill_score', 0)}%",
        "",
        "Matched Skills:",
        ", ".join(result.get("matched_skills", [])) if result.get("matched_skills") else "None",
        "",
        "Missing Skills:",
        ", ".join(result.get("missing_skills", [])) if result.get("missing_skills") else "None",
        "",
        "Matched Soft Skills:",
        ", ".join(result.get("matched_soft_skills", [])) if result.get("matched_soft_skills") else "None",
        "",
        "Missing Soft Skills:",
        ", ".join(result.get("missing_soft_skills", [])) if result.get("missing_soft_skills") else "None",
        "",
        "Strengths:"
    ]

    for item in result.get("strengths", []):
        report_lines.append(f"- {item}")

    report_lines.append("")
    report_lines.append("Weaknesses:")
    for item in result.get("weaknesses", []):
        report_lines.append(f"- {item}")

    report_lines.append("")
    report_lines.append("AI Explanation:")
    report_lines.append(result.get("ai_explanation", "No explanation available."))

    return "\n".join(report_lines)


def build_pdf_report(result):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50

    def write_line(text, font="Helvetica", size=10, gap=16):
        nonlocal y
        pdf.setFont(font, size)
        pdf.drawString(40, y, str(text)[:110])
        y -= gap
        if y < 60:
            pdf.showPage()
            y = height - 50

    write_line("AI Resume Screener & Job Match Report", "Helvetica-Bold", 16, 24)
    write_line(f"Candidate Name: {result.get('candidate_name', 'Unknown')}")
    write_line(f"Resume File: {result.get('resume_filename', 'Unknown')}")
    write_line(f"Job Domain: {result.get('job_domain', 'general')}")
    write_line(f"Final Match Score: {result.get('match_score', 0)}%")
    write_line(f"Match Label: {result.get('match_label', 'N/A')}")
    write_line("")
    write_line("Score Breakdown", "Helvetica-Bold", 12, 18)
    write_line(f"Semantic Score: {result.get('semantic_score', 0)}%")
    write_line(f"Skill Score: {result.get('skill_coverage', 0)}%")
    write_line(f"Responsibility Score: {result.get('responsibility_score', 0)}%")
    write_line(f"Experience Score: {result.get('experience_score', 0)}%")
    write_line(f"Education Score: {result.get('education_score', 0)}%")
    write_line(f"Soft Skill Score: {result.get('soft_skill_score', 0)}%")
    write_line("")

    write_line("Matched Skills", "Helvetica-Bold", 12, 18)
    matched = result.get("matched_skills", [])
    if matched:
        for skill in matched:
            write_line(f"- {skill}")
    else:
        write_line("- None")

    write_line("")
    write_line("Missing Skills", "Helvetica-Bold", 12, 18)
    missing = result.get("missing_skills", [])
    if missing:
        for skill in missing:
            write_line(f"- {skill}")
    else:
        write_line("- None")

    write_line("")
    write_line("Strengths", "Helvetica-Bold", 12, 18)
    strengths = result.get("strengths", [])
    if strengths:
        for item in strengths:
            write_line(f"- {item}")
    else:
        write_line("- None")

    write_line("")
    write_line("Weaknesses", "Helvetica-Bold", 12, 18)
    weaknesses = result.get("weaknesses", [])
    if weaknesses:
        for item in weaknesses:
            write_line(f"- {item}")
    else:
        write_line("- None")

    write_line("")
    write_line("AI Explanation", "Helvetica-Bold", 12, 18)
    explanation = result.get("ai_explanation", "")
    if explanation:
        for part in explanation.split(". "):
            if part.strip():
                line = part.strip()
                if not line.endswith("."):
                    line += "."
                write_line(line)
    else:
        write_line("No explanation available.")

    pdf.save()
    buffer.seek(0)
    return buffer


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    global latest_result

    resume_files = request.files.getlist("resumes")
    job_description = request.form.get("job_description", "").strip()

    if not resume_files or all(f.filename.strip() == "" for f in resume_files):
        return "No resumes uploaded."

    if not job_description:
        return "Job description is required."

    def score_label(score):
        score = float(score or 0)
        if score >= 70:
            return "strong"
        elif score >= 50:
            return "moderate"
        return "weak"

    def safe_text(value, fallback="N/A"):
        if value is None:
            return fallback
        value = str(value).strip()
        return value if value else fallback

    results = []
    jd_data = parse_job_description(job_description)

    for resume_file in resume_files:
        if not resume_file or resume_file.filename.strip() == "":
            continue

        if not allowed_file(resume_file.filename):
            continue

        filename = secure_filename(resume_file.filename)

        try:
            resume_text = extract_text_from_pdf(resume_file)
            if not resume_text or not resume_text.strip():
                continue

            resume_data = parse_resume(resume_text)
            v3_result = calculate_v3_match_score(resume_data, jd_data)

            semantic = v3_result["section_similarity"]["overall_semantic_score"] * 100
            skills = v3_result["combined_skill_score"] * 100
            responsibility = v3_result["responsibility_match"]["score"] * 100
            experience = v3_result["experience_fit"]["score"] * 100
            education = v3_result["education_fit"]["score"] * 100
            soft_skill = min(100, (semantic * 0.4 + responsibility * 0.6))

            final_score = round_score(v3_result.get("final_percentage", 0))

            matched_skills = v3_result["exact_skill_match"].get("matched_required", [])
            missing_skills = v3_result["exact_skill_match"].get("missing_required", [])

            responsibility_matches = []
            for item in v3_result["responsibility_match"].get("matched", []):
                responsibility_matches.append(f"Matched responsibility: {item}")

            suggestions = []
            if skills < 60:
                suggestions.append("Add more relevant technical or domain-specific skills.")
            if responsibility < 50:
                suggestions.append("Include more experience aligned with job responsibilities.")
            if experience < 50:
                suggestions.append("Highlight relevant work experience more clearly.")
            if education < 60:
                suggestions.append("Mention relevant academic qualifications clearly.")
            if missing_skills:
                suggestions.append("Consider adding missing skills: " + ", ".join(missing_skills[:5]))

            sentence_matches = extract_best_sentence_matches(
                resume_text=resume_text,
                job_text=job_description,
                top_n=5,
                min_score=0.25
            )

            evidence_matches = []
            for item in sentence_matches[:5]:
                evidence_matches.append({
                    "job_text": safe_text(item.get("job_sentence", ""), ""),
                    "resume_text": safe_text(item.get("resume_sentence", ""), ""),
                    "similarity": round(float(item.get("score", 0)) * 100, 2)
                })

            result = {
                "resume_filename": filename,
                "candidate_name": resume_data.get("name", filename),

                "match_score": round_score(final_score),
                "match_label": "",

                "semantic_score": round_score(semantic),
                "skill_coverage": round_score(skills),
                "responsibility_score": round_score(responsibility),
                "experience_score": round_score(experience),
                "education_score": round_score(education),
                "soft_skill_score": round_score(soft_skill),

                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "matched_soft_skills": [],
                "missing_soft_skills": [],

                "responsibility_matches": responsibility_matches,
                "suggestions": suggestions,

                "strengths": v3_result.get("strengths", []),
                "weaknesses": v3_result.get("gaps", []),
                "insights": v3_result.get("reasons", []),

                "resume_preview": resume_data.get("clean_text", "")[:1000],
                "job_description_preview": job_description[:1000],
                "job_domain": v3_result["domain_alignment"]["jd_domain"]["domain"],

                "sentence_matches": sentence_matches,
                "evidence_matches": evidence_matches,

                "weights": build_weights({
                    "semantic_score": semantic,
                    "skills_score": skills,
                    "responsibilities_score": responsibility,
                    "experience_score": experience,
                    "education_score": education,
                    "soft_skills_score": soft_skill,
                }),
            }

            result["ai_explanation"] = build_explainable_summary(result)
            result["score_reasoning"] = build_score_reasoning(result)

            # normalize if you already have this helper
            result = normalize_result_structure(result)

            # make template-compatible keys
            result["name"] = safe_text(
                result.get("name") or result.get("candidate_name"),
                "Unknown Candidate"
            )
            result["filename"] = safe_text(
                result.get("filename") or result.get("resume_filename"),
                "Unknown File"
            )
            result["predicted_domain"] = safe_text(
                result.get("predicted_domain") or result.get("job_domain"),
                "unknown"
            )

            result["final_score"] = round(float(
                result.get("final_score", result.get("match_score", 0))
            ), 2)

            result["semantic_score"] = round(float(result.get("semantic_score", 0)), 2)
            result["skill_score"] = round(float(
                result.get("skill_score", result.get("skill_coverage", 0))
            ), 2)
            result["responsibility_score"] = round(float(result.get("responsibility_score", 0)), 2)
            result["experience_score"] = round(float(result.get("experience_score", 0)), 2)
            result["education_score"] = round(float(result.get("education_score", 0)), 2)
            result["soft_skill_score"] = round(float(result.get("soft_skill_score", 0)), 2)

            result["semantic_score_label"] = score_label(result["semantic_score"])
            result["skill_score_label"] = score_label(result["skill_score"])
            result["responsibility_score_label"] = score_label(result["responsibility_score"])
            result["experience_score_label"] = score_label(result["experience_score"])
            result["education_score_label"] = score_label(result["education_score"])
            result["soft_skill_score_label"] = score_label(result["soft_skill_score"])

            result["matched_skills"] = list(dict.fromkeys(result.get("matched_skills", [])))[:20]
            result["missing_skills"] = list(dict.fromkeys(result.get("missing_skills", [])))[:20]
            result["strengths"] = result.get("strengths", [])[:6]
            result["weaknesses"] = result.get("weaknesses", [])[:6]

            # reasoning_points for template
            result["reasoning_points"] = result.get("score_reasoning", [])[:6]

            explanation = safe_text(result.get("ai_explanation"), "No explanation available.")
            result["ai_explanation"] = explanation[:900]

            cleaned_evidence = []
            for ev in result.get("evidence_matches", [])[:5]:
                cleaned_evidence.append({
                    "job_text": safe_text(ev.get("job_text"), ""),
                    "resume_text": safe_text(ev.get("resume_text"), ""),
                    "similarity": round(float(ev.get("similarity", 0)), 2)
                })
            result["evidence_matches"] = cleaned_evidence

            results.append(result)

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue

    if not results:
        return "No valid resumes processed."

    # sort by final score
    results = sorted(results, key=lambda x: float(x.get("final_score", 0)), reverse=True)

    # best-score flags
    best_final_idx = max(range(len(results)), key=lambda i: results[i].get("final_score", 0))
    best_skill_idx = max(range(len(results)), key=lambda i: results[i].get("skill_score", 0))
    best_semantic_idx = max(range(len(results)), key=lambda i: results[i].get("semantic_score", 0))
    best_experience_idx = max(range(len(results)), key=lambda i: results[i].get("experience_score", 0))
    best_education_idx = max(range(len(results)), key=lambda i: results[i].get("education_score", 0))
    best_soft_idx = max(range(len(results)), key=lambda i: results[i].get("soft_skill_score", 0))

    for i, r in enumerate(results, start=1):
        r["rank"] = i
        r["match_score"] = r["final_score"]
        r["match_label"] = get_relative_label(r["final_score"], i)
        r["badges"] = generate_badges(r, results)

        r["best_final"] = (i - 1) == best_final_idx
        r["best_skill"] = (i - 1) == best_skill_idx
        r["best_semantic"] = (i - 1) == best_semantic_idx
        r["best_experience"] = (i - 1) == best_experience_idx
        r["best_education"] = (i - 1) == best_education_idx
        r["best_softskills"] = (i - 1) == best_soft_idx

    latest_result = results

    chart_labels = [r["name"] for r in results]
    chart_final_scores = [r["final_score"] for r in results]
    chart_semantic_scores = [r["semantic_score"] for r in results]
    chart_skill_scores = [r["skill_score"] for r in results]
    chart_responsibility_scores = [r["responsibility_score"] for r in results]

    top_three = results[:3]
    radar_labels = ["Semantic", "Skills", "Responsibilities", "Experience", "Education", "Soft Skills"]
    radar_datasets = [
        {
            "label": r["name"],
            "data": [
                r["semantic_score"],
                r["skill_score"],
                r["responsibility_score"],
                r["experience_score"],
                r["education_score"],
                r["soft_skill_score"]
            ]
        }
        for r in top_three
    ]

    return render_template(
        "ranking.html",
        results=results,
        chart_labels=chart_labels,
        chart_final_scores=chart_final_scores,
        chart_semantic_scores=chart_semantic_scores,
        chart_skill_scores=chart_skill_scores,
        chart_responsibility_scores=chart_responsibility_scores,
        radar_labels=radar_labels,
        radar_datasets=radar_datasets
    )
    
@app.route("/download-report")
def download_report():
    global latest_result

    if not latest_result:
        return "No report available yet. Please analyze a resume first."

    pdf_buffer = build_pdf_report(latest_result[0])

    return Response(
        pdf_buffer.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=top_resume_report.pdf"}
    )


if __name__ == "__main__":
    app.run(debug=True)