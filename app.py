import os
import re
import json
from typing import List, Tuple
from io import BytesIO

import streamlit as st

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


st.set_page_config(page_title="Fresher Job Cracker AI", page_icon="💼", layout="wide")


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


def build_resume_fallback(
    name: str,
    email: str,
    phone: str,
    location: str,
    target_role: str,
    profile_type: str,
    summary: str,
    education: str,
    experience: str,
    skills: str,
    projects: str,
    certifications: str,
) -> str:
    default_summary_map = {
        "No experience": f"Motivated fresher targeting {target_role} roles with strong learning agility, communication skills, and a structured approach to problem-solving.",
        "Internship only": f"Early-career candidate targeting {target_role} roles with internship exposure, business understanding, and the ability to execute in fast-paced environments.",
        "Career switch": f"Professional transitioning into {target_role} roles with transferable skills, adaptability, and a strong willingness to learn and deliver results.",
        "Experienced": f"Results-oriented candidate targeting {target_role} roles with relevant execution experience, stakeholder handling, and problem-solving skills.",
    }

    resume = f"""# {name}
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
    return resume


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


def score_resume(
    resume_text: str,
    jd_text: str,
    profile_type: str,
    skills_text: str,
    experience_text: str,
    projects_text: str,
    target_role: str,
) -> Tuple[int, List[str], List[str]]:
    score = 35
    feedback = []
    positives = []

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
        positives.append("You have enough experience/internship bullets to work with.")
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

    match_score, matched, missing = estimate_match(resume_text, jd_text)
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

    if profile_type == "No experience" and exp_lines >= 1:
        positives.append("You are using available experience creatively, which is important for freshers.")
    if profile_type == "Career switch":
        feedback.append("As a career switcher, you must highlight transferable achievements more clearly.")

    score = max(0, min(score, 100))

    if score < 55:
        feedback.insert(0, "This resume will likely get rejected in its current form for competitive roles.")
    elif score < 75:
        feedback.insert(0, "This resume is decent but still not strong enough to maximize shortlist chances.")
    else:
        feedback.insert(0, "This resume is in good shape, but a few role-specific improvements can still raise your chances.")

    suggestions = []
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
"):
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
        "education": "PGDM, IMT Nagpur
B.Tech in Food Technology, Institute Name",
        "experience": "Conducted market and competitor analysis for academic and live projects.
Supported quality and operations work during internships.
Managed coordination and communication responsibilities in team-based assignments.",
        "projects": "Built a buyer persona and customer journey framework for a consumer brand.
Created a market analysis and go-to-market recommendation for a business case competition.",
        "certifications": "Advanced Excel
Google Analytics Fundamentals",
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


# ---------- UI ----------
if "history" not in st.session_state:
    st.session_state["history"] = []


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


def delete_history_entry(index: int):
    if 0 <= index < len(st.session_state["history"]):
        st.session_state["history"].pop(index)

st.markdown("""
    <style>
    .main-title {font-size: 2.2rem; font-weight: 700; margin-bottom: 0.2rem;}
    .subtle {color: #6b7280; margin-bottom: 1rem;}
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1200px;}
    div[data-testid=\"stMetricValue\"] {font-size: 2rem;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">💼 Fresher Job Cracker AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtle">Built for freshers and early-career candidates who want clearer guidance, better resumes, and a sharper job strategy.</div>', unsafe_allow_html=True)

if "example_loaded" not in st.session_state:
    st.session_state["example_loaded"] = False

c_top1, c_top2, c_top3 = st.columns([1, 1, 3])
with c_top1:
    if st.button("Load Example Data", use_container_width=True):
        sample = load_example_data()
        for k, v in sample.items():
            st.session_state[k] = v
        st.session_state["example_loaded"] = True
with c_top2:
    if st.button("Clear All", use_container_width=True):
        keys_to_clear = [
            "name", "email", "phone", "location", "target_role", "profile_type", "summary",
            "education", "experience", "projects", "certifications", "skills", "company", "jd_text",
            "resume_output", "resume_score", "positives", "feedback", "suggestions", "cover_output",
            "match_score", "matched", "missing", "match_suggestions", "action_plan"
        ]
        for key in keys_to_clear:
            st.session_state.pop(key, None)
        st.session_state["example_loaded"] = False
with c_top3:
    if st.session_state.get("example_loaded"):
        st.success("Example data loaded. You can now test all tabs quickly.")

c_save1, c_save2 = st.columns([1, 3])
with c_save1:
    if st.button("Save Current Version", use_container_width=True):
        save_current_version(
            name=st.session_state.get("name", name if 'name' in locals() else ''),
            company=st.session_state.get("company", company if 'company' in locals() else ''),
            target_role=st.session_state.get("target_role", target_role if 'target_role' in locals() else ''),
        )
        st.success("Current version saved.")
with c_save2:
    if st.session_state.get("history"):
        st.info(f"Saved versions: {len(st.session_state['history'])}")

with st.sidebar:
    st.header("Settings")
    use_ai = st.toggle("Use OpenAI API", value=False, help="Turn on only after setting OPENAI_API_KEY in your environment.")
    st.markdown("### What makes this different")
    st.markdown(
        "- Fresher-first resume builder
"
        "- Brutally honest resume score
"
        "- Job match + gap diagnosis
"
        "- 7-day action plan"
    )

    st.markdown("---")

# ---------- Job Application Tracker ----------
st.markdown("## 📋 Job Application Tracker")

if "applications" not in st.session_state:
    st.session_state["applications"] = []

with st.expander("Add New Application", expanded=False):
    app_company = st.text_input("Company", key="app_company")
    app_role = st.text_input("Role", key="app_role")
    app_status = st.selectbox("Status", ["Applied", "Interview", "Rejected", "Offer"], key="app_status")
    app_date = st.date_input("Date Applied", key="app_date")
    follow_up = st.date_input("Follow-up Date", key="follow_up")

    if st.button("Add Application", use_container_width=True):
        st.session_state["applications"].append({
            "company": app_company,
            "role": app_role,
            "status": app_status,
            "date": str(app_date),
            "follow_up": str(follow_up)
        })
        st.success("Application added.")

apps = st.session_state.get("applications", [])

if apps:
    st.markdown("### Your Applications")

    for i, app in enumerate(apps):
        c1, c2, c3, c4, c5, c6 = st.columns([2,2,2,2,2,1])
        with c1:
            st.write(app["company"])
        with c2:
            st.write(app["role"])
        with c3:
            st.write(app["status"])
        with c4:
            st.write(app["date"])
        with c5:
            st.write(app["follow_up"])
        with c6:
            if st.button("❌", key=f"del_{i}"):
                st.session_state["applications"].pop(i)
                st.rerun()

    # simple analytics
    total = len(apps)
    interviews = len([a for a in apps if a["status"] == "Interview"])
    offers = len([a for a in apps if a["status"] == "Offer"])

    cA, cB, cC = st.columns(3)
    cA.metric("Total Applied", total)
    cB.metric("Interviews", interviews)
    cC.metric("Offers", offers)

else:
    st.caption("No applications added yet.")

# ---------- Smart Suggestions Engine ----------
st.markdown("---")
st.markdown("## 🧠 Smart Suggestions")

if st.button("Get Smart Suggestions", use_container_width=True):
    score = st.session_state.get("resume_score", 0)
    match = st.session_state.get("match_score", 0)

    suggestions = []

    if score < 60:
        suggestions.append("Focus on improving your resume before applying more.")
    if match < 50:
        suggestions.append("You are applying to mismatched roles. Narrow your targeting.")
    if len(apps) < 10:
        suggestions.append("Increase application volume to at least 10–15 per week.")
    if len([a for a in apps if a["status"] == "Interview"]) == 0 and len(apps) > 5:
        suggestions.append("Your resume is not converting. Rewrite key bullet points.")

    if not suggestions:
        suggestions.append("You are on the right track. Keep applying and refining.")

    for s in suggestions:
        st.write(f"- {s}")

# ---------- In-App User Feedback ----------
st.markdown("---")
st.markdown("## 💬 In-App Feedback")

if "user_feedback_log" not in st.session_state:
    st.session_state["user_feedback_log"] = []

feedback_name = st.text_input("Your Name (optional)", key="feedback_name")
feedback_type = st.selectbox(
    "Feedback Type",
    ["General", "Bug Report", "Feature Request", "Confusing UX", "What I liked"],
    key="feedback_type"
)
feedback_text = st.text_area(
    "Share your feedback",
    placeholder="What did you like, what felt confusing, what should be improved?",
    height=140,
    key="feedback_text"
)
feedback_rating = st.slider("Overall Rating", min_value=1, max_value=5, value=4, key="feedback_rating")
feedback_recommend = st.radio("Would you recommend this app to a friend?", ["Yes", "No"], horizontal=True, key="feedback_recommend")

c_fb1, c_fb2 = st.columns(2)
with c_fb1:
    if st.button("Submit Feedback", use_container_width=True):
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

with c_fb2:
    if st.button("AI Summarize Feedback", use_container_width=True):
        logs = st.session_state.get("user_feedback_log", [])
        if not logs:
            st.warning("No feedback submitted yet.")
        else:
            compiled = "

".join([
                f"Name: {x['name']}
Type: {x['type']}
Feedback: {x['text']}" for x in logs
            ])
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
                        f"Feedback entries: {len(logs)}
