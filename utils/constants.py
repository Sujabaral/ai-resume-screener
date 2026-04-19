# utils/constants.py

"""
Central constants for the AI Resume Screener v2.0

This file stores:
- universal skill categories
- domain keywords for job classification
- seniority keywords
- education keywords
- scoring weights
"""

SKILL_CATEGORIES = {
    "technical": [
        "python", "java", "c", "c++", "c#", "sql", "mysql", "postgresql",
        "html", "css", "javascript", "typescript", "react", "angular",
        "node.js", "flask", "django", "fastapi", "git", "github", "api",
        "rest api", "machine learning", "deep learning", "data analysis",
        "data visualization", "pandas", "numpy", "scikit-learn", "tensorflow",
        "pytorch", "power bi", "tableau", "excel", "cloud", "aws", "azure",
        "docker", "kubernetes", "linux", "testing", "automation testing",
        "manual testing", "ui/ux", "figma"
    ],
    "business": [
        "reporting", "documentation", "data entry", "analysis", "coordination",
        "administration", "presentation", "project management", "planning",
        "scheduling", "record keeping", "operations", "stakeholder management",
        "client communication", "proposal writing", "business development"
    ],
    "marketing": [
        "seo", "sem", "social media", "content writing", "copywriting",
        "campaign management", "branding", "market research", "email marketing",
        "digital marketing", "advertising", "content strategy", "analytics"
    ],
    "sales": [
        "lead generation", "negotiation", "crm", "client relationship",
        "sales target", "upselling", "cold calling", "customer acquisition",
        "closing sales", "pipeline management", "sales reporting"
    ],
    "finance": [
        "accounting", "bookkeeping", "financial reporting", "budgeting",
        "auditing", "taxation", "invoice processing", "payroll", "tally",
        "quickbooks", "reconciliation", "accounts payable", "accounts receivable",
        "financial analysis", "cost control"
    ],
    "healthcare": [
        "patient care", "clinical documentation", "medication administration",
        "vital signs", "care planning", "medical terminology", "nursing care",
        "health assessment", "infection control", "patient education",
        "emergency response", "clinical support"
    ],
    "education": [
        "lesson planning", "classroom management", "curriculum development",
        "student assessment", "teaching", "mentoring", "tutoring",
        "instructional design", "academic support", "training delivery"
    ],
    "hr": [
        "recruitment", "onboarding", "employee engagement", "performance management",
        "interviewing", "talent acquisition", "attendance management",
        "hr administration", "employee relations", "policy compliance",
        "training coordination"
    ],
    "operations": [
        "inventory management", "scheduling", "logistics", "quality control",
        "vendor management", "compliance", "supply chain", "procurement",
        "warehouse operations", "process improvement", "dispatch", "coordination"
    ],
    "customer_support": [
        "customer service", "client support", "issue resolution", "ticket handling",
        "call handling", "email support", "chat support", "complaint handling",
        "customer communication", "service delivery"
    ],
    "soft_skills": [
        "communication", "teamwork", "leadership", "problem solving",
        "time management", "adaptability", "attention to detail",
        "critical thinking", "interpersonal skills", "collaboration",
        "organization", "creativity", "decision making", "responsibility",
        "work ethic"
    ]
}

DOMAIN_KEYWORDS = {
    "technology": [
        "software", "developer", "engineer", "programming", "python", "java",
        "web development", "backend", "frontend", "database", "api", "cloud",
        "machine learning", "data science", "testing", "devops", "it support"
    ],
    "marketing": [
        "marketing", "seo", "campaign", "branding", "content", "social media",
        "digital marketing", "promotion", "advertising", "market research"
    ],
    "sales": [
        "sales", "lead generation", "target", "crm", "business development",
        "customer acquisition", "revenue", "client relationship"
    ],
    "finance": [
        "accounting", "finance", "bookkeeping", "audit", "budget",
        "financial reporting", "payroll", "tax", "invoice"
    ],
    "hr": [
        "human resources", "hr", "recruitment", "onboarding", "employee",
        "talent acquisition", "performance management", "payroll"
    ],
    "education": [
        "teacher", "teaching", "student", "curriculum", "lesson planning",
        "education", "training", "classroom"
    ],
    "healthcare": [
        "nurse", "patient", "clinical", "hospital", "medical", "healthcare",
        "care", "treatment", "medication"
    ],
    "operations": [
        "operations", "inventory", "logistics", "vendor", "supply chain",
        "procurement", "scheduling", "process improvement"
    ],
    "customer_support": [
        "customer support", "customer service", "client support", "call center",
        "ticket", "complaint resolution", "chat support", "service desk"
    ],
    "general": []
}

