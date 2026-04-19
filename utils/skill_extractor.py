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


def extract_skills(text):
    """
    Extract all skills found in text from predefined categories.

    Args:
        text (str): Cleaned resume or job description text

    Returns:
        list: Sorted list of unique detected skills
    """
    if not text:
        return []

    text = text.lower()
    found_skills = set()

    for category_skills in SKILL_CATEGORIES.values():
        for skill in category_skills:
            if skill in text:
                found_skills.add(skill)

    return sorted(found_skills)


def extract_skills_by_category(text):
    """
    Extract skills grouped by category.

    Args:
        text (str): Cleaned resume or job description text

    Returns:
        dict: category -> list of detected skills
    """
    if not text:
        return {}

    text = text.lower()
    categorized_skills = {}

    for category, skills in SKILL_CATEGORIES.items():
        matched = [skill for skill in skills if skill in text]
        if matched:
            categorized_skills[category] = sorted(matched)

    return categorized_skills