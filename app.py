from flask import Flask, render_template, request, jsonify
import fitz  # pymupdf
import docx
import re
import os

app = Flask(__name__)

# ── Skills Database ───────────────────────────────
SKILLS = {
    "Programming Languages": [
        "python", "java", "javascript", "c++", "c#", "php", "ruby",
        "swift", "kotlin", "typescript", "r", "matlab", "scala", "go"
    ],
    "Web Technologies": [
        "html", "css", "react", "angular", "vue", "node", "django",
        "flask", "bootstrap", "jquery", "rest", "api", "graphql"
    ],
    "Databases": [
        "sql", "mysql", "postgresql", "mongodb", "firebase", "oracle",
        "sqlite", "redis", "elasticsearch"
    ],
    "Data Science & AI": [
        "machine learning", "deep learning", "tensorflow", "pytorch",
        "keras", "scikit", "pandas", "numpy", "opencv", "nlp",
        "computer vision", "data analysis", "tableau", "power bi"
    ],
    "Cloud & DevOps": [
        "aws", "azure", "google cloud", "docker", "kubernetes",
        "git", "github", "linux", "jenkins", "ci/cd"
    ],
    "Soft Skills": [
        "leadership", "communication", "teamwork", "problem solving",
        "management", "analytical", "creative", "detail oriented"
    ]
}

KEYWORDS = {
    "education": ["bachelor", "master", "phd", "degree", "university",
                  "college", "graduated", "cgpa", "gpa", "b.s", "m.s", "bsc", "msc"],
    "experience": ["experience", "worked", "developed", "managed", "led",
                   "created", "built", "designed", "implemented", "intern"],
    "certifications": ["certified", "certification", "certificate", "aws certified",
                       "google certified", "microsoft certified", "coursera", "udemy"]
}

# ── Extract Text ──────────────────────────────────
def extract_text(file):
    filename = file.filename.lower()
    if filename.endswith(".pdf"):
        data = file.read()
        doc  = fitz.open(stream=data, filetype="pdf")
        return " ".join(page.get_text() for page in doc)
    elif filename.endswith(".docx"):
        data = file.read()
        import io
        doc  = docx.Document(io.BytesIO(data))
        return " ".join(p.text for p in doc.paragraphs)
    elif filename.endswith(".txt"):
        return file.read().decode("utf-8", errors="ignore")
    return ""

# ── Analyze Resume ────────────────────────────────
def analyze_resume(text):
    text_lower = text.lower()
    result = {}

    # 1. Skills found
    found_skills = {}
    total_skills = 0
    for category, skills in SKILLS.items():
        found = [s for s in skills if s in text_lower]
        if found:
            found_skills[category] = found
            total_skills += len(found)
    result["skills"] = found_skills
    result["total_skills"] = total_skills

    # 2. Keywords check
    keyword_results = {}
    for section, words in KEYWORDS.items():
        found = [w for w in words if w in text_lower]
        keyword_results[section] = {
            "found": len(found) > 0,
            "keywords": found
        }
    result["keywords"] = keyword_results

    # 3. Contact info check
    email = bool(re.search(r'[\w.-]+@[\w.-]+\.\w+', text))
    phone = bool(re.search(r'(\+92|0)?[\s-]?\d{3}[\s-]?\d{7}|\d{10,11}', text))
    linkedin = "linkedin" in text_lower
    github   = "github" in text_lower
    result["contact"] = {
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github
    }

    # 4. Word count & length check
    words = len(text.split())
    result["word_count"] = words
    if words < 200:
        result["length_feedback"] = "Resume bohot chota hai — zyada detail add karo!"
    elif words > 800:
        result["length_feedback"] = "Resume thoda lamba hai — concise rakho!"
    else:
        result["length_feedback"] = "Resume ki length bilkul theek hai!"

    # 5. Score calculate karo
    score = 0

    # Skills score (max 40)
    score += min(40, total_skills * 3)

    # Keywords score (max 30)
    for section, data in keyword_results.items():
        if data["found"]:
            score += 10

    # Contact score (max 20)
    if email:    score += 5
    if phone:    score += 5
    if linkedin: score += 5
    if github:   score += 5

    # Length score (max 10)
    if 200 <= words <= 800:
        score += 10

    result["score"] = min(100, score)

    # 6. Grade
    if score >= 80:
        result["grade"] = "A"
        result["grade_text"] = "Excellent!"
    elif score >= 60:
        result["grade"] = "B"
        result["grade_text"] = "Good!"
    elif score >= 40:
        result["grade"] = "C"
        result["grade_text"] = "Average"
    else:
        result["grade"] = "D"
        result["grade_text"] = "Needs Work"

    # 7. Suggestions
    suggestions = []
    if not email:
        suggestions.append("Email address add karo — zaroor hona chahiye!")
    if not phone:
        suggestions.append("Phone number add karo!")
    if not linkedin:
        suggestions.append("LinkedIn profile link add karo!")
    if not github:
        suggestions.append("GitHub link add karo — especially for tech jobs!")
    if not keyword_results["education"]["found"]:
        suggestions.append("Education section properly likho — degree, university, year!")
    if not keyword_results["experience"]["found"]:
        suggestions.append("Experience section add karo — internships bhi chalenge!")
    if not keyword_results["certifications"]["found"]:
        suggestions.append("Certifications add karo — Coursera, Udemy wagera!")
    if total_skills < 5:
        suggestions.append("Zyada technical skills add karo!")
    if words < 200:
        suggestions.append("Resume mein zyada detail likho!")

    if not suggestions:
        suggestions.append("Zabardast resume hai — koi major issue nahi!")

    result["suggestions"] = suggestions
    return result

# ── Routes ────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    if "resume" not in request.files:
        return jsonify({"error": "File nahi mila!"})
    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "Koi file select nahi ki!"})
    text = extract_text(file)
    if not text.strip():
        return jsonify({"error": "File se text extract nahi hua!"})
    result = analyze_resume(text)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)