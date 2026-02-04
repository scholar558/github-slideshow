import json
import os
import re
import smtplib
from email.message import EmailMessage
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SKILLS = {
    "python",
    "javascript",
    "java",
    "sql",
    "aws",
    "docker",
    "kubernetes",
    "react",
    "node",
    "flask",
    "django",
    "linux",
    "git",
    "ci/cd",
}

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret")


def extract_text_from_pdf(path: Path) -> str:
    if PdfReader is None:
        raise RuntimeError("PyPDF2 is not installed. Install requirements.txt")
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def parse_cv_text(text: str) -> dict:
    lowered = text.lower()
    found_skills = sorted(skill for skill in SKILLS if skill in lowered)

    year_matches = [int(match) for match in re.findall(r"(\d+)\s+years?", lowered)]
    years_experience = max(year_matches, default=0)

    return {
        "skills": found_skills,
        "years_experience": years_experience,
        "summary": text.strip()[:500],
    }


def parse_cv(path: Path) -> dict:
    if path.suffix.lower() == ".pdf":
        text = extract_text_from_pdf(path)
    else:
        text = path.read_text(encoding="utf-8", errors="ignore")
    return parse_cv_text(text)


def load_jobs() -> list[dict]:
    jobs_path = DATA_DIR / "jobs.json"
    with jobs_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def match_jobs(cv_data: dict, jobs: list[dict]) -> list[dict]:
    matches = []
    cv_skills = set(cv_data.get("skills", []))
    cv_years = cv_data.get("years_experience", 0)

    for job in jobs:
        required_skills = set(job.get("required_skills", []))
        required_years = job.get("required_years", 0)
        if required_skills.issubset(cv_skills) and required_years <= cv_years:
            matches.append(job)
    return matches


def send_email(recipient: str, matches: list[dict]) -> tuple[bool, str]:
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    smtp_from = os.environ.get("SMTP_FROM")

    if not all([smtp_host, smtp_user, smtp_pass, smtp_from]):
        return False, "SMTP is not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASS, SMTP_FROM."

    body_lines = ["Here are the roles you fully qualify for:", ""]
    for job in matches:
        body_lines.append(f"- {job['title']} at {job['company']} ({job['url']})")

    message = EmailMessage()
    message["Subject"] = "Qualified Job Matches"
    message["From"] = smtp_from
    message["To"] = recipient
    message.set_content("\n".join(body_lines))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(message)

    return True, "Email sent successfully."


@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    cv_data = None
    email_status = None

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        uploaded = request.files.get("cv")

        if not uploaded or uploaded.filename == "":
            flash("Please upload a CV file.")
            return redirect(url_for("index"))

        filename = uploaded.filename
        saved_path = UPLOAD_DIR / filename
        uploaded.save(saved_path)

        try:
            cv_data = parse_cv(saved_path)
        except Exception as exc:
            flash(f"Failed to parse CV: {exc}")
            return redirect(url_for("index"))

        jobs = load_jobs()
        results = match_jobs(cv_data, jobs)

        if email:
            email_status = send_email(email, results)

    return render_template(
        "index.html",
        cv_data=cv_data,
        results=results,
        email_status=email_status,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
