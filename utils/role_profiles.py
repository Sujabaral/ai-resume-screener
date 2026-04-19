ROLE_PROFILES = {
    "backend": {
        "weights": {
            "overall": 0.35,
            "skills": 0.40,
            "experience": 0.15,
            "projects": 0.10
        },
        "required_skills": [
            "python", "flask", "sql", "git"
        ],
        "preferred_skills": [
            "docker", "postgresql", "fastapi", "linux"
        ]
    },
    "frontend": {
        "weights": {
            "overall": 0.30,
            "skills": 0.40,
            "experience": 0.10,
            "projects": 0.20
        },
        "required_skills": [
            "html", "css", "javascript"
        ],
        "preferred_skills": [
            "react", "git", "github"
        ]
    },
    "data_analyst": {
        "weights": {
            "overall": 0.30,
            "skills": 0.40,
            "experience": 0.15,
            "projects": 0.15
        },
        "required_skills": [
            "python", "sql", "pandas", "data analysis"
        ],
        "preferred_skills": [
            "matplotlib", "numpy", "postgresql"
        ]
    },
    "ml_engineer": {
        "weights": {
            "overall": 0.30,
            "skills": 0.45,
            "experience": 0.10,
            "projects": 0.15
        },
        "required_skills": [
            "python", "machine learning", "scikit-learn"
        ],
        "preferred_skills": [
            "tensorflow", "pytorch", "nlp", "transformers"
        ]
    }
}