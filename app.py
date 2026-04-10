import os
import re
import json
from io import BytesIO
from typing import List, Tuple
from datetime import date

import streamlit as st

try:
    import docx
except Exception:
    docx = None

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False


# ---------- Page setup ----------
st.set_page_config(page_title="Fresher Job Cracker AI", page_icon="💼", layout="wide")


# ---------- Styling ----------
st.markdown(
    """
    <style>
    :root {
        --bg: #0f1115;
        --card: #171a21;
        --card-2: #1e232d;
        --text: #f7f7f8;
        --muted: #b6bcc8;
        --line: rgba(255,255,255,0.08);
        --accent: #fc8019;
        --accent-2: #ff9b4a;
        --success: #22c55e;
        --danger: #ef4444;
        --shadow: 0 12px 30px rgba(0,0,0,0.28);
    }

    html, body, [class*="css"]  {
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at top right, rgba(252,128,25,0.10), transparent 22%),
                    linear-gradient(180deg, #0c0e12 0%, #0f1115 100%);
        color: var(--text);
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2.2rem;
        max-width: 1280px;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #141821 0%, #10131a 100%);
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 1.4rem;
    }

    .hero {
        background: linear-gradient(135deg, rgba(252,128,25,0.18), rgba(252,128,25,0.08));
        border: 1px solid rgba(252,128,25,0.18);
        border-radius: 24px;
        padding: 1.3rem 1.4rem 1.1rem 1.4rem;
        box-shadow: var(--shadow);
        margin-bottom: 1rem;
    }

    .hero-title {
        font-size: 2.25rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin-bottom: 0.35rem;
        color: white;
    }

    .hero-sub {
        color: #fff3ea;
        font-size: 1rem;
        line-height: 1.55;
        max-width: 900px;
    }

    .badge-row {
        display: flex;
        gap: 0.55rem;
        flex-wrap: wrap;
        margin-top: 1rem;
    }

    .badge {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.08);
        color: white;
        padding: 0.45rem 0.75rem;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .soft-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border: 1px solid var(--line);
        border-radius: 22px;
        padding: 1rem 1rem 0.9rem 1rem;
        box-shadow: var(--shadow);
        margin-bottom: 1rem;
    }

    .card-title {
        font-size: 1.05rem;
        font-weight: 800;
        color: white;
        margin-bottom: 0.35rem;
    }

    .card-sub {
        color: var(--muted);
        font-size: 0.92rem;
        line-height: 1.45;
    }

    .step-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.8rem;
        margin: 0.95rem 0 1rem 0;
    }

    .step {
        background: linear-gradient(180deg, #171a21 0%, #141821 100%);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 0.9rem;
        min-height: 120px;
    }

    .step-num {
        color: var(--accent-2);
        font-size: 0.8rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .step-head {
        color: white;
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }

    .step-copy {
        color: var(--muted);
        font-size: 0.88rem;
        line-height: 1.45;
    }

    .section-title {
        font-size: 1.6rem;
        font-weight: 800;
        color: white;
        margin: 0.15rem 0 0.6rem 0;
    }

    .section-sub {
        color: var(--muted);
        font-size: 0.95rem;
        margin-bottom: 0.7rem;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, #181c23 0%, #13171f 100%);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 0.8rem 0.95rem;
    }

    div[data-testid="stMetricValue"] {
        color: white;
        font-size: 2rem;
        font-weight: 800;
    }

    div[data-testid="stMetricLabel"] {
        color: var(--muted);
    }

    .small-note {
        color: var(--muted);
        font-size: 0.87rem;
        line-height: 1.5;
    }

    .founder-note {
        background: rgba(255,255,255,0.03);
        border: 1px dashed rgba(252,128,25,0.25);
        border-radius: 18px;
        padding: 0.85rem 0.95rem;
        color: #ffe9d6;
        font-size: 0.93rem;
        line-height: 1.55;
        margin-top: 0.8rem;
    }

    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(135deg, var(--accent), #ff9a4f) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        min-height: 2.9rem !important;
        box-shadow: 0 8px 22px rgba(252,128,25,0.22);
    }

    .stButton > button:hover, .stDownloadButton > button:hover {
        filter: brightness(1.03);
        transform: translateY(-1px);
    }

    .stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"], .stDateInput input {
        border-radius: 14px !important;
    }

    [data-baseweb="tab-list"] {
        gap: 0.45rem;
        padding-bottom: 0.2rem;
    }

    [data-baseweb="tab"] {
        background: #161a21 !important;
        border: 1px solid var(--line) !important;
        border-radius: 999px !important;
        padding: 0.55rem 0.95rem !important;
        color: white !important;
        height: auto !important;
    }

    [aria-selected="true"][data-baseweb="tab"] {
        background: linear-gradient(135deg, var(--accent), #ff9a4f) !important;
        border-color: transparent !important;
        color: white !important;
    }

    hr {
        border: none;
        border-top: 1px solid var(--line);
        margin: 1.2rem 0;
    }

    @media (max-width: 1100px) {
        .step-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
    }

    @media (max-width: 640px) {
        .hero-title { font-size: 1.7rem; }
        .step-grid { grid-template-columns: 1fr; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- Helpers ----------
def extract_text_from_upload(uploaded_file) -> str:
    if uploaded_file is None:
        return ""

    file_name = (uploaded_file.name or "").lower()
    try:
        if file_name.endswith(".txt"):
            return uploaded_file.read().decode("utf-8", errors="ignore")

        if file_name.endswith(".docx") and docx is not None:
            document = docx.Document(uploaded_file)
            return "
".join([p.text for p in document.paragraphs if p.text.strip()])

        if file_name.endswith(".pdf") and PdfReader is not None:
            reader = PdfReader(uploaded_file)
            pages = []
            for page in reader.pages:
                try:
                    pages.append(page.extract_text() or "")
                except Exception:
                    pages.append("")
            return "
".join(pages)
    except Exception:
        return ""

    return ""


def analyze_uploaded_resume(resume_text: str, jd_text: str) -> Tuple[int, List[str], List[str], List[str], List[str]]:
    score, positives, feedback, suggestions = score_resume(
        resume_text=resume_text,
        jd_text=jd_text,
        profile_type="No experience",
        skills_text=", ".join(extract_keywords(resume_text)[:10]),
        experience_text=resume_text,
        projects_text=resume_text,
        target_role="Uploaded Resume",
    )
    _, matched, missing = estimate_match(resume_text, jd_text)
    return score, positives, feedback, suggestions, missing


def suggest_roles_from_resume(resume_text: str) -> Tuple[List[str], List[str]]:
    text = clean_text(resume_text).lower()
    role_map = {
        "sales": ["Key Account Manager", "Business Development Executive", "Sales Executive"],
        "marketing": ["Marketing Executive", "Brand Associate", "Category Executive"],
        "operations": ["Operations Executive", "Supply Chain Analyst", "Process Coordinator"],
        "analysis": ["Business Analyst", "Sales Analyst", "Operations Analyst"],
        "communication": ["Client Success Executive", "Inside Sales Executive", "Account Coordinator"],
    }

    recommended = []
    for key, roles in role_map.items():
        if key in text:
            recommended.extend(roles)

    if not recommended:
        recommended = ["Business Development Executive", "Operations Executive", "Marketing Executive"]

    not_ideal = [
        "Highly technical software engineering roles",
        "Senior management roles",
        "Deep-specialist roles requiring years of experience",
    ]

    return list(dict.fromkeys(recommended))[:5], not_ideal


# ---------- Helpers ----------
def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def extract_keywords(text: str) -> List[str]:
    text = clean_text(text).lower()
    words = re.findall(r"[a-zA-Z][a-zA-Z\-\+\.]{1,}", text)
    stopwords = {
        "the", "and", "for", "with", "you", "your", "our", "are", "will", "who", "that",
        "this", "from", "have", "has", "had", "job", "role", "work", "team", "into", "all",
        "any", "but", "not", "can", "able", "using", "use", "their", "they", "them", "what",
        "when", "where", "how", "why", "about", "should", "must", "good", "strong", "such",
        "looking", "candidate", "candidates", "skills", "skill", "experience", "preferred", "required",
        "years", "year", "month", "months", "day", "days", "etc", "new", "best", "need", "plus",
        "get", "build", "make", "help", "across", "within", "ability", "including", "responsible",
        "knowledge", "understanding", "seeking", "seeks", "seeker", "fresher", "graduate"
    }
    filtered = [w for w in words if len(w) > 2 and w not in stopwords]
    freq = {}
    for w in filtered:
        freq[w] = freq.get(w, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    return [w for w, _ in ranked[:30]]


def to_bullets(block: str, default_line: str) -> str:
    lines = [line.strip("-• ") for line in (block or "").split("\n") if line.strip()]
    if not lines:
        lines = [default_line]
    return "\n".join([f"- {line}" for line in lines])


def build_resume_fallback(name: str, email: str, phone: str, location: str, target_role: str, profile_type: str,
                          summary: str, education: str, experience: str, skills: str, projects: str,
                          certifications: str) -> str:
    default_summary_map = {
        "No experience": f"Motivated fresher targeting {target_role} roles with strong learning agility, communication skills, and a structured approach to problem-solving.",
        "Internship only": f"Early-career candidate targeting {target_role} roles with internship exposure, business understanding, and the ability to execute in fast-paced environments.",
        "Career switch": f"Professional transitioning into {target_role} roles with transferable skills, adaptability, and a strong willingness to learn and deliver results.",
        "Experienced": f"Results-oriented candidate targeting {target_role} roles with relevant execution experience, stakeholder handling, and problem-solving skills.",
    }
    return f"""# {name}
{email} | {phone} | {location}

## Target Role
{target_role}

## Profile Type
{profile_type}

## Professional Summary
{summary or default_summary_map.get(profile_type, default_summary_map['No experience'])}

## Education
{education or 'Add your latest degree, institute, and graduation year'}

## Experience
{to_bullets(experience, 'Add internship, campus leadership, freelance work, or responsibility-based experience relevant to the target role')}

## Projects
{to_bullets(projects, 'Add one role-relevant project showing analysis, execution, research, sales, or operations impact')}

## Certifications
{certifications or 'Add relevant certifications here'}

## Skills
{skills or 'Communication, Excel, PowerPoint, Research, Problem Solving, Stakeholder Management'}
"""


def build_cover_letter_fallback(name: str, company: str, role: str, summary: str, strengths: str, jd_text: str) -> str:
    keywords = extract_keywords(jd_text)[:6]
    kw_text = ", ".join(keywords) if keywords else "communication, execution, and adaptability"
    return f"""Dear Hiring Manager,

I am writing to express my interest in the {role} role at {company}. I am excited about this opportunity because it aligns with my background and my interest in building a strong career in this field.

{summary or 'I bring a combination of business understanding, learning agility, and a strong willingness to take ownership.'} My strengths include {strengths or 'communication, structured thinking, and execution'}. Based on the job description, I understand that the role values {kw_text}. I believe these expectations align well with my profile and potential.

I would welcome the chance to discuss how I can contribute to your team. Thank you for your time and consideration.

Sincerely,
{name}
"""


def estimate_match(resume_text: str, jd_text: str) -> Tuple[int, List[str], List[str]]:
    resume_keywords = set(extract_keywords(resume_text))
    jd_keywords = set(extract_keywords(jd_text))
    if not jd_keywords:
        return 0, [], []
    overlap = sorted(list(resume_keywords & jd_keywords))
    missing = sorted(list(jd_keywords - resume_keywords))[:12]
    score = int((len(overlap) / max(len(jd_keywords), 1)) * 100)
    score = max(15, min(score, 95)) if resume_text.strip() and jd_text.strip() else 0
    return score, overlap[:12], missing


def score_resume(resume_text: str, jd_text: str, profile_type: str, skills_text: str, experience_text: str,
                 projects_text: str, target_role: str) -> Tuple[int, List[str], List[str], List[str]]:
    score = 35
    feedback, positives, suggestions = [], [], []
    skills_count = len([s for s in skills_text.split(",") if s.strip()])
    exp_lines = len([x for x in experience_text.split("\n") if x.strip()])
    proj_lines = len([x for x in projects_text.split("\n") if x.strip()])
    has_numbers = bool(re.search(r"\d", resume_text or ""))
    has_summary = "## Professional Summary" in resume_text and len(clean_text(resume_text.split("## Professional Summary")[-1][:220])) > 20

    if has_summary:
        score += 8
        positives.append("You have a usable summary section.")
    else:
        feedback.append("Your resume lacks a clear professional summary.")

    if skills_count >= 5:
        score += 10
        positives.append("Your skills section has decent coverage.")
    else:
        feedback.append("Your skills section is too thin and may look weak to recruiters.")

    if exp_lines >= 2:
        score += 12
        positives.append("You have enough experience or internship bullets to work with.")
    else:
        feedback.append("You need stronger experience bullets, even if they come from internships, college work, events, or responsibilities.")

    if proj_lines >= 1:
        score += 10
        positives.append("You have at least one project, which helps as a fresher.")
    else:
        feedback.append("You need at least one role-relevant project to avoid looking empty as a fresher.")

    if has_numbers:
        score += 10
        positives.append("Your resume includes numbers, which makes it more credible.")
    else:
        feedback.append("Your resume has no measurable impact. Add numbers, scale, percentages, team size, or frequency wherever truthful.")

    match_score, _, missing = estimate_match(resume_text, jd_text)
    if match_score >= 60:
        score += 15
        positives.append("Your resume language aligns reasonably well with the job description.")
    elif match_score >= 35:
        score += 8
        feedback.append("Your resume partially matches the target job, but important keywords are still missing.")
    else:
        feedback.append("Your resume is too generic for this role and will likely struggle in ATS screening.")

    if target_role.strip():
        score += 5
        positives.append("You are targeting a defined role, which makes customization easier.")
    else:
        feedback.append("You have not defined a target role clearly.")

    if profile_type == "Career switch":
        feedback.append("As a career switcher, you must highlight transferable achievements more clearly.")

    score = max(0, min(score, 100))

    if score < 55:
        feedback.insert(0, "This resume will likely get rejected in its current form for competitive roles.")
    elif score < 75:
        feedback.insert(0, "This resume is decent but still not strong enough to maximize shortlist chances.")
    else:
        feedback.insert(0, "This resume is in good shape, but a few role-specific improvements can still raise your chances.")

    if missing:
        suggestions.append(f"Add these missing job keywords where truthful: {', '.join(missing[:6])}.")
    if not has_numbers:
        suggestions.append("Rewrite at least 2 bullets with numbers or measurable outcomes.")
    if proj_lines < 1:
        suggestions.append(f"Add 1 project tailored to {target_role or 'your target role'}.")
    if exp_lines < 2:
        suggestions.append("Turn internships, college leadership, shop work, volunteering, or event coordination into experience bullets.")
    if skills_count < 5:
        suggestions.append("Expand your skills section with relevant tools and functional skills.")
    if not suggestions:
        suggestions.append("Customize this version for each company instead of using one resume everywhere.")

    return score, positives[:5], feedback[:6], suggestions[:5]


def generate_action_plan(target_role: str, missing_skills: List[str], resume_score: int, profile_type: str) -> List[str]:
    role = target_role or "your target role"
    top_missing = ", ".join(missing_skills[:3]) if missing_skills else "role-specific keywords"
    plan = [
        f"Day 1: Rewrite your resume for {role} and fix the weakest bullets first.",
        f"Day 2: Add 1 relevant project and include these missing keywords where truthful: {top_missing}.",
        "Day 3: Apply to 15 carefully selected roles instead of mass-applying blindly.",
        "Day 4: Prepare answers for 'Tell me about yourself', 'Why this role?', and one strengths question.",
        "Day 5: Improve LinkedIn headline, About section, and featured achievements.",
        "Day 6: Follow up on earlier applications and message 5 recruiters or alumni.",
        "Day 7: Review rejections, refine your resume again, and apply to another 15 better-matched roles.",
    ]
    if resume_score < 55:
        plan[0] = f"Day 1: Do not apply yet. First rebuild your resume for {role} because the current version is too weak."
    if profile_type == "No experience":
        plan[1] = f"Day 2: Add project, internship-style work, event responsibility, or family business contribution relevant to {role}."
    return plan


def make_pdf_bytes(title: str, content: str) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(40, y, title)
    y -= 28
    pdf.setFont("Helvetica", 10)

    for raw_line in (content or "").split("\n"):
        line = raw_line.replace("#", "").replace("*", "").strip()
        if not line:
            y -= 12
            continue
        words = line.split()
        current = ""
        wrapped_lines = []
        for word in words:
            test = f"{current} {word}".strip()
            if pdf.stringWidth(test, "Helvetica", 10) < width - 80:
                current = test
            else:
                wrapped_lines.append(current)
                current = word
        if current:
            wrapped_lines.append(current)
        for wline in wrapped_lines:
            if y < 50:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = height - 50
            pdf.drawString(40, y, wline)
            y -= 14
    pdf.save()
    buffer.seek(0)
    return buffer.read()


def load_example_data() -> dict:
    return {
        "name": "Tamoghna Adhikari",
        "email": "tamoghna@example.com",
        "phone": "+91XXXXXXXXXX",
        "location": "Kolkata, India",
        "target_role": "Key Account Manager",
        "profile_type": "Internship only",
        "summary": "Recent PGDM graduate targeting sales and account management roles with strong communication, analytical thinking, and market understanding.",
        "education": "PGDM, IMT Nagpur\nB.Tech in Food Technology, Institute Name",
        "experience": "Conducted market and competitor analysis for academic and live projects.\nSupported quality and operations work during internships.\nManaged coordination and communication responsibilities in team-based assignments.",
        "projects": "Built a buyer persona and customer journey framework for a consumer brand.\nCreated a market analysis and go-to-market recommendation for a business case competition.",
        "certifications": "Advanced Excel\nGoogle Analytics Fundamentals",
        "skills": "Excel, PowerPoint, Communication, Market Research, Sales, Analysis, Presentation Skills",
        "company": "Zomato",
        "jd_text": "We are looking for a Key Account Manager to manage partner relationships, drive growth, analyze performance, coordinate with internal teams, and improve merchant success. Strong communication, problem-solving, stakeholder management, and Excel skills are preferred."
    }


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def call_llm(system_prompt: str, user_prompt: str) -> str:
    client = get_openai_client()
    if client is None:
        raise RuntimeError("OpenAI client not available")
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content.strip()


def save_current_version(name: str, company: str, target_role: str):
    entry = {
        "label": f"{len(st.session_state['history']) + 1}. {target_role or 'Untitled Role'} @ {company or 'General'}",
        "name": name,
        "company": company,
        "target_role": target_role,
        "resume_output": st.session_state.get("resume_output", ""),
        "cover_output": st.session_state.get("cover_output", ""),
        "resume_score": st.session_state.get("resume_score"),
        "match_score": st.session_state.get("match_score"),
        "feedback": st.session_state.get("feedback", []),
        "suggestions": st.session_state.get("suggestions", []),
        "missing": st.session_state.get("missing", []),
        "action_plan": st.session_state.get("action_plan", []),
    }
    st.session_state["history"].append(entry)


def load_history_entry(entry: dict):
    st.session_state["resume_output"] = entry.get("resume_output", "")
    st.session_state["cover_output"] = entry.get("cover_output", "")
    st.session_state["resume_score"] = entry.get("resume_score")
    st.session_state["match_score"] = entry.get("match_score")
    st.session_state["feedback"] = entry.get("feedback", [])
    st.session_state["suggestions"] = entry.get("suggestions", [])
    st.session_state["missing"] = entry.get("missing", [])
    st.session_state["action_plan"] = entry.get("action_plan", [])


# ---------- Session state ----------
for key, default in {
    "history": [],
    "applications": [],
    "user_feedback_log": [],
    "example_loaded": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## Settings")
    use_ai = st.toggle("Use OpenAI API", value=False)

    st.markdown("<div class='soft-card'><div class='card-title'>What makes this different</div><div class='card-sub'>Built for freshers who need guidance, not just tools.</div></div>", unsafe_allow_html=True)
    st.markdown("- Fresher-first resume builder")
    st.markdown("- Brutally honest resume score")
    st.markdown("- Job match + gap diagnosis")
    st.markdown("- 7-day action plan")
    st.markdown("- Application tracker")
    st.markdown("- Interview simulator")
    st.markdown("- AI feedback system")

    st.markdown("---")
    st.markdown("### Saved versions")
    history = st.session_state.get("history", [])
    if history:
        selected_label = st.selectbox("Compare past versions", [h["label"] for h in history])
        selected_index = [h["label"] for h in history].index(selected_label)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Load", use_container_width=True):
                load_history_entry(history[selected_index])
        with c2:
            if st.button("Delete", use_container_width=True):
                st.session_state["history"].pop(selected_index)
                st.rerun()
    else:
        st.caption("No saved versions yet.")

    st.markdown("<div class='founder-note'>Built by someone who knows how frustrating the fresher job search can be. The goal is simple: help users fix what matters fastest.</div>", unsafe_allow_html=True)


# ---------- Hero ----------
st.markdown(
    """
    <div class='hero'>
        <div class='hero-title'>🍔 Fresher Job Cracker AI</div>
        <div class='hero-sub'>Get shortlisted for jobs even with no experience. This app helps you fix your resume, improve role fit, prepare for interviews, and track applications with a smooth guided workflow.</div>
        <div class='badge-row'>
            <div class='badge'>Resume Builder</div>
            <div class='badge'>Brutal Resume Score</div>
            <div class='badge'>Job Match</div>
            <div class='badge'>Interview Practice</div>
            <div class='badge'>Application Tracker</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class='step-grid'>
        <div class='step'><div class='step-num'>Step 1</div><div class='step-head'>Fill your profile</div><div class='step-copy'>Start with your details, education, experience, and target role.</div></div>
        <div class='step'><div class='step-num'>Step 2</div><div class='step-head'>Build and improve</div><div class='step-copy'>Generate your resume, then sharpen it for the role you want.</div></div>
        <div class='step'><div class='step-num'>Step 3</div><div class='step-head'>Check fit</div><div class='step-copy'>Score your resume, compare against the job description, and fix gaps.</div></div>
        <div class='step'><div class='step-num'>Step 4</div><div class='step-head'>Prepare and track</div><div class='step-copy'>Practice interviews, follow a 7-day plan, and manage applications.</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

cta1, cta2, cta3 = st.columns([1, 1, 2])
with cta1:
    if st.button("Load Example Data", use_container_width=True):
        for k, v in load_example_data().items():
            st.session_state[k] = v
        st.session_state["example_loaded"] = True
with cta2:
    if st.button("Clear All", use_container_width=True):
        keep = {"history", "applications", "user_feedback_log"}
        for key in list(st.session_state.keys()):
            if key not in keep:
                st.session_state.pop(key, None)
        st.session_state["example_loaded"] = False
        st.rerun()
with cta3:
    if st.session_state.get("example_loaded"):
        st.success("Example data loaded. You can now test all tabs quickly.")
    else:
        st.info("Start here: fill your profile on the left, then use the tabs on the right in order.")


# ---------- Main split ----------
left, right = st.columns([1.05, 1], gap="large")

with left:
    st.markdown("<div class='soft-card'><div class='section-title'>Candidate Details</div><div class='section-sub'>Tell the app who you are and what roles you are targeting.</div></div>", unsafe_allow_html=True)

    name = st.text_input("Full Name", value=st.session_state.get("name", ""), placeholder="Tamoghna Adhikari")
    email = st.text_input("Email", value=st.session_state.get("email", ""), placeholder="you@example.com")
    phone = st.text_input("Phone", value=st.session_state.get("phone", ""), placeholder="+91XXXXXXXXXX")
    location = st.text_input("Location", value=st.session_state.get("location", ""), placeholder="Kolkata, India")
    target_role = st.text_input("Target Role", value=st.session_state.get("target_role", ""), placeholder="Key Account Manager")

    profile_options = ["No experience", "Internship only", "Career switch", "Experienced"]
    profile_type = st.selectbox(
        "Profile Type",
        profile_options,
        index=profile_options.index(st.session_state.get("profile_type", "No experience")) if st.session_state.get("profile_type", "No experience") in profile_options else 0,
    )

    summary = st.text_area("Professional Summary", value=st.session_state.get("summary", ""), height=95)
    education = st.text_area("Education", value=st.session_state.get("education", ""), height=95)
    experience = st.text_area("Experience / Internships / Responsibilities", value=st.session_state.get("experience", ""), height=115)
    projects = st.text_area("Projects", value=st.session_state.get("projects", ""), height=95)
    certifications = st.text_area("Certifications", value=st.session_state.get("certifications", ""), height=70)
    skills = st.text_area("Skills (comma-separated)", value=st.session_state.get("skills", ""), height=85)

    st.markdown("<div class='soft-card'><div class='card-title'>Target Job</div><div class='card-sub'>Paste a real job description for better scoring and matching.</div></div>", unsafe_allow_html=True)
    company = st.text_input("Company Name", value=st.session_state.get("company", ""), placeholder="Zomato")
    jd_text = st.text_area("Paste Job Description", value=st.session_state.get("jd_text", ""), height=220)

with right:
    st.markdown("<div class='soft-card'><div class='section-title'>Career Workflow</div><div class='section-sub'>Move through the tabs like a guided journey instead of one long messy process.</div></div>", unsafe_allow_html=True)

    save_col, info_col = st.columns([1, 2])
    with save_col:
        if st.button("Save Current Version", use_container_width=True):
            save_current_version(name, company, target_role)
            st.success("Saved.")
    with info_col:
        st.markdown("<div class='small-note'>Best order: Resume Builder → Auto Improve → Resume Score → Job Match → 7-Day Plan → Interview.</div>", unsafe_allow_html=True)

    tabs = st.tabs(["Upload CV Audit", "Resume Builder", "Auto Improve", "Resume Score", "Cover Letter", "Job Match", "7-Day Plan", "Interview"]) 

    with tabs[0]:
        st.markdown("<div class='card-title'>Upload your existing CV</div><div class='card-sub'>Audit your current resume, check ATS-style fit, improve it, and see role suggestions.</div>", unsafe_allow_html=True)

        uploaded_cv = st.file_uploader("Upload your CV (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"], key="uploaded_cv")
        uploaded_text = ""
        if uploaded_cv is not None:
            uploaded_text = extract_text_from_upload(uploaded_cv)
            st.session_state["uploaded_resume_text"] = uploaded_text
            if uploaded_text.strip():
                st.success("Resume text extracted successfully.")
            else:
                st.warning("Could not extract text properly. Try a text-based PDF, DOCX, or TXT file.")

        st.text_area("Extracted Resume Text", value=st.session_state.get("uploaded_resume_text", ""), height=220)

        if st.button("Analyze Uploaded CV", key="analyze_uploaded_cv", use_container_width=True):
            resume_text = st.session_state.get("uploaded_resume_text", "")
            if not resume_text.strip():
                st.warning("Please upload a readable resume first.")
            else:
                score, positives, feedback, suggestions, missing = analyze_uploaded_resume(resume_text, jd_text)
                st.session_state["uploaded_resume_score"] = score
                st.session_state["uploaded_positives"] = positives
                st.session_state["uploaded_feedback"] = feedback
                st.session_state["uploaded_suggestions"] = suggestions
                st.session_state["uploaded_missing"] = missing

                rec_roles, not_ideal_roles = suggest_roles_from_resume(resume_text)
                st.session_state["recommended_roles"] = rec_roles
                st.session_state["not_ideal_roles"] = not_ideal_roles

        if st.session_state.get("uploaded_resume_score") is not None:
            st.metric("Uploaded CV ATS Score", f"{st.session_state['uploaded_resume_score']}/100")
            u1, u2 = st.columns(2)
            with u1:
                st.markdown("### What is working")
                for item in st.session_state.get("uploaded_positives", []):
                    st.write(f"- {item}")
                st.markdown("### Suggested roles")
                for item in st.session_state.get("recommended_roles", []):
                    st.write(f"- {item}")
            with u2:
                st.markdown("### What to improve")
                for item in st.session_state.get("uploaded_feedback", []):
                    st.write(f"- {item}")
                st.markdown("### Not ideal right now")
                for item in st.session_state.get("not_ideal_roles", []):
                    st.write(f"- {item}")

            st.markdown("### Exact changes to increase chances")
            for item in st.session_state.get("uploaded_suggestions", []):
                st.write(f"- {item}")

            st.markdown("### Missing keywords from JD")
            for item in st.session_state.get("uploaded_missing", []):
                st.write(f"- {item}")

            if st.button("Generate Improved Version From Uploaded CV", key="improve_uploaded_cv", use_container_width=True):
                resume_text = st.session_state.get("uploaded_resume_text", "")
                if resume_text.strip():
                    if use_ai:
                        try:
                            prompt = f"""
Improve this uploaded resume for better ATS performance and fresher job applications.

Resume:
{resume_text}

Job description:
{jd_text}

Instructions:
- Keep it truthful.
- Rewrite weak bullets.
- Improve summary and experience phrasing.
- Add missing keywords where appropriate.
- Return the improved resume in markdown.
"""
                            improved_uploaded = call_llm("You are an expert ATS resume optimizer.", prompt)
                        except Exception as e:
                            st.error(f"Could not improve uploaded CV: {e}")
                            improved_uploaded = resume_text
                    else:
                        improved_uploaded = resume_text.replace("worked", "executed").replace("helped", "contributed")

                    st.session_state["uploaded_improved_resume"] = improved_uploaded

            st.text_area("Improved Resume Output", value=st.session_state.get("uploaded_improved_resume", ""), height=260)

    with tabs[7]:
        st.markdown("<div class='card-title'>Build your resume</div><div class='card-sub'>Create an ATS-friendly fresher resume in one click.</div>", unsafe_allow_html=True)
        if st.button("Generate Resume", key="generate_resume", use_container_width=True):
            try:
                if use_ai:
                    prompt = f"""
Create an ATS-friendly resume in markdown for this candidate.

Name: {name}
Email: {email}
Phone: {phone}
Location: {location}
Target role: {target_role}
Profile type: {profile_type}
Summary: {summary}
Education: {education}
Experience: {experience}
Projects: {projects}
Certifications: {certifications}
Skills: {skills}

Instructions:
- Optimize for a fresher or early-career candidate.
- Use strong action verbs.
- Keep it concise and professional.
- Do not invent facts.
"""
                    resume_output = call_llm("You are an expert resume writer for freshers and MBA graduates.", prompt)
                else:
                    resume_output = build_resume_fallback(name, email, phone, location, target_role, profile_type, summary, education, experience, skills, projects, certifications)
                st.session_state["resume_output"] = resume_output
            except Exception as e:
                st.error(f"Could not generate resume: {e}")

        resume_output = st.session_state.get("resume_output", "")
        st.text_area("Resume Output", value=resume_output, height=380)
        if resume_output:
            d1, d2 = st.columns(2)
            with d1:
                st.download_button("Download .md", data=resume_output, file_name="resume.md", mime="text/markdown", use_container_width=True)
            with d2:
                if REPORTLAB_AVAILABLE:
                    st.download_button("Download PDF", data=make_pdf_bytes("Resume", resume_output), file_name="resume.pdf", mime="application/pdf", use_container_width=True)

    with tabs[1]:
        st.markdown("<div class='card-title'>Improve weak bullets fast</div><div class='card-sub'>Make your resume more role-aligned and action-oriented.</div>", unsafe_allow_html=True)
        if st.button("Auto Improve My Resume", key="auto_improve", use_container_width=True):
            base_resume = st.session_state.get("resume_output") or build_resume_fallback(name, email, phone, location, target_role, profile_type, summary, education, experience, skills, projects, certifications)
            try:
                if use_ai:
                    prompt = f"""
Improve the following resume for a fresher/early-career candidate targeting {target_role}.

Resume:
{base_resume}

Job description:
{jd_text}

Instructions:
- Rewrite weak bullets to be action-oriented and outcome-focused.
- Add realistic metrics placeholders like (X%, X units, X clients) ONLY if exact numbers are not available.
- Align language with the job description keywords.
- Keep it truthful. Do not invent facts.
- Return improved resume in markdown.
"""
                    improved = call_llm("You are an expert resume optimizer for freshers.", prompt)
                else:
                    improved = base_resume
                    improved = re.sub(r"\bhandled\b", "Managed", improved, flags=re.I)
                    improved = re.sub(r"\bworked on\b", "Executed", improved, flags=re.I)
                    improved = re.sub(r"\bhelped\b", "Contributed to", improved, flags=re.I)
                    improved = improved.replace("- ", "- Led/Executed: ")
                st.session_state["resume_output"] = improved
                st.success("Resume improved. Check the Resume Builder tab output.")
            except Exception as e:
                st.error(f"Could not improve resume: {e}")

        st.text_area("Improved Resume Preview", value=st.session_state.get("resume_output", ""), height=360)

    with tabs[2]:
        st.markdown("<div class='card-title'>Brutally honest resume score</div><div class='card-sub'>Find what is working, what is weak, and what to fix next.</div>", unsafe_allow_html=True)
        if st.button("Score My Resume", key="score_resume", use_container_width=True):
            resume_base = st.session_state.get("resume_output") or build_resume_fallback(name, email, phone, location, target_role, profile_type, summary, education, experience, skills, projects, certifications)
            score, positives, feedback, suggestions = score_resume(resume_base, jd_text, profile_type, skills, experience, projects, target_role)
            st.session_state["resume_score"] = score
            st.session_state["positives"] = positives
            st.session_state["feedback"] = feedback
            st.session_state["suggestions"] = suggestions

        resume_score = st.session_state.get("resume_score")
        if resume_score is not None:
            st.metric("Resume Score", f"{resume_score}/100")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### What is working")
                for item in st.session_state.get("positives", []):
                    st.write(f"- {item}")
            with c2:
                st.markdown("### What to fix next")
                for item in st.session_state.get("suggestions", []):
                    st.write(f"- {item}")
            st.markdown("### Brutal feedback")
            for item in st.session_state.get("feedback", []):
                st.write(f"- {item}")

    with tabs[3]:
        st.markdown("<div class='card-title'>Write a tailored cover letter</div><div class='card-sub'>Make it role-specific without overcomplicating it.</div>", unsafe_allow_html=True)
        if st.button("Generate Cover Letter", key="cover_letter", use_container_width=True):
            try:
                if use_ai:
                    prompt = f"""
Write a concise, personalized cover letter.

Candidate name: {name}
Company: {company}
Role: {target_role}
Profile type: {profile_type}
Candidate summary: {summary}
Education: {education}
Experience: {experience}
Projects: {projects}
Skills: {skills}
Job description: {jd_text}

Instructions:
- Keep it professional and specific.
- Keep it around 250-350 words.
- Make it suitable for a fresher or early-career candidate.
- Do not invent facts.
"""
                    cover_output = call_llm("You are an expert career coach and cover letter writer.", prompt)
                else:
                    cover_output = build_cover_letter_fallback(name, company or "the company", target_role or "the role", summary, skills, jd_text)
                st.session_state["cover_output"] = cover_output
            except Exception as e:
                st.error(f"Could not generate cover letter: {e}")

        cover_output = st.session_state.get("cover_output", "")
        st.text_area("Cover Letter Output", value=cover_output, height=360)
        if cover_output:
            d1, d2 = st.columns(2)
            with d1:
                st.download_button("Download .txt", data=cover_output, file_name="cover_letter.txt", mime="text/plain", use_container_width=True)
            with d2:
                if REPORTLAB_AVAILABLE:
                    st.download_button("Download PDF", data=make_pdf_bytes("Cover Letter", cover_output), file_name="cover_letter.pdf", mime="application/pdf", use_container_width=True)

    with tabs[4]:
        st.markdown("<div class='card-title'>Check job fit</div><div class='card-sub'>Compare your resume against a real JD and identify missing keywords.</div>", unsafe_allow_html=True)
        if st.button("Analyze Job Match", key="job_match", use_container_width=True):
            resume_base = st.session_state.get("resume_output") or build_resume_fallback(name, email, phone, location, target_role, profile_type, summary, education, experience, skills, projects, certifications)
            try:
                if use_ai:
                    prompt = f"""
Analyze how well this candidate fits the job.

Candidate profile/resume:
{resume_base}

Job description:
{jd_text}

Return valid JSON with these keys only:
match_score, matched_skills, missing_skills, suggestions
"""
                    raw = call_llm("You are a hiring analyst. Return only valid JSON.", prompt)
                    raw = raw.strip().replace("```json", "").replace("```", "")
                    parsed = json.loads(raw)
                    score = int(parsed.get("match_score", 0))
                    matched = parsed.get("matched_skills", [])
                    missing = parsed.get("missing_skills", [])
                    suggestions = parsed.get("suggestions", [])
                else:
                    score, matched, missing = estimate_match(resume_base, jd_text)
                    suggestions = [
                        "Add missing keywords from the job description where truthful.",
                        "Rewrite bullets to reflect responsibilities closer to the target role.",
                        "Make one project directly relevant to this job.",
                    ]
                st.session_state["match_score"] = score
                st.session_state["matched"] = matched
                st.session_state["missing"] = missing
                st.session_state["match_suggestions"] = suggestions
            except Exception as e:
                st.error(f"Could not analyze match: {e}")

        match_score = st.session_state.get("match_score")
        if match_score is not None:
            st.metric("Job Match Score", f"{match_score}%")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### Matched skills")
                for item in st.session_state.get("matched", []):
                    st.write(f"- {item}")
            with c2:
                st.markdown("### Missing skills / keywords")
                for item in st.session_state.get("missing", []):
                    st.write(f"- {item}")
            st.markdown("### Fix plan")
            for item in st.session_state.get("match_suggestions", []):
                st.write(f"- {item}")

    with tabs[5]:
        st.markdown("<div class='card-title'>Follow a structured 7-day plan</div><div class='card-sub'>Turn feedback into action instead of endlessly tweaking.</div>", unsafe_allow_html=True)
        if st.button("Generate 7-Day Plan", key="action_plan", use_container_width=True):
            resume_base = st.session_state.get("resume_output") or build_resume_fallback(name, email, phone, location, target_role, profile_type, summary, education, experience, skills, projects, certifications)
            resume_score = st.session_state.get("resume_score")
            if resume_score is None:
                resume_score, _, _, _ = score_resume(resume_base, jd_text, profile_type, skills, experience, projects, target_role)
            missing = st.session_state.get("missing", [])
            st.session_state["action_plan"] = generate_action_plan(target_role, missing, resume_score, profile_type)

        for item in st.session_state.get("action_plan", []):
            st.write(f"- {item}")

    with tabs[6]:
        st.markdown("<div class='card-title'>Practice with interview simulation</div><div class='card-sub'>Generate role-based questions and test your answers.</div>", unsafe_allow_html=True)
        role_for_interview = target_role or "your target role"
        if st.button("Generate Interview Questions", key="interview_questions", use_container_width=True):
            try:
                if use_ai:
                    prompt = f"Generate 5 common interview questions for a fresher applying for {role_for_interview}. Also provide ideal structured answers."
                    output = call_llm("You are an expert interview coach.", prompt)
                else:
                    output = f"""1. Tell me about yourself.\nAnswer: Briefly explain your education, key skills, and interest in {role_for_interview}.\n\n2. Why do you want this role?\nAnswer: Align your interest with the role and company.\n\n3. What are your strengths?\nAnswer: Mention 2 to 3 strengths with examples.\n\n4. Describe a challenge you faced.\nAnswer: Use STAR method (Situation, Task, Action, Result).\n\n5. Why should we hire you?\nAnswer: Connect your skills and willingness to learn with the job."""
                st.session_state["interview_output"] = output
            except Exception as e:
                st.error(f"Error generating questions: {e}")

        st.text_area("Interview Questions & Answers", value=st.session_state.get("interview_output", ""), height=240)
        answer = st.text_area("Practice Answer", key="practice_answer", height=140)
        if st.button("Evaluate My Answer", key="evaluate_interview", use_container_width=True):
            try:
                if use_ai:
                    eval_prompt = f"Evaluate this interview answer for a fresher role.\n\nAnswer:\n{answer}\n\nGive feedback on clarity, structure, confidence, and improvement suggestions."
                    feedback = call_llm("You are an interview coach.", eval_prompt)
                else:
                    feedback = "Your answer is decent. Improve structure using STAR method and be more specific with examples."
                st.session_state["interview_feedback"] = feedback
            except Exception as e:
                st.error(f"Error evaluating answer: {e}")
        if st.session_state.get("interview_feedback"):
            st.markdown("### Feedback")
            st.write(st.session_state["interview_feedback"])