"
                        f"What users liked: {like_count}
"
                        f"Bug reports: {bug_count}
"
                        f"Feature requests: {feature_count}
"
                        f"Confusing UX reports: {confusing_count}

"
                        "Priority: Fix repeated UX confusion first, then bug reports, then requested features."
                    )
                st.session_state["feedback_summary"] = summary
            except Exception as e:
                st.error(f"Could not summarize feedback: {e}")

logs = st.session_state.get("user_feedback_log", [])
if logs:
    st.markdown("### Submitted Feedback")

    avg_rating = round(sum(x.get("rating", 0) for x in logs) / len(logs), 1)
    yes_recommend = len([x for x in logs if x.get("recommend") == "Yes"])
    recommend_pct = round((yes_recommend / len(logs)) * 100, 1) if logs else 0

    c_f1, c_f2, c_f3 = st.columns(3)
    c_f1.metric("Total Feedback", len(logs))
    c_f2.metric("Average Rating", f"{avg_rating}/5")
    c_f3.metric("Would Recommend", f"{recommend_pct}%")

    export_data = json.dumps(logs, indent=2)
    st.download_button(
        "Export Feedback Log (.json)",
        data=export_data,
        file_name="feedback_log.json",
        mime="application/json",
        use_container_width=False,
    )

    for i, entry in enumerate(logs, start=1):
        st.write(f"**{i}. {entry['type']}** — {entry['name']}")
        st.write(f"Rating: {entry.get('rating', 'N/A')}/5 | Recommend: {entry.get('recommend', 'N/A')}")
        st.write(entry["text"])

