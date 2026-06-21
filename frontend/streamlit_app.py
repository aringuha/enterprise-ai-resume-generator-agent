import os
import requests
import streamlit as st

try:
    import pdfplumber
except Exception:
    pdfplumber = None

FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY", "dev-secret-key")

st.set_page_config(
    page_title="Enterprise AI Resume Generator",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 3rem;
      }
      .hero {
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 1rem;
        margin-bottom: 1.25rem;
      }
      .eyebrow {
        color: #2563eb;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
      }
      .hero h1 {
        font-size: 2rem;
        line-height: 1.15;
        margin: 0;
      }
      .hero p {
        color: #4b5563;
        font-size: 1rem;
        margin-top: 0.5rem;
        max-width: 760px;
      }
      .section-title {
        border-top: 1px solid #e5e7eb;
        padding-top: 1.2rem;
        margin-top: 1.4rem;
        margin-bottom: 0.7rem;
      }
      .section-title h2 {
        font-size: 1.25rem;
        margin-bottom: 0.15rem;
      }
      .section-title p {
        color: #6b7280;
        margin-top: 0;
      }
      .status-card {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.85rem 1rem;
        background: #ffffff;
      }
      .status-label {
        color: #6b7280;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
      }
      .status-value {
        color: #111827;
        font-size: 1rem;
        font-weight: 700;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Production-style AI workflow</div>
      <h1>Enterprise AI Resume Generator</h1>
      <p>Build a targeted resume from your profile and a target job description using FastAPI, CrewAI, Ollama, structured JSON, observability, and API security.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "api_base" not in st.session_state:
    st.session_state.api_base = FASTAPI_BASE_URL


def auth_headers(api_key):
    return {"Authorization": f"Bearer {api_key}", "X-API-Key": api_key}


def extract_uploaded_text(uploaded_file, api_base=None, api_key=None):
    if uploaded_file is None:
        return ""
    if api_base and api_key:
        try:
            uploaded_file.seek(0)
            response = requests.post(
                f"{api_base}/api/v1/documents/extract",
                headers=auth_headers(api_key),
                files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                timeout=60,
            )
            response.raise_for_status()
            return response.json().get("text", "")
        except requests.RequestException as exc:
            st.warning(f"Backend extraction failed; trying local text extraction. Details: {exc}")
    if uploaded_file.type == "application/pdf":
        if pdfplumber is None:
            st.warning("PDF upload needs pdfplumber installed. Paste the text manually for now.")
            return ""
        text_parts = []
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text_parts.append(page.extract_text() or "")
        return "\n".join(part for part in text_parts if part).strip()
    return uploaded_file.getvalue().decode("utf-8", errors="ignore").strip()

if not st.session_state.authenticated:
    login_left, login_main, login_right = st.columns([1, 1.35, 1])
    with login_main:
        st.subheader("Secure Login")
        st.caption("Authenticate before accessing resume or job data.")
        login_api_base = st.text_input("FastAPI Base URL", value=st.session_state.api_base)
        login_api_key = st.text_input("Bearer Token / API Key", type="password")
        if st.button("Login", type="primary", use_container_width=True):
            try:
                response = requests.get(
                    f"{login_api_base}/api/v1/auth/validate",
                    headers=auth_headers(login_api_key),
                    timeout=30,
                )
                if response.status_code == 401:
                    st.error("Invalid token or API key.")
                else:
                    response.raise_for_status()
                    st.session_state.authenticated = True
                    st.session_state.api_key = login_api_key
                    st.session_state.api_base = login_api_base
                    st.rerun()
            except requests.ConnectionError:
                st.error("FastAPI is not reachable. Start the backend on port 8000.")
            except requests.Timeout:
                st.error("Login check timed out. Confirm the backend is running.")
            except requests.RequestException as exc:
                st.error(f"Login failed: {exc}")
        st.info("For local development, use dev-secret-key unless you changed .env.")
    st.stop()

with st.sidebar:
    st.header("System")
    st.write("**Agentic Framework:** CrewAI")
    st.write("**Orchestration:** Sequential multi-agent crew")
    st.write("**LLM Runtime:** Ollama")
    st.write("**API:** FastAPI")
    st.write("**Frontend:** Streamlit")
    st.success("Logged in")
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.api_key = ""
        st.rerun()
    api_base = st.text_input("FastAPI Base URL", value=st.session_state.api_base)
    api_key = st.text_input("Bearer Token / API Key", value=st.session_state.api_key or API_KEY, type="password")
    st.session_state.api_base = api_base
    st.session_state.api_key = api_key
    if st.button("Check API Readiness"):
        try:
            ready_response = requests.get(f"{api_base}/ready", timeout=10)
            if ready_response.ok:
                st.success("API is ready")
            else:
                st.warning("API is reachable but not ready")
            st.json(ready_response.json())
        except requests.ConnectionError:
            st.error("FastAPI is not reachable. Start the backend on port 8000.")
        except requests.Timeout:
            st.error("FastAPI readiness check timed out.")
        except requests.RequestException as exc:
            st.error(f"Readiness check failed: {exc}")

status_cols = st.columns(4)
status_items = [
    ("Authentication", "Active"),
    ("Workflow", "2-step intake"),
    ("Security", "Bearer/JWT + API key"),
    ("Output", "Structured JSON"),
]
for col, (label, value) in zip(status_cols, status_items):
    with col:
        st.markdown(
            f"""
            <div class="status-card">
              <div class="status-label">{label}</div>
              <div class="status-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown(
    """
    <div class="section-title">
      <h2>1. Resume Details</h2>
      <p>Upload your resume or enter the core profile fields. Uploaded text can be reviewed and edited before generation.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
resume_mode = st.segmented_control(
    "Resume input method",
    ["Upload resume", "Enter fields"],
    default="Enter fields",
)

uploaded_resume_text = ""
if resume_mode == "Upload resume":
    resume_file = st.file_uploader("Upload resume as PDF, DOCX, TXT, or MD", type=["pdf", "docx", "txt", "md"])
    uploaded_resume_text = extract_uploaded_text(resume_file, api_base, api_key)
    resume_text = st.text_area("Resume text", uploaded_resume_text, height=260)
else:
    resume_text = ""

profile_col1, profile_col2 = st.columns(2)
with profile_col1:
    name = st.text_input("Name", "Arindra Guha")
    email = st.text_input("Email", "arin@example.com")
    phone = st.text_input("Phone", "555-555-5555")
    location = st.text_input("Location", "Cary, NC")
with profile_col2:
    skills_text = st.text_area("Skills, comma-separated", "Python, FastAPI, Streamlit, Ollama, CrewAI, GenAI, Agentic AI, Kafka, Azure, Kubernetes, SQL, Security, Observability")
    summary_default = resume_text[:1200] if resume_text else "Enterprise architect with AI, cloud, distributed systems, API, security, and observability experience."
    summary = st.text_area("Candidate Summary", summary_default, height=140)

st.subheader("Experience, Education, and Projects")
exp_col1, exp_col2 = st.columns(2)
with exp_col1:
    company = st.text_input("Company", "Lockheed Martin")
    title = st.text_input("Title", "Principal Software Engineer")
    years = st.number_input("Years", min_value=0.0, max_value=40.0, value=5.0, step=0.5)
    responsibilities_default = "Built local AI resume generator using Ollama\nDesigned FastAPI endpoints and CrewAI workflow\nImplemented logging, metrics, API authentication, and Streamlit UI"
    if resume_text:
        responsibilities_default = resume_text[:1500]
    responsibilities_text = st.text_area("Responsibilities, one per line", responsibilities_default, height=180)
with exp_col2:
    education_text = st.text_area("Education, one per line", "PhD Electrical Engineering\nMBA")
    certifications_text = st.text_area("Certifications, one per line", "PMP\nAWS Solutions Architect")
    projects_text = st.text_area(
        "Projects, one per line",
        "Enterprise AI Resume Generator | CrewAI, FastAPI, Streamlit, Ollama | Built secure resume generation workflow",
    )

st.markdown(
    """
    <div class="section-title">
      <h2>2. Target Job Details</h2>
      <p>Paste or upload the role description. The ATS agent compares this against the resume details above.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
job_mode = st.segmented_control(
    "Job description input method",
    ["Upload job description", "Paste job description"],
    default="Paste job description",
)
job_description_default = "Requires GenAI, Agentic AI, architecture, governance, APIs, cloud, security, observability, and responsible AI."
if job_mode == "Upload job description":
    job_file = st.file_uploader("Upload job description as PDF, DOCX, TXT, or MD", type=["pdf", "docx", "txt", "md"], key="job_file")
    uploaded_job_text = extract_uploaded_text(job_file, api_base, api_key)
    job_description_default = uploaded_job_text or job_description_default

job_col1, job_col2 = st.columns([1, 2])
with job_col1:
    target_company = st.text_input("Target Company", "Wells Fargo")
    target_title = st.text_input("Target Role", "Principal AI Architect")
with job_col2:
    job_description = st.text_area("Job Description", job_description_default, height=220)

st.markdown(
    """
    <div class="section-title">
      <h2>3. Generate and Review</h2>
      <p>Run the multi-agent workflow and review the generated resume, ATS analysis, and quality review.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.button("Generate Resume", type="primary", use_container_width=True):
    projects = []
    for line in projects_text.splitlines():
        parts = [part.strip() for part in line.split("|")]
        if not parts or not parts[0]:
            continue
        projects.append({
            "name": parts[0],
            "technologies": [tech.strip() for tech in parts[1].split(",")] if len(parts) > 1 else [],
            "description": parts[2] if len(parts) > 2 else parts[0],
            "outcomes": [parts[2]] if len(parts) > 2 else [],
        })

    payload = {
        "candidate_profile": {
            "name": name, "email": email, "phone": phone, "location": location,
            "summary": summary,
            "skills": [s.strip() for s in skills_text.split(",") if s.strip()],
            "experience": [{
                "company": company, "title": title, "years": years,
                "responsibilities": [r.strip() for r in responsibilities_text.splitlines() if r.strip()],
            }],
            "projects": projects,
            "education": [e.strip() for e in education_text.splitlines() if e.strip()],
            "certifications": [c.strip() for c in certifications_text.splitlines() if c.strip()],
        },
        "target_job": {"title": target_title, "company": target_company, "description": job_description},
    }
    try:
        response = requests.post(f"{api_base}/api/v1/resume/generate", json=payload, headers=auth_headers(api_key), timeout=180)
        response.raise_for_status()
        result = response.json()
        export_response = requests.post(
            f"{api_base}/api/v1/resume/export/text",
            json=result,
            headers=auth_headers(api_key),
            timeout=30,
        )
        export_text = export_response.text if export_response.ok else ""
        st.success("Resume generated successfully")

        confidence = result.get("submission_confidence") or {}
        conf_level = confidence.get("level", "N/A")
        conf_pct = confidence.get("percentage", 0)
        conf_submit = confidence.get("should_submit", "N/A")
        conf_color = "green" if conf_level == "HIGH" else "orange" if conf_level == "MEDIUM" else "red"
        st.markdown(
            f'<div style="border:2px solid {conf_color}; border-radius:8px; padding:12px 16px; margin-bottom:16px;">'
            f'<span style="font-size:1.3rem; font-weight:700; color:{conf_color};">'
            f'Submission Confidence: {conf_level} ({conf_pct}%) — {conf_submit}</span><br/>'
            f'<span style="color:#4b5563;">{confidence.get("rationale", "")}</span></div>',
            unsafe_allow_html=True,
        )

        domain_fit = result.get("domain_fit") or {}
        if domain_fit.get("fit_level") == "Weak":
            st.warning(f"**Domain Fit Warning:** {domain_fit.get('recommendation', '')}")
        elif domain_fit.get("fit_level") == "Moderate":
            st.info(f"**Domain Fit:** {domain_fit.get('recommendation', '')}")

        profile_analysis = result.get("profile_analysis") or {}
        if profile_analysis.get("seniority_match") != "Aligned" and profile_analysis.get("seniority_risk_note"):
            st.warning(f"**Seniority Alert:** {profile_analysis['seniority_risk_note']}")

        st.write("**Agentic Framework:**", result.get("agentic_framework"))
        st.write("**LLM Provider:**", result.get("llm_provider"))
        st.write("**Crew Path:**", " → ".join(result.get("crew_execution_path", [])))
        download_col1, download_col2 = st.columns(2)
        with download_col1:
            st.download_button(
                "Download Resume TXT",
                export_text,
                file_name="generated_resume.txt",
                mime="text/plain",
                disabled=not bool(export_text),
                use_container_width=True,
            )
        with download_col2:
            st.download_button(
                "Download Structured JSON",
                response.text,
                file_name="generated_resume.json",
                mime="application/json",
                use_container_width=True,
            )

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Resume", "ATS Analysis", "Gap Analysis", "Review", "Confidence", "Raw JSON"])
        with tab1:
            st.markdown("### Professional Summary")
            st.write(result["resume_content"]["professional_summary"])
            st.markdown("### Skills")
            st.write(", ".join(result["resume_content"]["skills_section"]))
            st.markdown("### Experience Bullets")
            for b in result["resume_content"]["experience_bullets"]:
                st.write(f"- {b}")
            st.markdown("### Projects")
            for project in result["resume_content"]["project_descriptions"]:
                st.write(f"- {project}")
        with tab2:
            ats = result.get("ats_analysis", {})
            breakdown = ats.get("score_breakdown") or {}
            st.metric("ATS Score", f"{ats.get('ats_score', 0)} / 100")
            st.markdown("#### Score Breakdown")
            bd_cols = st.columns(5)
            bd_cols[0].metric("Required Keywords", f"{breakdown.get('required_keyword_score', 0)}/30")
            bd_cols[1].metric("Preferred Keywords", f"{breakdown.get('preferred_keyword_score', 0)}/20")
            bd_cols[2].metric("Quantified Outcomes", f"{breakdown.get('quantified_outcomes_score', 0)}/20")
            bd_cols[3].metric("Title Alignment", f"{breakdown.get('title_alignment_score', 0)}/15")
            bd_cols[4].metric("Education/Creds", f"{breakdown.get('education_credentials_score', 0)}/15")
            st.markdown("#### Required Keywords")
            req_matched = ats.get("matched_required", [])
            req_missing = ats.get("missing_required", [])
            if req_matched:
                st.write("**Matched:** " + ", ".join(req_matched))
            if req_missing:
                st.write("**Missing:** " + ", ".join(req_missing))
            st.markdown("#### Preferred Keywords")
            pref_matched = ats.get("matched_preferred", [])
            pref_missing = ats.get("missing_preferred", [])
            if pref_matched:
                st.write("**Matched:** " + ", ".join(pref_matched))
            if pref_missing:
                st.write("**Missing:** " + ", ".join(pref_missing))
            st.markdown("#### Formatting Suggestions")
            for sug in ats.get("formatting_suggestions", []):
                st.write(f"- {sug}")
            crewai_ats = ats.get("crewai_output")
            if crewai_ats:
                st.markdown("#### CrewAI ATS Agent Output")
                st.write(crewai_ats)
        with tab3:
            gap_items = result.get("gap_analysis", [])
            if gap_items:
                st.markdown("**Category key:** A = Have it, undocumented · B = Adjacent, short course · C = True gap · D = Scale gap · E = Experience gap")
                for g in gap_items:
                    icon = {"A": "🟢", "B": "🟡", "C": "🔴", "D": "🟠", "E": "🔵"}.get(g.get("category", "C"), "⚪")
                    weight_badge = "🔒 Required" if g.get("jd_weight") == "Required" else "💡 Preferred"
                    st.markdown(f"{icon} **{g.get('skill_or_requirement', '')}** — Category {g.get('category', '?')}: {g.get('category_label', '')} ({weight_badge})")
                    st.write(f"  {g.get('recommendation', '')}")
                    if g.get("screening_prep"):
                        st.caption(f"  Screening prep: {g['screening_prep']}")
            else:
                st.success("No significant gaps identified.")
        with tab4:
            review = result.get("review", {})
            st.metric("Professionalism Score", review.get("professionalism_score", 0))
            quant_found = review.get("quantified_outcomes_found", [])
            if review.get("has_quantified_outcomes"):
                st.success(f"Quantified outcomes found: {', '.join(quant_found[:8])}")
            else:
                st.warning("No quantified outcomes detected in resume. Consider adding measurable results.")
            for rec in review.get("recommendations", []):
                st.write(f"- {rec}")
            crewai_review = review.get("crewai_output")
            if crewai_review:
                st.markdown("#### CrewAI Reviewer Output")
                st.write(crewai_review)
        with tab5:
            if confidence:
                st.markdown(f"### Should Submit: **{conf_submit}**")
                st.markdown(f"**Confidence:** {conf_level} ({conf_pct}%)")
                conf_detail_cols = st.columns(2)
                with conf_detail_cols[0]:
                    st.write(f"**Core Match:** {confidence.get('core_match', 'N/A')}")
                    st.write(f"**Domain Fit:** {confidence.get('domain_fit', 'N/A')}")
                    st.write(f"**Seniority Fit:** {confidence.get('seniority_fit', 'N/A')}")
                with conf_detail_cols[1]:
                    st.write(f"**Differentiators:** {confidence.get('differentiators', 'N/A')}")
                    st.write(f"**Meaningful Gaps:** {confidence.get('meaningful_gaps', 'None')}")
                st.markdown("#### Rationale")
                st.write(confidence.get("rationale", ""))
                df = domain_fit
                if df:
                    st.markdown("#### Domain Analysis")
                    st.write(f"**Fit Level:** {df.get('fit_level', 'N/A')}")
                    if df.get("domain_overlap"):
                        st.write(f"**Overlapping terms:** {', '.join(df['domain_overlap'][:15])}")
                    if df.get("domain_gaps"):
                        st.write(f"**Job-specific terms not in profile:** {', '.join(df['domain_gaps'][:15])}")
        with tab6:
            st.json(result)
    except requests.ConnectionError:
        st.error("FastAPI is not reachable. Start the backend with uvicorn on http://127.0.0.1:8000.")
    except requests.Timeout:
        st.error("The request timed out. If Ollama is generating, try again or use a smaller model.")
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else "unknown"
        st.error(f"API returned HTTP {status_code}.")
        if status_code in (401, 403):
            st.info("Check the API key / bearer token. The local development value is dev-secret-key.")
        elif status_code == 503:
            st.info("The API is running but not ready. Start Ollama and pull the configured model.")
        else:
            try:
                st.json(exc.response.json())
            except Exception:
                st.write(exc.response.text if exc.response is not None else str(exc))
    except requests.RequestException as exc:
        st.error(f"API request failed: {exc}")
        st.info("Make sure FastAPI and Ollama are running and the API key is correct.")