# ---------- Lower sections ----------
st.markdown("---")

c1, c2 = st.columns([1.1, 0.9], gap="large")

with c1:
    st.markdown("<div class='soft-card'><div class='section-title'>📋 Job Application Tracker</div><div class='section-sub'>Track where you applied, current status, and follow-up dates.</div></div>", unsafe_allow_html=True)
    with st.expander("Add New Application", expanded=False):
        app_company = st.text_input("Company", key="app_company")
        app_role = st.text_input("Role", key="app_role")
        app_status = st.selectbox("Status", ["Applied", "Interview", "Rejected", "Offer"], key="app_status")
        app_date = st.date_input("Date Applied", value=date.today(), key="app_date")
        follow_up = st.date_input("Follow-up Date", value=date.today(), key="follow_up")
        if st.button("Add Application", key="add_application", use_container_width=True):
            st.session_state["applications"].append({
                "company": app_company,
                "role": app_role,
                "status": app_status,
                "date": str(app_date),
                "follow_up": str(follow_up),
            })
            st.success("Application added.")

    apps = st.session_state.get("applications", [])
    if apps:
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Applied", len(apps))
        m2.metric("Interviews", len([a for a in apps if a["status"] == "Interview"]))
        m3.metric("Offers", len([a for a in apps if a["status"] == "Offer"]))
        for i, app in enumerate(apps):
            with st.container(border=True):
                a1, a2, a3, a4, a5 = st.columns([1.4, 1.2, 1, 1.1, 0.8])
                a1.write(f"**{app['company']}**")
                a2.write(app["role"])
                a3.write(app["status"])
                a4.write(app["follow_up"])
                if a5.button("Delete", key=f"delete_app_{i}"):
                    st.session_state["applications"].pop(i)
                    st.rerun()
    else:
        st.caption("No applications added yet.")

