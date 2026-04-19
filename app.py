from flask import Flask, render_template, request, Response
import os
from werkzeug.utils import secure_filename
from utils.role_profiles import ROLE_PROFILES
from utils.insight_engine import generate_resume_insights
from utils.report_generator import build_report_text as build_v2_report
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


def generate_strengths(final_score, skill_score, matched_skills, resume_categories):
    strengths = []

    if final_score >= 70:
        strengths.append("The resume has strong overall similarity with the job description.")

    if skill_score >= 70:
        strengths.append("A good portion of the required skills are present in the resume.")

    if len(matched_skills) >= 5:
        strengths.append("Multiple relevant skills were matched successfully.")

    if "programming" in resume_categories:
        strengths.append("Programming skills are clearly visible in the resume.")

    if "tools" in resume_categories:
        strengths.append("The resume includes useful development tools and workflow knowledge.")

    if not strengths:
        strengths.append("The resume shows some relevant background, but needs stronger alignment.")

    return strengths


def generate_suggestions(final_score, skill_score, missing_skills, resume_categories, jd_categories):
    suggestions = []

    if final_score >= 75:
        suggestions.append("Strong overall match with the job description.")
    elif final_score >= 50:
        suggestions.append("Moderate overall match. The resume can be tailored further.")
    else:
        suggestions.append("Low overall match. Consider tailoring your resume significantly.")

    if skill_score >= 75:
        suggestions.append("Good coverage of required skills.")
    elif skill_score >= 50:
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


def generate_ai_explanation(result):
    score = result["match_score"]
    matched = len(result["matched_skills"])
    missing = len(result["missing_skills"])
    similarity = result["overall_similarity"]
    experience = result["experience_score"]
    projects = result["project_score"]

    if score >= 80:
        level = "This resume is a strong fit for the role."
    elif score >= 65:
        level = "This resume is a good match, with a few areas to strengthen."
    elif score >= 50:
        level = "This resume shows partial alignment with the role."
    elif score >= 35:
        level = "This resume has limited alignment with the job description."
    else:
        level = "This resume is currently a weak match for the role."

    explanation = (
        f"{level} It matched {matched} required skill(s) and missed {missing} key skill(s). "
        f"The textual similarity score was {similarity}%, suggesting "
    )

    if similarity >= 60:
        explanation += "the wording and content align very well with the job description. "
    elif similarity >= 35:
        explanation += "moderate alignment in wording and content. "
    else:
        explanation += "low alignment in wording and phrasing. "

    if experience > 0:
        explanation += f"Relevant experience signals contributed {experience}% to the score. "
    else:
        explanation += "No strong experience evidence was detected. "

    if projects > 0:
        explanation += f"Project relevance added {projects}% to the evaluation."
    else:
        explanation += "Projects did not significantly strengthen the match."

    return explanation


def generate_badges(result, all_results):
    badges = []

    if result["rank"] == 1:
        badges.append("Top Overall Match")

    max_skill = max(r["skill_coverage"] for r in all_results)
    max_similarity = max(r["overall_similarity"] for r in all_results)
    max_experience = max(r["experience_score"] for r in all_results)
    max_project = max(r["project_score"] for r in all_results)

    if result["skill_coverage"] == max_skill and max_skill > 0:
        badges.append("Best Skill Coverage")

    if result["overall_similarity"] == max_similarity and max_similarity > 0:
        badges.append("Best Similarity Match")

    if result["experience_score"] == max_experience and max_experience > 0:
        badges.append("Best Experience Signal")

    if result["project_score"] == max_project and max_project > 0:
        badges.append("Best Project Relevance")

    if result["match_score"] >= 80:
        badges.append("Excellent Fit")
    elif result["match_score"] >= 65:
        badges.append("Strong Candidate")
    elif result["match_score"] >= 50:
        badges.append("Moderate Candidate")

    return badges


def build_weighted_breakdown(scores):
    return {
        "skill": scores["weighted_skill_score"],
        "similarity": scores["overall_similarity"],
        "experience": scores["experience_score"],
        "projects": scores["project_score"],
    }