if st.session_state.get("feedback_summary"):
    st.markdown("### AI Feedback Summary")
    st.write(st.session_state["feedback_summary"])

# ---------- Run Info ----------

if st.session_state.get("history"):
    st.markdown("### Version Comparison")
    history = st.session_state["history"]
    labels = [h["label"] for h in history]
    if len(labels) >= 2:
        comp1, comp2 = st.columns(2)
        with comp1:
            left_choice = st.selectbox("Version A", labels, key="compare_a")
        with comp2:
            right_choice = st.selectbox("Version B", labels, index=min(1, len(labels)-1), key="compare_b")

        a = history[labels.index(left_choice)]
        b = history[labels.index(right_choice)]

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"#### {a['label']}")
            st.write(f"- Resume score: {a.get('resume_score', 'N/A')}")
            st.write(f"- Job match score: {a.get('match_score', 'N/A')}")
            if a.get("feedback"):
                st.markdown("**Feedback**")
                for item in a["feedback"][:4]:
                    st.write(f"- {item}")
            if a.get("missing"):
                st.markdown("**Missing keywords**")
                for item in a["missing"][:4]:
                    st.write(f"- {item}")
        with c2:
            st.markdown(f"#### {b['label']}")
            st.write(f"- Resume score: {b.get('resume_score', 'N/A')}")
            st.write(f"- Job match score: {b.get('match_score', 'N/A')}")
            if b.get("feedback"):
                st.markdown("**Feedback**")
                for item in b["feedback"][:4]:
                    st.write(f"- {item}")
            if b.get("missing"):
                st.markdown("**Missing keywords**")
                for item in b["missing"][:4]:
                    st.write(f"- {item}")
    else:
        st.caption("Save at least 2 versions to compare them here.")
    st.markdown("### Saved versions")
    history = st.session_state.get("history", [])
    if history:
        selected_label = st.selectbox("Compare past versions", [h["label"] for h in history])
        selected_index = [h["label"] for h in history].index(selected_label)
        c_hist1, c_hist2 = st.columns(2)
        with c_hist1:
            if st.button("Load Selected", use_container_width=True):
                load_history_entry(history[selected_index])
                st.success("Saved version loaded into the app.")
        with c_hist2:
            if st.button("Delete Selected", use_container_width=True):
                delete_history_entry(selected_index)
                st.success("Saved version deleted.")
    else:
        st.caption("No saved versions yet.")