with c2:
    st.markdown("<div class='soft-card'><div class='section-title'>🧠 Smart Suggestions</div><div class='section-sub'>Quick product-style guidance based on your scores and application activity.</div></div>", unsafe_allow_html=True)
    if st.button("Get Smart Suggestions", key="smart_suggestions", use_container_width=True):
        score = st.session_state.get("resume_score", 0) or 0
        match = st.session_state.get("match_score", 0) or 0
        apps = st.session_state.get("applications", [])
        suggestions = []
        if score < 60:
            suggestions.append("Focus on improving your resume before applying more.")
        if match < 50:
            suggestions.append("You are applying to mismatched roles. Narrow your targeting.")
        if len(apps) < 10:
            suggestions.append("Increase application volume to at least 10 to 15 per week.")
        if len([a for a in apps if a["status"] == "Interview"]) == 0 and len(apps) > 5:
            suggestions.append("Your resume is not converting. Rewrite key bullet points.")
        if not suggestions:
            suggestions.append("You are on the right track. Keep applying and refining.")
        st.session_state["smart_suggestions"] = suggestions

    for item in st.session_state.get("smart_suggestions", []):
        st.write(f"- {item}")


# ---------- Comparison ----------
if st.session_state.get("history"):
    st.markdown("---")
    st.markdown("## Version Comparison")
    history = st.session_state["history"]
    labels = [h["label"] for h in history]
    if len(labels) >= 2:
        s1, s2 = st.columns(2)
        with s1:
            left_choice = st.selectbox("Version A", labels, key="compare_a")
        with s2:
            right_choice = st.selectbox("Version B", labels, index=min(1, len(labels)-1), key="compare_b")
        a = history[labels.index(left_choice)]
        b = history[labels.index(right_choice)]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"### {a['label']}")
            st.write(f"- Resume score: {a.get('resume_score', 'N/A')}")
            st.write(f"- Job match score: {a.get('match_score', 'N/A')}")
            for item in a.get("feedback", [])[:4]:
                st.write(f"- {item}")
        with c2:
            st.markdown(f"### {b['label']}")
            st.write(f"- Resume score: {b.get('resume_score', 'N/A')}")
            st.write(f"- Job match score: {b.get('match_score', 'N/A')}")
            for item in b.get("feedback", [])[:4]:
                st.write(f"- {item}")


