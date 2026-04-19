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
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


def score_label(score):
    if score >= 80:
        return "Excellent Match"
    if score >= 65:
        return "Strong Match"
    if score >= 50:
        return "Moderate Match"
    if score >= 35:
        return "Weak Match"
    return "Low Match"


def generate_badges(result, all_results):
    badges = []

    if result["rank"] == 1:
        badges.append("Top Overall Match")

    max_skill = max((r.get("skill_coverage", 0) for r in all_results), default=0)
    max_semantic = max((r.get("semantic_score", 0) for r in all_results), default=0)
    max_experience = max((r.get("experience_score", 0) for r in all_results), default=0)
    max_responsibility = max((r.get("responsibility_score", 0) for r in all_results), default=0)

    if result.get("skill_coverage", 0) == max_skill and max_skill > 0:
        badges.append("Best Skill Coverage")

    if result.get("semantic_score", 0) == max_semantic and max_semantic > 0:
        badges.append("Best Semantic Match")

    if result.get("experience_score", 0) == max_experience and max_experience > 0:
        badges.append("Best Experience Fit")

    if result.get("responsibility_score", 0) == max_responsibility and max_responsibility > 0:
        badges.append("Best Responsibility Match")

    if result["match_score"] >= 80:
        badges.append("Excellent Fit")
    elif result["match_score"] >= 65:
        badges.append("Strong Candidate")
    elif result["match_score"] >= 50:
        badges.append("Moderate Candidate")

    return badges


def build_weighted_breakdown(scores):
    return {
        "semantic": scores.get("semantic_score", 0),
        "skill": scores.get("skill_score", 0),
        "responsibility": scores.get("responsibility_score", 0),
        "experience": scores.get("experience_score", 0),
        "education": scores.get("education_score", 0),
        "keyword_alignment": scores.get("keyword_alignment_score", 0),
    }


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
        "",
        "Matched Skills:",
        ", ".join(result.get("matched_skills", [])) if result.get("matched_skills") else "None",
        "",
        "Missing Skills:",
        ", ".join(result.get("missing_skills", [])) if result.get("missing_skills") else "None",
        "",
        "Strengths:"
    ]

    for item in result.get("strengths", []):
        report_lines.append(f"- {item}")

    report_lines.append("")
    report_lines.append("Weaknesses:")
    for item in result.get("suggestions", []):
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
        pdf.drawString(40, y, text[:110])
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
    for item in result.get("strengths", []):
        write_line(f"- {item}")

    write_line("")
    write_line("Weaknesses", "Helvetica-Bold", 12, 18)
    for item in result.get("suggestions", []):
        write_line(f"- {item}")

    write_line("")
    write_line("AI Explanation", "Helvetica-Bold", 12, 18)
    explanation = result.get("ai_explanation", "")
    for part in explanation.split(". "):
        if part.strip():
            write_line(part.strip() + ".")

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

            result = {
                "resume_filename": filename,
                "candidate_name": resume_data.get("name", filename),
                "match_score": float(scores.get("final_score", 0.0)),
                "match_label": score_label(float(scores.get("final_score", 0.0))),
                "semantic_score": float(scores.get("semantic_score", 0.0)),
                "skill_coverage": float(scores.get("skill_score", 0.0)),
                "responsibility_score": float(scores.get("responsibility_score", 0.0)),
                "experience_score": float(scores.get("experience_score", 0.0)),
                "education_score": float(scores.get("education_score", 0.0)),
                "keyword_alignment_score": float(scores.get("keyword_alignment_score", 0.0)),
                "matched_skills": scores.get("matched_skills", []),
                "missing_skills": scores.get("missing_skills", []),
                "strengths": summary.get("strengths", []),
                "suggestions": summary.get("weaknesses", []),
                "ai_explanation": summary.get("explanation", ""),
                "resume_preview": resume_data.get("clean_text", "")[:1000],
                "job_description_preview": job_description[:1000],
                "job_domain": jd_data.get("domain", "general"),
                "weighted_breakdown": build_weighted_breakdown(scores),
            }

            results.append(result)

        except Exception as e:
            print(f"Error processing {resume_file.filename}: {e}")
            continue

    if not results:
        return "No valid PDF files processed."

    results = sorted(
        results,
        key=lambda x: float(x.get("match_score", 0.0)),
        reverse=True
    )

    for i, result in enumerate(results, start=1):
        result["rank"] = i

    latest_result = results

    for result in results:
        result["badges"] = generate_badges(result, results)

    top_result = results[0]

    top_summary = {
        "resume_filename": top_result["resume_filename"],
        "candidate_name": top_result.get("candidate_name", top_result["resume_filename"]),
        "match_score": top_result["match_score"],
        "match_label": top_result["match_label"],
        "job_domain": top_result.get("job_domain", "general"),
        "matched_count": len(top_result["matched_skills"]),
        "missing_count": len(top_result["missing_skills"]),
        "why_top": []
    }

    if top_result["semantic_score"] >= 70:
        top_summary["why_top"].append("Strong semantic alignment with the job description.")
    if top_result["skill_coverage"] >= 60:
        top_summary["why_top"].append("High required skill coverage compared to other resumes.")
    if top_result["responsibility_score"] >= 55:
        top_summary["why_top"].append("Responsibilities align well with the job requirements.")
    if top_result["experience_score"] >= 60:
        top_summary["why_top"].append("Experience level fits the role reasonably well.")
    if top_result["education_score"] >= 70:
        top_summary["why_top"].append("Education background matches the job requirement.")
    if not top_summary["why_top"]:
        top_summary["why_top"].append("This resume ranked highest within the uploaded batch.")

    comparison_chart = {
        "labels": [r["resume_filename"] for r in results],
        "match_scores": [r["match_score"] for r in results],
        "semantic_scores": [r["semantic_score"] for r in results],
        "skill_scores": [r["skill_coverage"] for r in results],
        "responsibility_scores": [r["responsibility_score"] for r in results],
    }

    radar_chart = {
        "labels": ["Semantic", "Skills", "Responsibilities", "Experience", "Education"],
        "datasets": [
            {
                "label": r["resume_filename"],
                "data": [
                    r["semantic_score"],
                    r["skill_coverage"],
                    r["responsibility_score"],
                    r["experience_score"],
                    r["education_score"]
                ]
            }
            for r in results[:3]
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