import re

from utils.constants import EDUCATION_KEYWORDS, RESPONSIBILITY_VERBS, SENIORITY_KEYWORDS
from utils.domain_classifier import predict_job_domain
from utils.text_preprocessor import preprocess_text, split_sentences


# ----------------------------
# SMART SKILL EXTRACTION
# ----------------------------

def extract_skills_from_sentences(sentences):
    """
    Extract skills dynamically from sentences instead of fixed keyword lists.
    Works better for marketing, HR, content, etc.
    """
    skills = set()

    patterns = [
        r"experience in ([a-zA-Z\s,/-]+)",
        r"knowledge of ([a-zA-Z\s,/-]+)",
        r"proficiency in ([a-zA-Z\s,/-]+)",
        r"skills in ([a-zA-Z\s,/-]+)",
        r"responsible for ([a-zA-Z\s,/-]+)",
        r"including ([a-zA-Z\s,/-]+)",
        r"familiarity with ([a-zA-Z\s,/-]+)",
        r"expertise in ([a-zA-Z\s,/-]+)",
    ]

    for sentence in sentences:
        s = sentence.lower()

        for pattern in patterns:
            matches = re.findall(pattern, s)
            for match in matches:
                parts = re.split(r",|and|/|;", match)
                for p in parts:
                    skill = p.strip(" .:-")
                    if 2 < len(skill) < 50:
                        skills.add(skill)

        # direct keyword fallback
        keywords = [
            "content creation", "copywriting", "editing",
            "social media", "seo", "branding",
            "digital marketing", "communication",
            "research", "teamwork", "creativity",
            "photoshop", "canva", "analytics",
            "management", "coordination", "sales",
            "customer service", "recruitment", "onboarding"
        ]

        for kw in keywords:
            if kw in s:
                skills.add(kw)

    return sorted(list(skills))


# ----------------------------
# RESPONSIBILITY EXTRACTION
# ----------------------------

def extract_responsibilities(jd_text):
    sentences = split_sentences(jd_text)
    responsibilities = []

    for sentence in sentences:
        s = sentence.lower().strip()

        if len(s.split()) < 5:
            continue

        if any(verb in s for verb in RESPONSIBILITY_VERBS):
            responsibilities.append(sentence.strip())

    return sorted(list(set(responsibilities)))[:20]


# ----------------------------
# EDUCATION
# ----------------------------

def extract_education_requirement(jd_text):
    text = preprocess_text(jd_text)

    for level, keywords in EDUCATION_KEYWORDS.items():
        if any(k in text for k in keywords):
            return level

    return "unknown"


# ----------------------------
# EXPERIENCE
# ----------------------------

def extract_experience_requirement(jd_text):
    text = preprocess_text(jd_text)

    matches = re.findall(r"(\d+)\+?\s+years", text)
    return int(matches[0]) if matches else 0


# ----------------------------
# SENIORITY
# ----------------------------

def extract_seniority_from_jd(jd_text):
    text = preprocess_text(jd_text)

    for level, keywords in SENIORITY_KEYWORDS.items():
        if any(k in text for k in keywords):
            return level

    return "entry_level"


# ----------------------------
# SOFT SKILLS
# ----------------------------

def extract_soft_skills(jd_text):
    soft_keywords = [
        "communication", "teamwork", "collaboration",
        "creativity", "adaptability", "problem solving",
        "time management", "leadership", "interpersonal"
    ]

    text = preprocess_text(jd_text)

    return [s for s in soft_keywords if s in text]


# ----------------------------
# PREFERRED SKILLS
# ----------------------------

def extract_preferred_skills(jd_text):
    markers = ["preferred", "plus", "nice to have", "good to have"]
    sentences = split_sentences(jd_text)

    preferred = []

    for s in sentences:
        if any(m in s.lower() for m in markers):
            preferred.extend(extract_skills_from_sentences([s]))

    return sorted(list(set(preferred)))


# ----------------------------
# JOB TITLE EXTRACTION
# ----------------------------

def extract_job_title(jd_text):
    lines = [line.strip() for line in jd_text.splitlines() if line.strip()]

    if not lines:
        return "Unknown Role"

    # Often the title is in the first few lines
    for line in lines[:5]:
        if 2 <= len(line.split()) <= 10:
            return line

    return lines[0]


# ----------------------------
# MAIN PARSER
# ----------------------------

def parse_job_description(jd_text):
    if not jd_text or not jd_text.strip():
        return {}

    clean_text = preprocess_text(jd_text)
    sentences = split_sentences(jd_text)

    domain_info = predict_job_domain(clean_text)

    required_skills = extract_skills_from_sentences(sentences)
    preferred_skills = extract_preferred_skills(jd_text)
    responsibilities = extract_responsibilities(jd_text)
    soft_skills = extract_soft_skills(jd_text)

    return {
        "raw_text": jd_text,
        "text": jd_text,
        "clean_text": clean_text,
        "cleaned_text": clean_text,

        "job_title": extract_job_title(jd_text),
        "summary": " ".join(sentences[:3]) if sentences else "",

        "job_domain": domain_info.get("domain", "general"),
        "domain_confidence": domain_info.get("confidence", 0.0),
        "top_domain_predictions": domain_info.get("top_predictions", []),

        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "soft_skills": soft_skills,

        "responsibilities": responsibilities,
        "qualifications": [extract_education_requirement(jd_text)],

        "education_requirement": extract_education_requirement(jd_text),
        "experience_required": extract_experience_requirement(jd_text),
        "seniority_level": extract_seniority_from_jd(jd_text),
    }