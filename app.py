from flask import Flask, render_template, request
import os

from config import Config
from utils.pdf_parser import extract_text_from_pdf
from utils.text_preprocessor import clean_text

app = Flask(__name__)
app.config.from_object(Config)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "resume" not in request.files:
        return "No resume file uploaded."

    resume_file = request.files["resume"]
    job_description = request.form.get("job_description", "")

    if resume_file.filename == "":
        return "No selected file."

    if not job_description.strip():
        return "Job description is required."

    save_path = os.path.join(app.config["UPLOAD_FOLDER"], resume_file.filename)
    resume_file.save(save_path)

    # Extract raw resume text
    raw_resume_text = extract_text_from_pdf(save_path)

    # Clean both resume and job description
    cleaned_resume_text = clean_text(raw_resume_text)
    cleaned_job_description = clean_text(job_description)

    result = {
        "resume_filename": resume_file.filename,
        "match_score": 0,
        "matched_skills": [],
        "missing_skills": [],
        "suggestions": ["Text extracted successfully. Scoring will be added on Day 3."],
        "resume_preview": cleaned_resume_text[:1000],
        "job_description_preview": cleaned_job_description[:1000]
    }

    return render_template("result.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)