left, right = st.columns([1, 1])

with left:
    st.subheader("Candidate Details")
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

    summary = st.text_area(
        "Professional Summary",
        value=st.session_state.get("summary", ""),
        placeholder="Recent PGDM graduate targeting sales and account management roles with strong communication, market understanding, and learning agility.",
        height=110,
    )
    education = st.text_area(
        "Education",
        value=st.session_state.get("education", ""),
        placeholder="PGDM, IMT Nagpur\nFood Technology degree, Institute Name",
        height=90,
    )
    experience = st.text_area(
        "Experience / Internships / Responsibilities",
        value=st.session_state.get("experience", ""),
        placeholder="Handled...\nAnalyzed...\nLed...\nImproved...",
        height=140,
    )
    projects = st.text_area(
        "Projects",
        value=st.session_state.get("projects", ""),
        placeholder="Built a market entry analysis...\nCreated a customer persona framework...",
        height=110,
    )
    certifications = st.text_area(
        "Certifications",
        value=st.session_state.get("certifications", ""),
        placeholder="Google Analytics\nAdvanced Excel\nSales training",
        height=80,
    )
    skills = st.text_area(
        "Skills (comma-separated)",
        value=st.session_state.get("skills", ""),
        placeholder="Excel, PowerPoint, Sales, Communication, Market Research, Python",
        height=90,
    )

    st.subheader("Target Job")
    company = st.text_input("Company Name", value=st.session_state.get("company", ""), placeholder="Zomato")
    jd_text = st.text_area(
        "Paste Job Description",
        value=st.session_state.get("jd_text", ""),
        placeholder="Paste the full job description here...",
        height=220,
    )

