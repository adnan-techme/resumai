import streamlit as st
from google import genai
import os
import subprocess
import pypdf
import time

# Must be the very first Streamlit command
st.set_page_config(page_title="ATS Resume Tailor", page_icon="✨", layout="centered")

# --- Custom CSS for Material/Modern Design ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

/* Hide Streamlit components */
header {visibility: hidden;}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif !important;
}

[data-testid="stAppViewContainer"] {
    background-color: #09090b;
    background-image: radial-gradient(circle at 50% 0%, #7f1d1d 0%, transparent 60%);
    color: #f1f5f9;
}

/* Titles */
.main-title {
    text-align: center;
    font-weight: 800;
    background: -webkit-linear-gradient(45deg, #ef4444, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3.5rem;
    margin-bottom: 0;
    padding-bottom: 10px;
}
.sub-title {
    text-align: center;
    color: #94a3b8;
    font-size: 1.2rem;
    font-weight: 300;
    margin-bottom: 2.5rem;
}

/* Primary Button Styling */
div.stButton > button {
    background: linear-gradient(135deg, #ef4444 0%, #2563eb 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.5rem 1.5rem;
    font-weight: 600;
    box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4);
    transition: all 0.3s ease;
}
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(239, 68, 68, 0.6);
    color: white;
    border: none;
}

/* Text Area */
.stTextArea textarea {
    background-color: rgba(30, 41, 59, 0.7) !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
    border-radius: 12px !important;
    padding: 15px !important;
    font-size: 1rem !important;
}
.stTextArea textarea:focus {
    border-color: #ef4444 !important;
    box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.2) !important;
}

/* Expanders */
.streamlit-expanderHeader {
    background-color: rgba(30, 41, 59, 0.7) !important;
    border-radius: 8px !important;
    border: 1px solid #334155 !important;
}