# ---------- Feedback ----------
st.markdown("---")
st.markdown("<div class='soft-card'><div class='section-title'>💬 In-App Feedback</div><div class='section-sub'>Collect feedback from early users directly inside the product.</div></div>", unsafe_allow_html=True)

feedback_name = st.text_input("Your Name (optional)", key="feedback_name")
feedback_type = st.selectbox("Feedback Type", ["General", "Bug Report", "Feature Request", "Confusing UX", "What I liked"], key="feedback_type")
feedback_text = st.text_area("Share your feedback", placeholder="What did you like, what felt confusing, what should be improved?", height=130, key="feedback_text")
feedback_rating = st.slider("Overall Rating", min_value=1, max_value=5, value=4, key="feedback_rating")
feedback_recommend = st.radio("Would you recommend this app to a friend?", ["Yes", "No"], horizontal=True, key="feedback_recommend")

f1, f2 = st.columns(2)
with f1:
    if st.button("Submit Feedback", key="submit_feedback", use_container_width=True):
        entry = {
            "name": feedback_name.strip() or "Anonymous",
            "type": feedback_type,
            "text": feedback_text.strip(),
            "rating": feedback_rating,
            "recommend": feedback_recommend,
        }
        if entry["text"]:
            st.session_state["user_feedback_log"].append(entry)
            st.success("Feedback submitted. Thank you.")
        else:
            st.warning("Please write some feedback before submitting.")