with right:
    tabs = st.tabs(["Resume Builder", "Auto Improve", "Resume Score", "Cover Letter", "Job Match", "7-Day Plan", "Interview Simulator"])  

    with tabs[0]:
        st.subheader("Fresher-Focused Resume")
        if st.button("Generate Resume", use_container_width=True):
            with st.spinner("Generating resume..."):
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
- If the candidate lacks formal work experience, use internships, projects, academic work, events, leadership, or family business contribution where provided.
- Use strong action verbs.
- Keep it concise and professional.
- Do not invent facts.
"""
                        resume_output = call_llm(
                            "You are an expert resume writer for freshers and MBA graduates.",
                            prompt,
                        )
                    else:
                        resume_output = build_resume_fallback(
                            name, email, phone, location, target_role, profile_type,
                            summary, education, experience, skills, projects, certifications,
                        )
                    st.session_state["resume_output"] = resume_output
                    st.session_state["candidate_name"] = name
                    st.session_state["candidate_company"] = company
                    st.session_state["candidate_target_role"] = target_role
                except Exception as e:
                    st.error(f"Could not generate resume: {e}")

        resume_output = st.session_state.get("resume_output", "")
        st.text_area("Resume Output", value=resume_output, height=420)
        if resume_output:
            c_dl1, c_dl2 = st.columns(2)
            with c_dl1:
                st.download_button(
                    "Download Resume as .md",
                    data=resume_output,
                    file_name="resume.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with c_dl2:
                if REPORTLAB_AVAILABLE:
                    st.download_button(
                        "Download Resume as PDF",
                        data=make_pdf_bytes("Resume", resume_output),
                        file_name="resume.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                else:
                    st.caption("Install reportlab for PDF export.")

    with tabs[1]:
        st.subheader("Auto Resume Improver")
        st.caption("Rewrite weak bullets, add impact, and align with the target job.")

        if st.button("Auto Improve My Resume", use_container_width=True):
            base_resume = st.session_state.get("resume_output") or build_resume_fallback(
                name, email, phone, location, target_role, profile_type,
                summary, education, experience, skills, projects, certifications,
            )
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
                    # Fallback improvement: simple transformations
                    improved = base_resume
                    improved = re.sub(r"handled", "Managed", improved, flags=re.I)
                    improved = re.sub(r"worked on", "Executed", improved, flags=re.I)
                    improved = re.sub(r"helped", "Contributed to", improved, flags=re.I)
                    improved = improved.replace("- ", "- Led/Executed: ")

                st.session_state["resume_output"] = improved
                st.success("Resume improved. Check the Resume Builder tab output.")
            except Exception as e:
                st.error(f"Could not improve resume: {e}")

        st.markdown("---")
        st.subheader("Brutally Honest Resume Score")
        if st.button("Score My Resume", use_container_width=True):
            resume_base = st.session_state.get("resume_output") or build_resume_fallback(
                name, email, phone, location, target_role, profile_type,
                summary, education, experience, skills, projects, certifications,
            )
            score, positives, feedback, suggestions = score_resume(
                resume_text=resume_base,
                jd_text=jd_text,
                profile_type=profile_type,
                skills_text=skills,
                experience_text=experience,
                projects_text=projects,
                target_role=target_role,
            )
            st.session_state["resume_score"] = score
            st.session_state["positives"] = positives
            st.session_state["feedback"] = feedback
            st.session_state["suggestions"] = suggestions

        resume_score = st.session_state.get("resume_score")
        if resume_score is not None:
            st.metric("Resume Score", f"{resume_score}/100")
            st.markdown("### What is working")
            for item in st.session_state.get("positives", []):
                st.write(f"- {item}")
            st.markdown("### Brutal feedback")
            for item in st.session_state.get("feedback", []):
                st.write(f"- {item}")
            st.markdown("### What to fix next")
            for item in st.session_state.get("suggestions", []):
                st.write(f"- {item}")

    with tabs[2]:
        st.subheader("Personalized Cover Letter")
        if st.button("Generate Cover Letter", use_container_width=True):
            with st.spinner("Generating cover letter..."):
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
                        cover_output = call_llm(
                            "You are an expert career coach and cover letter writer.",
                            prompt,
                        )
                    else:
                        cover_output = build_cover_letter_fallback(
                            name=name,
                            company=company or "the company",
                            role=target_role or "the role",
                            summary=summary,
                            strengths=skills,
                            jd_text=jd_text,
                        )
                    st.session_state["cover_output"] = cover_output
                except Exception as e:
                    st.error(f"Could not generate cover letter: {e}")

        cover_output = st.session_state.get("cover_output", "")
        st.text_area("Cover Letter Output", value=cover_output, height=420)
        if cover_output:
            c_dl3, c_dl4 = st.columns(2)
            with c_dl3:
                st.download_button(
                    "Download Cover Letter as .txt",
                    data=cover_output,
                    file_name="cover_letter.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with c_dl4:
                if REPORTLAB_AVAILABLE:
                    st.download_button(
                        "Download Cover Letter as PDF",
                        data=make_pdf_bytes("Cover Letter", cover_output),
                        file_name="cover_letter.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                else:
                    st.caption("Install reportlab for PDF export.")

    with tabs[3]:
        st.subheader("Job Match + Gap Diagnosis")
        if st.button("Analyze Job Match", use_container_width=True):
            resume_base = st.session_state.get("resume_output") or build_resume_fallback(
                name, email, phone, location, target_role, profile_type,
                summary, education, experience, skills, projects, certifications,
            )
            with st.spinner("Analyzing match..."):
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
                        raw = call_llm(
                            "You are a hiring analyst. Return only valid JSON.",
                            prompt,
                        )
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
                matched = st.session_state.get("matched", [])
                if matched:
                    for item in matched:
                        st.write(f"- {item}")
                else:
                    st.write("No strong matches detected yet.")
            with c2:
                st.markdown("### Missing skills / keywords")
                missing = st.session_state.get("missing", [])
                if missing:
                    for item in missing:
                        st.write(f"- {item}")
                else:
                    st.write("No obvious gaps found.")
            st.markdown("### Fix plan")
            for item in st.session_state.get("match_suggestions", []):
                st.write(f"- {item}")

    with tabs[4]:
        st.subheader("7-Day Job Action Plan")
        if st.button("Generate 7-Day Plan", use_container_width=True):
            resume_base = st.session_state.get("resume_output") or build_resume_fallback(
                name, email, phone, location, target_role, profile_type,
                summary, education, experience, skills, projects, certifications,
            )
            resume_score = st.session_state.get("resume_score")
            if resume_score is None:
                resume_score, _, _, _ = score_resume(
                    resume_text=resume_base,
                    jd_text=jd_text,
                    profile_type=profile_type,
                    skills_text=skills,
                    experience_text=experience,
                    projects_text=projects,
                    target_role=target_role,
                )
            missing = st.session_state.get("missing", [])
            plan = generate_action_plan(target_role, missing, resume_score, profile_type)
            st.session_state["action_plan"] = plan

    with tabs[6]:
        st.subheader("Interview Simulator")
        st.caption("Practice common interview questions and get feedback.")

        role_for_interview = target_role or "your target role"

        if st.button("Generate Interview Questions", use_container_width=True):
            try:
                if use_ai:
                    prompt = f"""
