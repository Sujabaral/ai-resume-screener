from flask import Flask, render_template, request, Response
import os
from io import BytesIO
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from config import Config
from utils.pdf_parser import extract_text_from_pdf
from utils.resume_parser import parse_resume
from utils.jd_parser import parse_job_description
from utils.scorer import calculate_match_score
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

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

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
            scores = calculate_match_score(resume_data, jd_data)
            summary = generate_result_summary(scores, resume_data, jd_data)

            final_score = round_score(scores.get("final_score", 0.0))

            result = {
                "resume_filename": filename,
                "candidate_name": resume_data.get("name", filename),

                "match_score": final_score,
                "match_label": scores.get("score_label", "Low Match"),

                "semantic_score": round_score(scores.get("semantic_score", 0.0)),
                "skill_coverage": round_score(scores.get("skills_score", 0.0)),
                "responsibility_score": round_score(scores.get("responsibilities_score", 0.0)),
                "experience_score": round_score(scores.get("experience_score", 0.0)),
                "education_score": round_score(scores.get("education_score", 0.0)),
                "soft_skill_score": round_score(scores.get("soft_skills_score", 0.0)),

                "matched_skills": scores.get("matched_skills", []),
                "missing_skills": scores.get("missing_skills", []),
                "matched_soft_skills": scores.get("matched_soft_skills", []),
                "missing_soft_skills": scores.get("missing_soft_skills", []),

                "strengths": summary.get("strengths", scores.get("strengths", [])),
                "weaknesses": summary.get("weaknesses", scores.get("weaknesses", [])),
                "insights": summary.get("insights", []),

                "ai_explanation": summary.get("explanation", ""),

                "resume_preview": resume_data.get("clean_text", "")[:1000],
                "job_description_preview": job_description[:1000],
                "job_domain": jd_data.get("job_domain", "general"),

                "weights": build_weights(scores),
            }

            results.append(normalize_result_structure(result))

        except Exception as e:
            print(f"Error processing {resume_file.filename}: {e}")
            continue

    if not results:
        return "No valid PDF files processed."

    results = sorted(
        results,
        key=lambda x: safe_float(x.get("match_score", 0.0)),
        reverse=True
    )

    for i, result in enumerate(results, start=1):
        result["rank"] = i
        result["match_label"] = get_relative_label(result.get("match_score", 0), i)

    for result in results:
        result["badges"] = generate_badges(result, results)

    latest_result = results
    top_result = results[0]

    top_summary = {
        "resume_filename": top_result.get("resume_filename", "Unknown"),
        "candidate_name": top_result.get(
            "candidate_name",
            top_result.get("resume_filename", "Unknown")
        ),
        "match_score": top_result.get("match_score", 0),
        "match_label": top_result.get("match_label", "N/A"),
        "job_domain": top_result.get("job_domain", "general"),
        "matched_count": len(top_result.get("matched_skills", [])),
        "missing_count": len(top_result.get("missing_skills", [])),
        "why_top": []
    }

    if top_result.get("semantic_score", 0) >= 70:
        top_summary["why_top"].append("Strong semantic alignment with the job description.")
    if top_result.get("skill_coverage", 0) >= 60:
        top_summary["why_top"].append("High required skill coverage compared to other resumes.")
    if top_result.get("responsibility_score", 0) >= 55:
        top_summary["why_top"].append("Responsibilities align well with the job requirements.")
    if top_result.get("experience_score", 0) >= 60:
        top_summary["why_top"].append("Experience level fits the role reasonably well.")
    if top_result.get("education_score", 0) >= 70:
        top_summary["why_top"].append("Education background matches the job requirement.")
    if top_result.get("soft_skill_score", 0) >= 60:
        top_summary["why_top"].append("Soft skills are strongly reflected in the resume.")

    if not top_summary["why_top"]:
        if top_result.get("match_score", 0) < 40:
            top_summary["why_top"].append(
                "This resume ranked highest in the current uploaded batch, but overall fit is still limited."
            )
        else:
            top_summary["why_top"].append(
                "This resume ranked highest within the uploaded batch."
            )

    comparison_chart = {
        "labels": [
            r.get("candidate_name", r.get("resume_filename", f"Resume {idx + 1}"))
            for idx, r in enumerate(results)
        ],
        "match_scores": [r.get("match_score", 0) for r in results],
        "semantic_scores": [r.get("semantic_score", 0) for r in results],
        "skill_scores": [r.get("skill_coverage", 0) for r in results],
        "responsibility_scores": [r.get("responsibility_score", 0) for r in results],
        "experience_scores": [r.get("experience_score", 0) for r in results],
        "education_scores": [r.get("education_score", 0) for r in results],
        "soft_skill_scores": [r.get("soft_skill_score", 0) for r in results],
    }

    radar_chart = {
        "labels": ["Semantic", "Skills", "Responsibilities", "Experience", "Education", "Soft Skills"],
        "datasets": [
            {
                "label": r.get("candidate_name", r.get("resume_filename", f"Resume {idx + 1}")),
                "data": [
                    r.get("semantic_score", 0),
                    r.get("skill_coverage", 0),
                    r.get("responsibility_score", 0),
                    r.get("experience_score", 0),
                    r.get("education_score", 0),
                    r.get("soft_skill_score", 0)
                ]
            }
            for idx, r in enumerate(results[:3])
        ]
    }

    return render_template(
        "ranking.html",
        results=results,
        top_summary=top_summary,
        comparison_chart=comparison_chart,
        radar_chart=radar_chart,
        jd_data=jd_data
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