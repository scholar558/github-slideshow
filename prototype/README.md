# CV Matcher Prototype

This prototype lets you upload a CV, extracts simple skills + years of experience, matches against sample job listings, and optionally emails you a summary of roles you fully qualify for.

## Features
- Upload CV (PDF or TXT).
- Naive skill + years-of-experience extraction.
- Match against sample job data in `data/jobs.json`.
- Optional SMTP email delivery.

## Getting started

```bash
cd prototype
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000` to use the UI.

## SMTP configuration (optional)

Set the following environment variables to enable email sending:

```bash
export SMTP_HOST=smtp.example.com
export SMTP_PORT=587
export SMTP_USER=your-user
export SMTP_PASS=your-password
export SMTP_FROM=you@example.com
```

## Sample data
Update `data/jobs.json` with job roles you want to evaluate. The matching rules require all `required_skills` and the `required_years` threshold.
