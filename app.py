from flask import Flask, render_template, request, Response
import os

from config import Config
from utils.pdf_parser import extract_resume_text
from utils.resume_parser import split_into_sections, extract_contact_info
from utils.text_preprocessor import preprocess_text
from utils.skill_extractor import extract_skills, extract_skills_by_category
from utils.jd_parser import parse_job_description
from utils.scorer import calculate_final_score

app = Flask(__name__)
app.config.from_object(Config)

latest_result = {}


def build_resume_data(pdf_path: str) -> dict:
    raw_text = extract_resume_text(pdf_path)
    cleaned_text = preprocess_text(raw_text)
    sections = split_into_sections(raw_text)
    skills = extract_skills(cleaned_text)
    contact = extract_contact_info(raw_text)

    return {
        "raw_text": raw_text,
        "cleaned_text": cleaned_text,
        "sections": sections,
        "skills": skills,
        "contact": contact
    }


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


def generate_category_feedback(resume_categories, jd_categories):
    feedback = []

    for category, jd_skills in jd_categories.items():
        resume_skills = resume_categories.get(category, [])

        matched = set(resume_skills) & set(jd_skills)
        missing = set(jd_skills) - set(resume_skills)

        category_name = category.replace("_", " ").title()

        if matched and not missing:
            feedback.append(f"Strong alignment in {category_name}.")
        elif matched and missing:
            feedback.append(
                f"Partial match in {category_name}. Missing: {', '.join(sorted(missing))}."
            )
        else:
            feedback.append(
                f"No strong evidence of required {category_name} skills in the resume."
            )

    return feedback


def generate_strengths(match_score, skill_coverage, matched_skills, resume_categories):
    strengths = []

    if match_score >= 70:
        strengths.append("The resume has strong overall similarity with the target job description.")

    if skill_coverage >= 70:
        strengths.append("A good portion of the required skills are already present in the resume.")

    if len(matched_skills) >= 5:
        strengths.append("Multiple relevant skills were matched successfully.")

    if "programming" in resume_categories:
        strengths.append("Programming skills are clearly visible in the resume.")

    if "tools" in resume_categories:
        strengths.append("The resume includes useful development tools and workflow knowledge.")

    if not strengths:
        strengths.append("The resume shows some relevant background, but needs stronger alignment.")

    return strengths


def generate_suggestions(match_score, skill_coverage, missing_skills, resume_categories, jd_categories):
    suggestions = []

    if match_score >= 75:
        suggestions.append("Strong overall text similarity with the job description.")
    elif match_score >= 50:
        suggestions.append("Moderate overall match. Resume can be tailored further.")
    else:
        suggestions.append("Low overall match. Consider tailoring your resume significantly.")

    if skill_coverage >= 75:
        suggestions.append("Good coverage of required skills.")
    elif skill_coverage >= 50:
        suggestions.append("Decent skill coverage, but some important skills are still missing.")
    else:
        suggestions.append("Skill coverage is low based on the detected job requirements.")

    if missing_skills:
        suggestions.append(
            "Consider adding or strengthening these skills if you have them: "
            + ", ".join(missing_skills)
        )

    for category, jd_skills in jd_categories.items():
        resume_skills = resume_categories.get(category, [])
        missing_in_category = set(jd_skills) - set(resume_skills)

        if missing_in_category:
            category_name = category.replace("_", " ").title()
            suggestions.append(
                f"Focus on improving {category_name} areas such as: {', '.join(sorted(missing_in_category))}."
            )

    if not missing_skills:
        suggestions.append("No major missing skills detected from the current skill list.")

    return suggestions


def build_report_text(result):
    report_lines = [
        "AI Resume Screener & Job Match Report",
        "=" * 40,
        f"Resume File: {result['resume_filename']}",
        f"Match Score: {result['match_score']}%",
        f"Skill Coverage: {result['skill_coverage']}%",
        "",
        "Matched Skills:",
        ", ".join(result["matched_skills"]) if result["matched_skills"] else "None",
        "",
        "Missing Skills:",
        ", ".join(result["missing_skills"]) if result["missing_skills"] else "None",
        "",
        "Strengths Summary:"
    ]

    for item in result["strengths"]:
        report_lines.append(f"- {item}")

    report_lines.append("")
    report_lines.append("Suggestions:")

    for item in result["suggestions"]:
        report_lines.append(f"- {item}")

    report_lines.append("")
    report_lines.append("Resume Skill Categories:")

    if result["resume_categories"]:
        for category, skills in result["resume_categories"].items():
            report_lines.append(f"- {category.replace('_', ' ').title()}: {', '.join(skills)}")
    else:
        report_lines.append("- None")

    report_lines.append("")
    report_lines.append("Job Description Skill Categories:")

    if result["jd_categories"]:
        for category, skills in result["jd_categories"].items():
            report_lines.append(f"- {category.replace('_', ' ').title()}: {', '.join(skills)}")
    else:
        report_lines.append("- None")

    report_lines.append("")
    report_lines.append("Resume Contact Info:")

    if result["contact_info"]:
        for key, value in result["contact_info"].items():
            if value:
                report_lines.append(f"- {key.title()}: {value}")
    else:
        report_lines.append("- None")

    return "\n".join(report_lines)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    global latest_result

    if "resume" not in request.files:
        return "No resume file uploaded."

    resume_file = request.files["resume"]
    job_description = request.form.get("job_description", "")

    if resume_file.filename == "":
        return "No selected file."

    if not allowed_file(resume_file.filename):
        return "Only PDF files are allowed."

    if not job_description.strip():
        return "Job description is required."

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    save_path = os.path.join(app.config["UPLOAD_FOLDER"], resume_file.filename)
    resume_file.save(save_path)

    resume_data = build_resume_data(save_path)
    jd_data = parse_job_description(job_description)

    scores = calculate_final_score(resume_data, jd_data)

    match_score = scores["final_score"]
    skill_score = scores["skill_score"]

    resume_skills = resume_data["skills"]
    jd_skills = jd_data["skills"]

    matched_skills = sorted(set(resume_skills) & set(jd_skills))
    missing_skills = sorted(set(jd_skills) - set(resume_skills))

    resume_categories = extract_skills_by_category(resume_data["cleaned_text"])
    jd_categories = extract_skills_by_category(jd_data["cleaned_text"])

    strengths = generate_strengths(
        match_score, skill_score, matched_skills, resume_categories
    )

    suggestions = generate_suggestions(
        match_score, skill_score, missing_skills, resume_categories, jd_categories
    )

    category_feedback = generate_category_feedback(resume_categories, jd_categories)
    suggestions.extend(category_feedback)

    latest_result = {
        "resume_filename": resume_file.filename,
        "match_score": match_score,
        "skill_coverage": skill_score,
        "overall_similarity": scores["overall_similarity"],
        "skill_score": scores["skill_score"],
        "experience_score": scores["experience_score"],
        "project_score": scores["project_score"],
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "strengths": strengths,
        "suggestions": suggestions,
        "resume_preview": resume_data["cleaned_text"][:1000],
        "job_description_preview": jd_data["cleaned_text"][:1000],
        "resume_categories": resume_categories,
        "jd_categories": jd_categories,
        "contact_info": resume_data["contact"],
        "resume_sections": resume_data["sections"]
    }

    return render_template("result.html", result=latest_result)


@app.route("/download-report")
def download_report():
    global latest_result

    if not latest_result:
        return "No report available yet. Please analyze a resume first."

    report_text = build_report_text(latest_result)

    return Response(
        report_text,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment;filename=resume_report.txt"}
    )


if __name__ == "__main__":
    app.run(debug=True)