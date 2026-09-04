# ATS Resume Tailor 🕸️

**ATS Resume Tailor** is a local Streamlit application designed to instantly tailor your resume and cover letter for specific job applications using the power of Google Gemini.

The main philosophy behind this tool is to **make it easier to fine-tune your resume for specific jobs without fabricating lies**. Instead of inventing experience, it analyzes a given Job Description (JD) and intelligently highlights your *existing* real skills, matching the terminology used by the employer.

## Features

- **Resume Tailoring**: Reads your base LaTeX resume and injects a customized "Technical Skills" section that prioritizes the exact technologies, tools, and keywords mentioned in the JD. It strictly preserves your 1-page layout and formatting.
- **Cover Letter Generation**: Drafts a conversational, professional, and factual cover letter (in both `.txt` and `.docx` formats) by drawing direct parallels between your real professional experience and the specific responsibilities of the role.
- **Job Application Tracker**: Includes a lightweight, local persistent tracker (saved to `job_applications.json`). It automatically counts your applications for the current month and lets you keep a history of the roles you've applied for.

## Requirements

- Python 3.x
- Standard Python libraries plus `streamlit`, `google-genai`, `pypdf`, `python-docx` (see `requirements.txt`)
- A valid Google Gemini API Key
- `tectonic` or `pdflatex` for compiling LaTeX to PDF locally.

## Usage

1. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```
2. Enter your Gemini API key (if not already set in your environment variables or Streamlit secrets).
3. Paste the target Job Description.
4. Click **Generate Tailored Resume** or **Generate Cover Letter**.
5. Once applied, click **Log Application** to track your progress!