/* Markdown Horizontal Rule */
hr {
    border-top: 1px solid #334155;
}
</style>
""", unsafe_allow_html=True)

# --- App Header ---
st.markdown('<h1 class="main-title">ATS Resume Tailor 🕸️</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Instantly tailor your resume and cover letter with the power of Gemini.</p>', unsafe_allow_html=True)

# Cross-platform LaTeX executable detection
def get_latex_cmd():
    import shutil
    local_win_tectonic = os.path.join(".", "tectonic", "tectonic.exe")
    if os.path.exists(local_win_tectonic):
        return [local_win_tectonic]
    if shutil.which("tectonic"):
        return ["tectonic"]
    return ["pdflatex", "-interaction=nonstopmode"]

# Secure API Key Resolution
def get_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    if os.environ.get("GEMINI_API_KEY"):
        return os.environ.get("GEMINI_API_KEY")
    # Fallback for local testing or custom deployment
    return st.sidebar.text_input("Gemini API Key", type="password", help="Enter your Gemini API Key")

api_key = get_api_key()

# Initialize Session State
if "generated" not in st.session_state:
    st.session_state.generated = False
if "tailored_tex" not in st.session_state:
    st.session_state.tailored_tex = ""
if "cover_letter" not in st.session_state:
    st.session_state.cover_letter = ""
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None

# --- Main Logic ---
def call_gemini_with_retry(client, prompt, max_retries=3):
    """Wrapper to handle 429 Rate Limits automatically."""
    for i in range(max_retries):
        try:
            return client.models.generate_content(model='gemini-3.5-flash-lite', contents=prompt)
        except Exception as e:
            if "429" in str(e) and i < max_retries - 1:
                st.toast(f"Rate limit hit. Waiting 20 seconds to retry... (Attempt {i+1}/{max_retries})")
                time.sleep(20)
                continue
            raise e

def generate_tailored_resume(client, base_tex, jd):
    prompt = f"""
    You are an expert technical recruiter and resume writer. 
    Below is my base resume in LaTeX format and a Job Description (JD) I am applying for.
    
    Job Description:
    {jd}
    
    Base Resume (LaTeX):
    {base_tex}
    
    Task:
    Return ONLY a modified version of the LaTeX code that subtly highlights relevant skills from the JD.
    CRITICALLY IMPORTANT: DO NOT fabricate any new experience, duties, or skills. If the JD asks for a skill (like "API documentation" or "Python") that is NOT supported by my base resume, DO NOT add it. You must stay 100% truthful to the base resume. Only reword existing bullet points to better align with the JD's terminology if the core meaning remains exactly the same.
    
    CRITICAL INSTRUCTIONS:
    1. Ensure the font size in the "Technical Skills" section EXACTLY matches the rest of the document. Do not make it bigger. Use the exact same formatting macros used in other sections.
    2. The final resume MUST be EXACTLY one full page. It MUST reach the very bottom of the first page, no less and no more. DO NOT remove any bullet points, roles, or sections. To fill space effectively, expand the "Projects" section by adding detailed explanations of what each app does, and add an extra line to the "Technical Skills" section containing general/soft skills if there is still space. DO NOT over-condense the original text. You can also reword experience sentences to take up more or fewer lines as needed.
    3. You may adjust vertical spacing using \vspace (e.g., \vspace{{4pt}}) ONLY inside the document body (after \begin{{document}}) to ensure the content flawlessly hits the bottom margin. DO NOT modify or remove any part of the preamble (everything before \begin{{document}}), geometry, margins, or any custom \newcommand definitions. Copy them EXACTLY as they are in the base resume.
    4. Do not add any conversational text or markdown formatting around the output, ONLY the raw LaTeX code.
    """
    response = call_gemini_with_retry(client, prompt)
    return response.text

def generate_cover_letter(client, base_tex, jd):
    prompt = f"""
    You are an expert career coach and cover letter writer.
    Below is my base resume in LaTeX format and a Job Description (JD) I am applying for.
    
    Job Description:
    {jd}
    
    Base Resume (LaTeX):
    {base_tex}
    
    Task:
    Write a highly targeted cover letter based on the provided resume and job description.
    Make it sound personal, professional, and enthusiastic.
    Highlight the most relevant experiences from the resume that match the job description.
    Return ONLY the text of the cover letter. Do not include any conversational text.
    """
    response = call_gemini_with_retry(client, prompt)
    return response.text

# User Input
job_description = st.text_area("Job Description", height=200, placeholder="Paste the job description here...")

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    resume_clicked = st.button("🚀 Generate Tailored Resume", use_container_width=True)
with col_btn2:
    cover_letter_clicked = st.button("✍️ Generate Cover Letter", use_container_width=True)

if resume_clicked or cover_letter_clicked:
    if not job_description.strip():
        st.error("Please paste the job description.")
    else:
        try:
            with open("main.tex", "r", encoding="utf-8") as f:
                base_tex_content = f.read()
        except FileNotFoundError:
            st.error("main.tex file not found in the current directory.")
            st.stop()
            
        try:
            if not api_key:
                st.error("Gemini API Key is missing. Please set GEMINI_API_KEY in secrets or enter it in the sidebar.")
                st.stop()
            client = genai.Client(api_key=api_key)
            
            if resume_clicked:
                progress_bar = st.progress(5, text="🧠 Analyzing Job Description and extracting keywords...")
                progress_bar.progress(20, text="📝 Drafting tailored resume to match JD...")
                tailored_tex = generate_tailored_resume(client, base_tex_content, job_description)
                if tailored_tex.startswith("```latex"):
                    tailored_tex = tailored_tex[8:]
                elif tailored_tex.startswith("```tex"):
                    tailored_tex = tailored_tex[6:]
                if tailored_tex.endswith("```"):
                    tailored_tex = tailored_tex[:-3]
                    
                tailored_tex = tailored_tex.replace("\\package{", "\\usepackage{")
                
                st.session_state.tailored_tex = tailored_tex.strip()
                st.session_state.pdf_data = None
                
                progress_bar.progress(70, text="⚙️ Compiling formatting into a beautiful PDF...")
                max_attempts = 3
                for attempt in range(max_attempts):
                    with open("tailored_resume.tex", "w", encoding="utf-8") as f:
                        f.write(st.session_state.tailored_tex)
                        
                    try:
                        if os.path.exists("tailored_resume.pdf"):
                            os.remove("tailored_resume.pdf")
                            
                        cmd = get_latex_cmd() + ["tailored_resume.tex"]
                        subprocess.run(cmd, check=True, capture_output=True)
                        
                        with open("tailored_resume.pdf", "rb") as pdf_file:
                            reader = pypdf.PdfReader(pdf_file)
                            num_pages = len(reader.pages)
                        
                        if num_pages == 1:
                            progress_bar.progress(100, text="✅ Finalizing documents...")
                            with open("tailored_resume.pdf", "rb") as f:
                                st.session_state.pdf_data = f.read()
                            break
                        else:
                            if attempt < max_attempts - 1:
                                progress_bar.progress(75 + (attempt * 10), text=f"✂️ Resume is {num_pages} pages long. Condensing to strictly fit 1 page (Attempt {attempt+1})...")
                                prompt = f"""
                                The LaTeX code you just generated resulted in a PDF that is {num_pages} pages long.
                                You MUST condense the content so it fits strictly on 1 page.
                                - DO NOT remove any bullet points, roles, or sections. Keep all content.
                                - Shorten wordy sentences so they take up 1 line instead of 2.
                                - DO NOT adjust \vspace, margins, geometry, or any formatting commands. ONLY shorten the text.
                                - Do NOT change the font sizes to make it fit.
                                - Return ONLY the modified LaTeX code.
                                
                                Current LaTeX:
                                {st.session_state.tailored_tex}
                                """
                                response = call_gemini_with_retry(client, prompt)
                                new_tex = response.text
                                if new_tex.startswith("```latex"): new_tex = new_tex[8:]
                                elif new_tex.startswith("```tex"): new_tex = new_tex[6:]
                                if new_tex.endswith("```"): new_tex = new_tex[:-3]
                                st.session_state.tailored_tex = new_tex.strip()
                            else:
                                progress_bar.progress(100, text="✅ Finalizing documents...")
                                with open("tailored_resume.pdf", "rb") as f:
                                    st.session_state.pdf_data = f.read()
                    except Exception as e:
                        print(f"Compilation error: {e}")
                        break

            if cover_letter_clicked:
                progress_bar = st.progress(5, text="✍️ Writing a highly targeted cover letter...")
                cover_letter = generate_cover_letter(client, base_tex_content, job_description)
                if cover_letter.startswith("```text"):
                    cover_letter = cover_letter[7:]
                elif cover_letter.startswith("```"):
                    cover_letter = cover_letter[3:]
                if cover_letter.endswith("```"):
                    cover_letter = cover_letter[:-3]
                
                st.session_state.cover_letter = cover_letter.strip()
                progress_bar.progress(100, text="✅ Finalizing cover letter...")

            st.session_state.generated = True
            st.rerun()
            
        except Exception as e:
            if "429" in str(e):
                st.error("Google Gemini API Rate Limit Exceeded (20 requests per minute). Please wait about a minute and try again!")
            elif "413" in str(e):
                st.error("Payload Too Large (413). The job description or base resume is too large for the API. Please try providing a shorter one.")
            else:
                st.error(f"An error occurred: {e}")

# --- Render Results if Generated ---
if st.session_state.generated:
    st.markdown("---")
    st.markdown("<h3 style='text-align: center; color: #ef4444; margin-bottom: 20px;'>🕷️ Your Documents are Ready!</h3>", unsafe_allow_html=True)
    
    columns = []
    if st.session_state.pdf_data:
        columns.append("resume")
    if st.session_state.cover_letter:
        columns.append("cover")
        
    if not columns:
        st.warning("No documents were successfully generated.")
    else:
        cols = st.columns(len(columns))
        for i, col_type in enumerate(columns):
            with cols[i]:
                if col_type == "resume":
                    st.download_button(
                        label="📥 Download Resume (.pdf)",
                        data=st.session_state.pdf_data,
                        file_name="Adnan_Ahmed_Resume.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                elif col_type == "cover":
                    st.download_button(
                        label="📥 Download Cover Letter (.txt)",
                        data=st.session_state.cover_letter,
                        file_name="Adnan_Ahmed_CoverLetter.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                    
    if st.session_state.cover_letter:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("👁️ Preview Cover Letter"):
            st.write(st.session_state.cover_letter)