SENIORITY_KEYWORDS = {
    "entry_level": [
        "fresher", "entry level", "junior", "assistant", "trainee", "internship",
        "intern", "associate", "graduate"
    ],
    "mid_level": [
        "mid level", "executive", "specialist", "officer", "coordinator",
        "analyst", "experienced"
    ],
    "senior_level": [
        "senior", "lead", "manager", "head", "supervisor", "principal",
        "director"
    ]
}

EDUCATION_KEYWORDS = {
    "high_school": [
        "high school", "secondary school", "see", "slc", "+2", "intermediate"
    ],
    "diploma": [
        "diploma"
    ],
    "bachelor": [
        "bachelor", "b.e.", "be", "bsc", "b.sc", "bba", "bca", "bachelor's"
    ],
    "master": [
        "master", "mba", "msc", "m.sc", "m.e.", "me", "master's"
    ],
    "phd": [
        "phd", "doctorate"
    ]
}

SECTION_HEADERS = {
    "summary": [
        "summary", "professional summary", "profile", "career objective",
        "objective", "about me"
    ],
    "skills": [
        "skills", "technical skills", "core skills", "competencies",
        "expertise", "key skills"
    ],
    "experience": [
        "experience", "work experience", "employment history",
        "professional experience", "internship", "projects"
    ],
    "education": [
        "education", "academic background", "qualification", "academic qualification"
    ],
    "certifications": [
        "certifications", "licenses", "training", "courses"
    ],
    "projects": [
        "projects", "academic projects", "personal projects"
    ]
}

RESPONSIBILITY_VERBS = [
    "managed", "led", "developed", "created", "designed", "implemented",
    "handled", "supported", "coordinated", "organized", "analyzed",
    "maintained", "delivered", "trained", "monitored", "improved",
    "executed", "prepared", "presented", "communicated", "assisted",
    "supervised", "planned", "performed", "resolved", "negotiated"
]

DEFAULT_SCORING_WEIGHTS = {
    "semantic_score": 0.30,
    "skill_match_score": 0.25,
    "responsibility_score": 0.20,
    "experience_score": 0.15,
    "education_score": 0.05,
    "keyword_alignment_score": 0.05
}

DOMAIN_WEIGHT_OVERRIDES = {
    "technology": {
        "semantic_score": 0.28,
        "skill_match_score": 0.30,
        "responsibility_score": 0.18,
        "experience_score": 0.14,
        "education_score": 0.05,
        "keyword_alignment_score": 0.05
    },
    "sales": {
        "semantic_score": 0.28,
        "skill_match_score": 0.22,
        "responsibility_score": 0.22,
        "experience_score": 0.16,
        "education_score": 0.04,
        "keyword_alignment_score": 0.08
    },
    "marketing": {
        "semantic_score": 0.30,
        "skill_match_score": 0.22,
        "responsibility_score": 0.20,
        "experience_score": 0.14,
        "education_score": 0.04,
        "keyword_alignment_score": 0.10
    },
    "finance": {
        "semantic_score": 0.27,
        "skill_match_score": 0.28,
        "responsibility_score": 0.20,
        "experience_score": 0.16,
        "education_score": 0.05,
        "keyword_alignment_score": 0.04
    },
    "hr": {
        "semantic_score": 0.29,
        "skill_match_score": 0.22,
        "responsibility_score": 0.22,
        "experience_score": 0.16,
        "education_score": 0.05,
        "keyword_alignment_score": 0.06
    },
    "education": {
        "semantic_score": 0.29,
        "skill_match_score": 0.22,
        "responsibility_score": 0.22,
        "experience_score": 0.16,
        "education_score": 0.06,
        "keyword_alignment_score": 0.05
    },
    "healthcare": {
        "semantic_score": 0.28,
        "skill_match_score": 0.24,
        "responsibility_score": 0.22,
        "experience_score": 0.16,
        "education_score": 0.06,
        "keyword_alignment_score": 0.04
    },
    "operations": {
        "semantic_score": 0.28,
        "skill_match_score": 0.24,
        "responsibility_score": 0.22,
        "experience_score": 0.17,
        "education_score": 0.05,
        "keyword_alignment_score": 0.04
    },
    "customer_support": {
        "semantic_score": 0.29,
        "skill_match_score": 0.22,
        "responsibility_score": 0.23,
        "experience_score": 0.15,
        "education_score": 0.04,
        "keyword_alignment_score": 0.07
    }
}