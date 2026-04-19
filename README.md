# AI Resume Screener & Job Match Scorer — Version 1.5

A Flask-based AI project that analyzes how well a resume matches a job description using structured resume parsing, skill extraction, weighted scoring, and actionable improvement suggestions.

## Overview

This project helps compare a candidate's resume against a job description and provides:

- overall match score
- skill coverage score
- matched skills
- missing skills
- category-wise skill analysis
- experience and project relevance
- resume improvement suggestions
- downloadable text report

Version 1.5 improves the project by making it more structured and closer to a real ATS-style resume analyzer.

---

## Features

### Core Features
- Upload resume in PDF format
- Paste a job description
- Extract text from resume
- Preprocess resume and job description text
- Detect resume sections such as Skills, Experience, Education, and Projects
- Extract skills from both resume and job description
- Compare resume skills with required job skills
- Show matched skills and missing skills
- Generate tailored improvement suggestions
- Download the analysis report

### Version 1.5 Enhancements
- PyMuPDF-based PDF parsing with PyPDF2 fallback
- Section-based resume parsing
- Skill normalization using aliases and synonyms
- Regex-based skill extraction
- Category-wise skill grouping
- Weighted job match scoring
- Contact information extraction
- Resume section detection
- Improved result page with score breakdown

---

## Tech Stack

- **Python**
- **Flask**
- **PyMuPDF**
- **PyPDF2**
- **scikit-learn**
- **HTML**
- **CSS**

---

## Project Structure

```bash
ai-resume-screener/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── uploads/
│   └── .gitkeep
├── static/
│   └── style.css
├── templates/
│   ├── index.html
│   └── result.html
└── utils/
    ├── __init__.py
    ├── pdf_parser.py
    ├── resume_parser.py
    ├── jd_parser.py
    ├── text_preprocessor.py
    ├── skill_extractor.py
    └── scorer.py


###How It Works
    1. Resume Upload
    The user uploads a PDF resume.
    2. Job Description Input
    The user pastes the job description into the form.
    3. Resume Parsing
    The system extracts resume text using:
    PyMuPDF for better parsing quality
    PyPDF2 as fallback if needed
    4. Text Preprocessing
    The extracted text is cleaned and normalized for better comparison.
    5. Section Detection
    The system tries to detect important resume sections such as:
    Summary
    Skills
    Experience
    Education
    Projects
    Certifications
    6. Skill Extraction
Skills are extracted from both the resume and job description using:
predefined skill categories
aliases and synonyms
regex-based matching
7. Weighted Scoring
The final score is calculated using multiple components:
50% Overall text similarity
30% Skill match score
10% Experience section relevance
10% Project section relevance
8. Suggestions and Feedback
The system identifies:
matched skills
missing skills
category-level gaps
recommendations for improvement