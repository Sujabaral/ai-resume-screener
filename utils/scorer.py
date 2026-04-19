from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_match_score(resume_text, job_description_text):
    """
    Calculate overall similarity score using TF-IDF and cosine similarity.
    """
    if not resume_text or not job_description_text:
        return 0

    documents = [resume_text, job_description_text]

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(documents)

    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

    return round(similarity * 100)


def calculate_skill_coverage(resume_skills, jd_skills):
    """
    Calculate how many job description skills are covered by the resume.

    Args:
        resume_skills (list): Skills found in resume
        jd_skills (list): Skills found in job description

    Returns:
        int: Skill coverage percentage
    """
    if not jd_skills:
        return 0

    matched = set(resume_skills) & set(jd_skills)
    coverage = (len(matched) / len(set(jd_skills))) * 100

    return round(coverage)