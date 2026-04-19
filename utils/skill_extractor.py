import re

SKILL_CATEGORIES = {
    "programming": [
        "python", "java", "c", "c++", "c#", "javascript"
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

# Aliases / synonyms -> standard skill form
SKILL_ALIASES = {
    "js": "javascript",
    "py": "python",
    "nodejs": "node.js",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "machine-learning": "machine learning",
    "deep-learning": "deep learning",
    "natural language processing": "nlp",
    "nlp": "nlp",
    "problem-solving": "problem solving",
    "c plus plus": "c++",
    "cplusplus": "c++",
    "c sharp": "c#",
    "postgres": "postgresql"
}


def normalize_text(text: str) -> str:
    """
    Normalize text for better skill matching.
    """
    if not text:
        return ""

    text = text.lower()

    # Normalize separators/hyphens
    text = text.replace("/", " ")
    text = text.replace(",", " ")
    text = text.replace("•", " ")
    text = text.replace("\n", " ")

    # Keep +, #, . because skills like c++, c#, node.js matter
    text = re.sub(r"[^a-z0-9+#.\s-]", " ", text)

    # Normalize multiple spaces
    text = re.sub(r"\s+", " ", text).strip()

    # Replace aliases with standard forms
    for alias, standard in SKILL_ALIASES.items():
        pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"
        text = re.sub(pattern, standard, text)

    return text


def build_skill_pattern(skill: str) -> str:
    """
    Build safe regex pattern for a skill.
    """
    escaped_skill = re.escape(skill)

    # Use custom handling for skills containing special chars like c++, c#, node.js
    return rf"(?<!\w){escaped_skill}(?!\w)"


def extract_skills(text: str) -> list:
    """
    Extract all skills found in text from predefined categories.

    Args:
        text (str): Cleaned resume or job description text

    Returns:
        list: Sorted list of unique detected skills
    """
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
    """
    Extract skills grouped by category.

    Args:
        text (str): Cleaned resume or job description text

    Returns:
        dict: category -> list of detected skills
    """
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