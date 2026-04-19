import re

SKILL_CATEGORIES = {
    "programming": [
        "python", "java", "c++", "c#", "javascript"
    ],
    "web_development": [
        "html", "css", "django", "flask", "fastapi", "react", "node.js"
    ],
    "databases": [
        "sql", "mysql", "postgresql", "mongodb"
    ],
    "data_science": [
        "pandas", "numpy", "scikit-learn", "data analysis", "matplotlib"
    ],
    "machine_learning": [
        "machine learning", "deep learning", "nlp", "tensorflow", "pytorch", "transformers"
    ],
    "tools": [
        "git", "github", "docker", "linux"
    ],
    "soft_skills": [
        "communication", "teamwork", "problem solving", "leadership"
    ]
}

SKILL_ALIASES = {
    "js": "javascript",
    "py": "python",
    "nodejs": "node.js",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "machine-learning": "machine learning",
    "deep-learning": "deep learning",
    "natural language processing": "nlp",
    "problem-solving": "problem solving",
    "c plus plus": "c++",
    "cplusplus": "c++",
    "c sharp": "c#",
    "postgres": "postgresql"
}


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = text.replace("/", " ")
    text = text.replace(",", " ")
    text = text.replace("•", " ")
    text = text.replace("\n", " ")

    # keep +, #, . and -
    text = re.sub(r"[^a-z0-9+#.\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # replace longer aliases first
    for alias, standard in sorted(SKILL_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"
        text = re.sub(pattern, standard, text)

    return text


def build_skill_pattern(skill: str) -> str:
    escaped_skill = re.escape(skill)
    return rf"(?<!\w){escaped_skill}(?!\w)"


def extract_skills(text: str) -> list:
    if not text:
        return []

    text = normalize_text(text)
    found_skills = set()

    for category_skills in SKILL_CATEGORIES.values():
        for skill in category_skills:
            pattern = build_skill_pattern(skill)
            if re.search(pattern, text):
                found_skills.add(skill)

    return sorted(found_skills)


def extract_skills_by_category(text: str) -> dict:
    if not text:
        return {}

    text = normalize_text(text)
    categorized_skills = {}

    for category, skills in SKILL_CATEGORIES.items():
        matched = []
        for skill in skills:
            pattern = build_skill_pattern(skill)
            if re.search(pattern, text):
                matched.append(skill)

        if matched:
            categorized_skills[category] = sorted(set(matched))

    return categorized_skills