ROLE_PROFILES = {
    "software_engineer": {
        "keywords": [
            "software engineer", "software developer", "developer", "programmer", "application developer"
        ],
        "weights": {
            "overall": 0.25,
            "skills": 0.30,
            "experience": 0.15,
            "projects": 0.15,
            "responsibilities": 0.10,
            "education": 0.05
        },
        "required_skills": [
            "python", "java", "c++", "git", "sql", "data structures", "algorithms"
        ],
        "preferred_skills": [
            "django", "flask", "fastapi", "rest api", "github", "linux", "problem solving"
        ],
        "soft_skills": [
            "teamwork", "communication", "analytical thinking", "problem solving"
        ],
        "education_keywords": [
            "computer engineering", "computer science", "software engineering", "information technology"
        ]
    },

    "backend_developer": {
        "keywords": [
            "backend developer", "backend engineer", "server-side developer", "api developer"
        ],
        "weights": {
            "overall": 0.25,
            "skills": 0.35,
            "experience": 0.15,
            "projects": 0.10,
            "responsibilities": 0.10,
            "education": 0.05
        },
        "required_skills": [
            "python", "sql", "flask", "api", "git"
        ],
        "preferred_skills": [
            "fastapi", "django", "postgresql", "docker", "linux", "rest api"
        ],
        "soft_skills": [
            "problem solving", "teamwork", "communication"
        ],
        "education_keywords": [
            "computer engineering", "computer science", "information technology"
        ]
    },

    "frontend_developer": {
        "keywords": [
            "frontend developer", "front-end developer", "ui developer", "web developer"
        ],
        "weights": {
            "overall": 0.20,
            "skills": 0.35,
            "experience": 0.10,
            "projects": 0.20,
            "responsibilities": 0.10,
            "education": 0.05
        },
        "required_skills": [
            "html", "css", "javascript"
        ],
        "preferred_skills": [
            "react", "bootstrap", "responsive design", "github", "git", "ui"
        ],
        "soft_skills": [
            "creativity", "communication", "teamwork", "attention to detail"
        ],
        "education_keywords": [
            "computer engineering", "computer science", "information technology"
        ]
    },

    "full_stack_developer": {
        "keywords": [
            "full stack developer", "full-stack developer", "web application developer"
        ],
        "weights": {
            "overall": 0.20,
            "skills": 0.35,
            "experience": 0.15,
            "projects": 0.15,
            "responsibilities": 0.10,
            "education": 0.05
        },
        "required_skills": [
            "html", "css", "javascript", "python", "sql", "git"
        ],
        "preferred_skills": [
            "react", "flask", "django", "rest api", "postgresql", "github"
        ],
        "soft_skills": [
            "problem solving", "teamwork", "communication", "adaptability"
        ],
        "education_keywords": [
            "computer engineering", "computer science", "information technology"
        ]
    },

    "data_analyst": {
        "keywords": [
            "data analyst", "business data analyst", "reporting analyst", "analytics associate"
        ],
        "weights": {
            "overall": 0.20,
            "skills": 0.35,
            "experience": 0.15,
            "projects": 0.10,
            "responsibilities": 0.15,
            "education": 0.05
        },
        "required_skills": [
            "python", "sql", "excel", "data analysis", "reporting"
        ],
        "preferred_skills": [
            "pandas", "numpy", "matplotlib", "power bi", "tableau", "statistics"
        ],
        "soft_skills": [
            "analytical thinking", "attention to detail", "communication", "problem solving"
        ],
        "education_keywords": [
            "computer engineering", "computer science", "statistics", "mathematics", "information technology", "business analytics"
        ]
    },

    "business_analyst": {
        "keywords": [
            "business analyst", "process analyst", "requirements analyst", "operations analyst"
        ],
        "weights": {
            "overall": 0.20,
            "skills": 0.30,
            "experience": 0.20,
            "projects": 0.10,
            "responsibilities": 0.15,
            "education": 0.05
        },
        "required_skills": [
            "requirements gathering", "documentation", "analysis", "reporting", "communication"
        ],
        "preferred_skills": [
            "excel", "sql", "power bi", "stakeholder management", "process improvement"
        ],
        "soft_skills": [
            "communication", "analytical thinking", "problem solving", "teamwork"
        ],
        "education_keywords": [
            "business", "management", "computer engineering", "information technology", "business analytics"
        ]
    },

    "ml_engineer": {
        "keywords": [
            "ml engineer", "machine learning engineer", "ai engineer", "artificial intelligence engineer"
        ],
        "weights": {
            "overall": 0.20,
            "skills": 0.40,
            "experience": 0.10,
            "projects": 0.15,
            "responsibilities": 0.10,
            "education": 0.05
        },
        "required_skills": [
            "python", "machine learning", "scikit-learn"
        ],
        "preferred_skills": [
            "tensorflow", "pytorch", "nlp", "transformers", "deep learning", "data preprocessing"
        ],
        "soft_skills": [
            "problem solving", "analytical thinking", "research", "communication"
        ],
        "education_keywords": [
            "computer engineering", "computer science", "artificial intelligence", "data science"
        ]
    },

    "qa_engineer": {
        "keywords": [
            "qa engineer", "quality assurance engineer", "software tester", "qa analyst", "test engineer"
        ],
        "weights": {
            "overall": 0.20,
            "skills": 0.30,
            "experience": 0.20,
            "projects": 0.10,
            "responsibilities": 0.15,
            "education": 0.05
        },
        "required_skills": [
            "testing", "bug reporting", "test cases", "quality assurance"
        ],
        "preferred_skills": [
            "manual testing", "selenium", "jira", "documentation", "regression testing"
        ],
        "soft_skills": [
            "attention to detail", "communication", "problem solving", "teamwork"
        ],
        "education_keywords": [
            "computer engineering", "computer science", "information technology"
        ]
    },

    "project_manager": {
        "keywords": [
            "project manager", "project coordinator", "program coordinator", "project officer"
        ],
        "weights": {
            "overall": 0.20,
            "skills": 0.25,
            "experience": 0.25,
            "projects": 0.10,
            "responsibilities": 0.15,
            "education": 0.05
        },
        "required_skills": [
            "project management", "coordination", "documentation", "planning", "communication"
        ],
        "preferred_skills": [
            "reporting", "stakeholder management", "time management", "leadership", "risk management"
        ],
        "soft_skills": [
            "leadership", "communication", "organization", "teamwork", "problem solving"
        ],
        "education_keywords": [
            "management", "business", "computer engineering", "information technology"
        ]
    },

    "hr": {
        "keywords": [
            "hr", "human resources", "hr assistant", "recruitment assistant", "talent acquisition"
        ],
        "weights": {
            "overall": 0.20,
            "skills": 0.25,
            "experience": 0.20,
            "projects": 0.05,
            "responsibilities": 0.20,
            "education": 0.10
        },
        "required_skills": [
            "communication", "recruitment", "documentation", "coordination", "interpersonal skills"
        ],
        "preferred_skills": [
            "onboarding", "employee relations", "record keeping", "ms office", "scheduling"
        ],
        "soft_skills": [
            "communication", "empathy", "organization", "confidentiality", "teamwork"
        ],
        "education_keywords": [
            "human resources", "business", "management", "psychology"
        ]
    },

    "marketing": {
        "keywords": [
            "marketing", "marketing executive", "digital marketing", "brand executive", "marketing officer"
        ],
        "weights": {
            "overall": 0.20,
            "skills": 0.30,
            "experience": 0.15,
            "projects": 0.15,
            "responsibilities": 0.15,
            "education": 0.05
        },
        "required_skills": [
            "marketing", "communication", "content creation", "campaign", "branding"
        ],
        "preferred_skills": [
            "social media", "seo", "analytics", "copywriting", "market research"
        ],
        "soft_skills": [
            "creativity", "communication", "teamwork", "adaptability"
        ],
        "education_keywords": [
            "marketing", "business", "management", "mass communication"
        ]
    },

    "sales": {
        "keywords": [
            "sales", "sales executive", "sales officer", "business development", "account executive"
        ],
        "weights": {
            "overall": 0.20,
            "skills": 0.25,
            "experience": 0.20,
            "projects": 0.05,
            "responsibilities": 0.20,
            "education": 0.10
        },
        "required_skills": [
            "sales", "communication", "customer handling", "negotiation", "relationship management"
        ],
        "preferred_skills": [
            "lead generation", "crm", "presentation", "reporting", "business development"
        ],
        "soft_skills": [
            "communication", "persuasion", "confidence", "teamwork", "time management"
        ],
        "education_keywords": [
            "business", "management", "marketing", "commerce"
        ]
    },

    "customer_support": {
        "keywords": [
            "customer support", "customer service", "support representative", "call center", "help desk"
        ],
        "weights": {
            "overall": 0.20,
            "skills": 0.25,
            "experience": 0.20,
            "projects": 0.05,
            "responsibilities": 0.20,
            "education": 0.10
        },
        "required_skills": [
            "communication", "customer service", "problem solving", "issue resolution"
        ],
        "preferred_skills": [
            "call handling", "email support", "crm", "documentation", "time management"
        ],
        "soft_skills": [
            "patience", "communication", "empathy", "problem solving", "adaptability"
        ],
        "education_keywords": [
            "business", "management", "computer engineering", "information technology", "arts"
        ]
    },

    "content_writer": {
        "keywords": [
            "content writer", "copywriter", "article writer", "seo writer", "content creator"
        ],
        "weights": {
            "overall": 0.20,
            "skills": 0.30,
            "experience": 0.15,
            "projects": 0.15,
            "responsibilities": 0.15,
            "education": 0.05
        },
        "required_skills": [
            "writing", "content creation", "grammar", "communication", "research"
        ],
        "preferred_skills": [
            "seo", "copywriting", "editing", "blog writing", "social media"
        ],
        "soft_skills": [
            "creativity", "attention to detail", "communication", "research"
        ],
        "education_keywords": [
            "journalism", "english", "mass communication", "marketing", "business"
        ]
    },

    "teacher": {
        "keywords": [
            "teacher", "instructor", "lecturer", "educator", "teaching assistant"
        ],
        "weights": {
            "overall": 0.20,
            "skills": 0.25,
            "experience": 0.20,
            "projects": 0.05,
            "responsibilities": 0.20,
            "education": 0.10
        },
        "required_skills": [
            "teaching", "communication", "lesson planning", "classroom management"
        ],
        "preferred_skills": [
            "student assessment", "curriculum design", "presentation", "mentoring"
        ],
        "soft_skills": [
            "communication", "patience", "leadership", "organization", "empathy"
        ],
        "education_keywords": [
            "education", "english", "mathematics", "science", "computer science"
        ]
    },

    "accountant": {
        "keywords": [
            "accountant", "accounts officer", "finance assistant", "bookkeeper", "accounts executive"
        ],
        "weights": {
            "overall": 0.20,
            "skills": 0.30,
            "experience": 0.20,
            "projects": 0.05,
            "responsibilities": 0.20,
            "education": 0.05
        },
        "required_skills": [
            "accounting", "bookkeeping", "excel", "financial reporting", "attention to detail"
        ],
        "preferred_skills": [
            "tally", "quickbooks", "tax", "reconciliation", "auditing"
        ],
        "soft_skills": [
            "attention to detail", "analytical thinking", "integrity", "organization"
        ],
        "education_keywords": [
            "accounting", "finance", "commerce", "business"
        ]
    },

    "graphic_designer": {
        "keywords": [
            "graphic designer", "visual designer", "creative designer", "brand designer"
        ],
        "weights": {
            "overall": 0.20,
            "skills": 0.30,
            "experience": 0.10,
            "projects": 0.20,
            "responsibilities": 0.15,
            "education": 0.05
        },
        "required_skills": [
            "design", "creativity", "visual communication", "branding"
        ],
        "preferred_skills": [
            "photoshop", "illustrator", "figma", "canva", "ui design"
        ],
        "soft_skills": [
            "creativity", "communication", "attention to detail", "time management"
        ],
        "education_keywords": [
            "design", "fine arts", "multimedia", "visual communication"
        ]
    },

    "general": {
        "keywords": [],
        "weights": {
            "overall": 0.25,
            "skills": 0.25,
            "experience": 0.15,
            "projects": 0.10,
            "responsibilities": 0.15,
            "education": 0.10
        },
        "required_skills": [],
        "preferred_skills": [],
        "soft_skills": [
            "communication", "teamwork", "problem solving", "adaptability", "time management"
        ],
        "education_keywords": []
    }
}