def build_report_text(result):
    report_lines = [
        "AI Resume Screener & Job Match Report",
        "=" * 45,
        f"Resume File: {result['resume_filename']}",
        f"Final Match Score: {result['match_score']}%",
        f"Match Label: {result['match_label']}",
        f"Skill Coverage: {result['skill_coverage']}%",
        f"Overall Similarity: {result['overall_similarity']}%",
        f"Experience Score: {result['experience_score']}%",
        f"Project Score: {result['project_score']}%",
        "",
        "Matched Skills:",
        ", ".join(result["matched_skills"]) if result["matched_skills"] else "None",
        "",
        "Missing Skills:",
        ", ".join(result["missing_skills"]) if result["missing_skills"] else "None",
        "",
        "Strengths:"
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
    report_lines.append("Contact Info:")

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

    resume_files = request.files.getlist("resumes")
    job_description = request.form.get("job_description", "").strip()
    selected_role = request.form.get("role", "").strip()

    print("REQUEST.FILES:", request.files)
    print("RESUME FILES:", resume_files)
    print("JOB DESCRIPTION LENGTH:", len(job_description))

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
            print(f"Skipped invalid file type: {resume_file.filename}")
            continue

        filename = secure_filename(resume_file.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        try:
            resume_file.save(save_path)

            resume_data = build_resume_data(save_path)
            scores = calculate_final_score(resume_data, jd_data, selected_role)

            resume_skills = resume_data["skills"]
            jd_skills = jd_data["skills"]

            matched_skills = sorted(set(resume_skills) & set(jd_skills))
            missing_skills = sorted(set(jd_skills) - set(resume_skills))

            resume_categories = extract_skills_by_category(resume_data["cleaned_text"])
            jd_categories = extract_skills_by_category(jd_data["cleaned_text"])

            strengths = generate_strengths(
                scores["final_score"],
                scores["weighted_skill_score"],
                matched_skills,
                resume_categories
            )

            suggestions = generate_suggestions(
                scores["final_score"],
                scores["weighted_skill_score"],
                missing_skills,
                resume_categories,
                jd_categories
            )

            suggestions.extend(generate_category_feedback(resume_categories, jd_categories))

            insights = generate_resume_insights(resume_data, jd_data)

            result = {
                "resume_filename": filename,
                "role_used": scores["role_used"],
                "match_score": scores["final_score"],
                "match_label": score_label(scores["final_score"]),
                "skill_coverage": scores["weighted_skill_score"],
                "overall_similarity": scores["overall_similarity"],
                "experience_score": scores["experience_score"],
                "project_score": scores["project_score"],
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "strengths": strengths,
                "suggestions": suggestions,
                "insights": insights,
                "resume_preview": resume_data["cleaned_text"][:1000],
                "job_description_preview": job_description[:1000],
                "resume_categories": resume_categories,
                "jd_categories": jd_categories,
                "contact_info": resume_data["contact"],
                "resume_sections": resume_data["sections"],
                "weighted_breakdown": build_weighted_breakdown(scores)
            }

            results.append(result)

        except Exception as e:
            print(f"Error processing {resume_file.filename}: {e}")
            continue

    if not results:
        return "No valid PDF files processed."

    # FIXED RANKING
    results = sorted(
        results,
        key=lambda x: (
            x["match_score"],
            x["skill_coverage"],
            x["overall_similarity"]
        ),
        reverse=True
    )

    for i, result in enumerate(results, start=1):
        result["rank"] = i

    ranked_results = results
    latest_result = ranked_results

    # ADD BADGES + AI EXPLANATION
    for result in ranked_results:
        result["badges"] = generate_badges(result, ranked_results)
        result["ai_explanation"] = generate_ai_explanation(result)

    # TOP SUMMARY
    top_result = ranked_results[0]

    top_summary = {
        "resume_filename": top_result["resume_filename"],
        "match_score": top_result["match_score"],
        "match_label": top_result["match_label"],
        "role_used": top_result["role_used"],
        "matched_count": len(top_result["matched_skills"]),
        "missing_count": len(top_result["missing_skills"]),
        "why_top": []
    }

    if top_result["skill_coverage"] >= 70:
        top_summary["why_top"].append("High skill coverage compared to other resumes.")

    if len(top_result["matched_skills"]) >= 2:
        top_summary["why_top"].append("Matched more relevant job skills.")

    if top_result["overall_similarity"] >= 20:
        top_summary["why_top"].append("Better textual similarity to the job description.")

    if top_result["experience_score"] > 0:
        top_summary["why_top"].append("Some relevant experience detected.")

    if top_result["project_score"] > 0:
        top_summary["why_top"].append("Projects show partial relevance.")

    if not top_summary["why_top"]:
        top_summary["why_top"].append(
            "Ranked highest among uploaded resumes, but overall match is still low."
        )

    # BAR CHART DATA
    comparison_chart = {
        "labels": [r["resume_filename"] for r in ranked_results],
        "match_scores": [r["match_score"] for r in ranked_results],
        "skill_scores": [r["skill_coverage"] for r in ranked_results],
        "similarity_scores": [r["overall_similarity"] for r in ranked_results],
    }

    # RADAR CHART DATA
    radar_chart = {
        "labels": ["Skill Coverage", "Similarity", "Experience", "Projects"],
        "datasets": [
            {
                "label": r["resume_filename"],
                "data": [
                    r["skill_coverage"],
                    r["overall_similarity"],
                    r["experience_score"],
                    r["project_score"]
                ]
            }
            for r in ranked_results[:3]
        ]
    }

    return render_template(
        "ranking.html",
        results=ranked_results,
        top_summary=top_summary,
        comparison_chart=comparison_chart,
        radar_chart=radar_chart
    )


@app.route("/download-report")
def download_report():
    global latest_result

    if not latest_result:
        return "No report available yet. Please analyze a resume first."

    report_text = build_v2_report(latest_result[0])
    return Response(
        report_text,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=resume_report.txt"}
    )


if __name__ == "__main__":
    app.run(debug=True)