with f2:
    if st.button("AI Summarize Feedback", key="summarize_feedback", use_container_width=True):
        logs = st.session_state.get("user_feedback_log", [])
        if not logs:
            st.warning("No feedback submitted yet.")
        else:
            compiled = "\n\n".join([f"Name: {x['name']}\nType: {x['type']}\nFeedback: {x['text']}" for x in logs])
            try:
                if use_ai:
                    prompt = f"""
Summarize the following user feedback for a job-search app.

Feedback entries:
{compiled}

Return:
1. Top recurring positives
2. Top recurring issues
3. Most requested features
4. Product improvement priorities
"""
                    summary = call_llm("You are a product analyst summarizing user feedback.", prompt)
                else:
                    bug_count = len([x for x in logs if x["type"] == "Bug Report"])
                    feature_count = len([x for x in logs if x["type"] == "Feature Request"])
                    confusing_count = len([x for x in logs if x["type"] == "Confusing UX"])
                    like_count = len([x for x in logs if x["type"] == "What I liked"])
                    summary = (
                        f"Feedback entries: {len(logs)}\n"
                        f"What users liked: {like_count}\n"
                        f"Bug reports: {bug_count}\n"
                        f"Feature requests: {feature_count}\n"
                        f"Confusing UX reports: {confusing_count}\n\n"
                        "Priority: Fix repeated UX confusion first, then bug reports, then requested features."
                    )
                st.session_state["feedback_summary"] = summary
            except Exception as e:
                st.error(f"Could not summarize feedback: {e}")