Generate 5 common interview questions for a fresher applying for {role_for_interview}.
Also provide ideal structured answers.
"""
                    output = call_llm("You are an expert interview coach.", prompt)
                else:
                    output = f"""
1. Tell me about yourself.
Answer: Briefly explain your education, key skills, and interest in {role_for_interview}.

2. Why do you want this role?
Answer: Align your interest with the role and company.

3. What are your strengths?
Answer: Mention 2-3 strengths with examples.

4. Describe a challenge you faced.
Answer: Use STAR method (Situation, Task, Action, Result).

5. Why should we hire you?
Answer: Connect your skills and willingness to learn with the job.
"""

                st.session_state["interview_output"] = output
            except Exception as e:
                st.error(f"Error generating questions: {e}")

        interview_output = st.session_state.get("interview_output", "")
        st.text_area("Interview Questions & Answers", value=interview_output, height=400)

        st.markdown("### Practice Answer")
        user_answer = st.text_area("Write your answer here", height=150)

        if st.button("Evaluate My Answer", use_container_width=True):
            try:
                if use_ai:
                    eval_prompt = f"""
Evaluate this interview answer for a fresher role.

Answer:
{user_answer}

Give feedback on:
- clarity
- structure
- confidence
- improvement suggestions
"""
                    feedback = call_llm("You are an interview coach.", eval_prompt)
                else:
                    feedback = "Your answer is decent. Improve structure using STAR method and be more specific."

                st.session_state["interview_feedback"] = feedback
            except Exception as e:
                st.error(f"Error evaluating answer: {e}")

        if st.session_state.get("interview_feedback"):
            st.markdown("### Feedback")
            st.write(st.session_state["interview_feedback"])

        plan = st.session_state.get("action_plan", [])
        if plan:
            for item in plan:
                st.write(f"- {item}")


st.markdown("---")
st.markdown("### Run locally")
st.code("pip install streamlit openai reportlab
streamlit run app.py", language="bash")
st.caption("Tip: Set OPENAI_API_KEY in your environment to enable AI generation.")
