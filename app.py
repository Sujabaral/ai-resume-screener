from flask import Flask, render_template, request, redirect, url_for
import os

from config import Config

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

    # Save uploaded file
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], resume_file.filename)
    resume_file.save(save_path)

    # For now, just pass placeholder data
    result = {
        "resume_filename": resume_file.filename,
        "job_description": job_description,
        "match_score": 0,
        "matched_skills": [],
        "missing_skills": [],
        "suggestions": ["Scoring logic will be added from Day 2 onward."]
    }

    return render_template("result.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)