logs = st.session_state.get("user_feedback_log", [])
if logs:
    a, b, c = st.columns(3)
    avg_rating = round(sum(x.get("rating", 0) for x in logs) / len(logs), 1)
    yes_recommend = len([x for x in logs if x.get("recommend") == "Yes"])
    recommend_pct = round((yes_recommend / len(logs)) * 100, 1) if logs else 0
    a.metric("Total Feedback", len(logs))
    b.metric("Average Rating", f"{avg_rating}/5")
    c.metric("Would Recommend", f"{recommend_pct}%")

    export_data = json.dumps(logs, indent=2)
    st.download_button("Export Feedback Log (.json)", data=export_data, file_name="feedback_log.json", mime="application/json")
    for i, entry in enumerate(logs, start=1):
        with st.container(border=True):
            st.write(f"**{i}. {entry['type']}** — {entry['name']}")
            st.write(f"Rating: {entry.get('rating', 'N/A')}/5 | Recommend: {entry.get('recommend', 'N/A')}")
            st.write(entry["text"])

if st.session_state.get("feedback_summary"):
    st.markdown("### AI Feedback Summary")
    st.write(st.session_state["feedback_summary"])


# ---------- Footer ----------
st.markdown("---")
st.markdown("<div class='small-note'>Tip: Add OPENAI_API_KEY in Streamlit secrets and turn on the sidebar toggle to unlock AI-powered generation and feedback.</div>", unsafe_allow_html=True)
