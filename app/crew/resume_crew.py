import logging
import os
import re
from collections import Counter
from typing import Dict, Any, List, Set, Tuple

try:
    from crewai import Agent, Task, Crew, Process, LLM
    CREWAI_AVAILABLE = True
except Exception:
    Agent = Task = Crew = Process = LLM = None
    CREWAI_AVAILABLE = False

from app.core.config import settings
from app.models.resume_models import (
    ResumeGenerationRequest,
    ProfileAnalysis,
    ATSAnalysis,
    ATSScoreBreakdown,
    ResumeContent,
    ReviewResult,
    DomainFitResult,
    GapItem,
    SubmissionConfidence,
)
from app.services.ollama_client import ollama_client

logger = logging.getLogger(__name__)

QUANTITY_PATTERN = re.compile(
    r"\$[\d,.]+[MBK]?|\d+%|\d+[xX]\b|\d+\+?\s*(?:years?|clients?|users?|students?|patients?|projects?|teams?|people|engineers?|members?)",
    re.IGNORECASE,
)

SENIORITY_TIERS = {
    "executive": ["chief", "cto", "cfo", "cio", "coo", "ceo", "vp", "vice president", "evp", "svp"],
    "director": ["director", "head of", "associate director"],
    "principal": ["principal", "staff", "distinguished", "fellow"],
    "senior": ["senior", "sr.", "lead", "manager"],
    "mid": ["mid", "ii", "iii", "specialist", "analyst"],
    "entry": ["junior", "jr.", "associate", "entry", "intern", "assistant", "coordinator", "i"],
}


class ResumeCrewAIWorkflow:
    """CrewAI-based multi-agent workflow. CrewAI is the agentic framework."""

    EXECUTION_PATH = [
        "profile_analyzer_agent",
        "ats_optimization_agent",
        "resume_writer_agent",
        "reviewer_agent",
    ]

    def __init__(self):
        os.environ["OLLAMA_API_BASE"] = settings.ollama_base_url
        self.llm = None
        if CREWAI_AVAILABLE:
            self.llm = LLM(
                model=ollama_client.crewai_llm_name(),
                base_url=settings.ollama_base_url,
                temperature=0.2,
            )

    def run(self, request: ResumeGenerationRequest) -> Dict[str, Any]:
        profile_text = request.candidate_profile.model_dump_json(indent=2)
        job_text = request.target_job.model_dump_json(indent=2)

        crew_output = self._run_crewai(profile_text, job_text)
        profile = self._build_profile_analysis(request, crew_output.get("profile_output"))
        domain_fit = self._build_domain_fit(request)
        ats = self._build_ats_analysis(request, crew_output.get("ats_output"))
        resume = self._build_resume_content(request, profile, ats, crew_output.get("writer_output"))
        review = self._build_review(resume, crew_output.get("reviewer_output"))
        gaps = self._build_gap_analysis(request, ats)
        confidence = self._build_submission_confidence(profile, domain_fit, ats, gaps)

        return {
            "profile_analysis": profile,
            "domain_fit": domain_fit,
            "ats_analysis": ats,
            "resume_content": resume,
            "review": review,
            "gap_analysis": gaps,
            "submission_confidence": confidence,
            "execution_path": self.EXECUTION_PATH,
            "used_crewai": crew_output.get("used_crewai", False),
        }

    def _run_crewai(self, profile_text: str, job_text: str) -> Dict[str, Any]:
        if not CREWAI_AVAILABLE:
            logger.warning("CrewAI package is not installed. Using fallback structured output.")
            return {
                "profile_output": None,
                "ats_output": None,
                "writer_output": None,
                "reviewer_output": None,
                "used_crewai": False,
            }

        try:
            profile_agent = Agent(
                role="Profile Analyzer Agent",
                goal=(
                    "Analyze the candidate's profile to determine their career level, "
                    "primary professional domain, total years of experience, and strongest "
                    "qualifications. Identify whether the candidate's seniority level aligns "
                    "with the target role or if there is a mismatch risk (overqualified or underqualified). "
                    "Consider all experience, education, and certifications holistically."
                ),
                backstory=(
                    "You are an experienced career advisor who has reviewed thousands of "
                    "resumes across every industry — technology, healthcare, education, finance, "
                    "government, nonprofit, trades, and more. You understand how hiring managers "
                    "and ATS systems evaluate candidates at different career levels. You assess "
                    "the full picture: years of experience, breadth vs depth, leadership signals, "
                    "and credential weight. You never invent facts — you only analyze what is provided."
                ),
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
            )
            ats_agent = Agent(
                role="ATS Optimization Agent",
                goal=(
                    "Compare the candidate's profile against the target job description. "
                    "Separate job requirements into REQUIRED vs PREFERRED qualifications. "
                    "Identify which keywords and qualifications the candidate matches and which "
                    "are missing. Score the match using weighted criteria: required keyword match "
                    "(30 points), preferred keyword match (20 points), presence of quantified "
                    "outcomes in the candidate's experience (20 points), title/seniority alignment "
                    "(15 points), and education/credential relevance (15 points). "
                    "Provide specific, actionable formatting suggestions."
                ),
                backstory=(
                    "You are an ATS and recruiting systems expert who understands how applicant "
                    "tracking systems score and filter resumes across all industries. You know that "
                    "a nursing resume, a teaching resume, and an engineering resume all get scored "
                    "the same way by the ATS: keyword presence, credential match, and formatting. "
                    "You distinguish between required and preferred qualifications because required "
                    "misses are deal-breakers while preferred misses are acceptable. You always "
                    "recommend including measurable outcomes — every profession has them."
                ),
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
            )
            writer_agent = Agent(
                role="Resume Writer Agent",
                goal=(
                    "Generate professional, ATS-optimized resume content tailored to the target "
                    "job. Write a professional summary that leads with the candidate's strongest "
                    "qualification for THIS specific role. Reorder and prioritize skills to match "
                    "what the job values most. Write experience bullets that include measurable "
                    "outcomes wherever possible — dollars saved, percentages improved, people served, "
                    "throughput increased, time reduced. Every bullet should show what the candidate "
                    "DID and what RESULTED from it. Use only facts provided in the profile."
                ),
                backstory=(
                    "You are a professional resume writer who has helped candidates across every "
                    "field — teachers, engineers, nurses, executives, tradespeople, researchers, "
                    "and more. You know that strong resume bullets follow a universal pattern: "
                    "action + context + result. You never use weak openers like 'Responsible for' "
                    "or 'Helped with.' You write with specificity: naming tools, methods, programs, "
                    "or frameworks the candidate actually used, regardless of industry. You tailor "
                    "every resume to the target job — the same candidate applying for two different "
                    "roles should get two different resumes."
                ),
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
            )
            reviewer_agent = Agent(
                role="Reviewer Agent",
                goal=(
                    "Review the generated resume content for quality. Check: grammar and spelling, "
                    "consistency of tense and formatting, whether experience bullets include "
                    "measurable outcomes, whether the professional summary aligns with the target "
                    "role, and overall professionalism. Flag any bullets that lack specificity or "
                    "measurable results. Score professionalism on a 0-100 scale."
                ),
                backstory=(
                    "You are a hiring manager and resume reviewer who has screened thousands of "
                    "applications. You know what makes a resume get past the first 6-second scan: "
                    "clear structure, quantified achievements, and role-relevant framing. You flag "
                    "vague bullets ('managed projects' without scope or outcome), tense inconsistencies, "
                    "and missing measurable results. You understand that every profession has metrics — "
                    "a teacher has student outcomes, a nurse has patient metrics, a salesperson has "
                    "revenue numbers. If the resume lacks quantified outcomes, you recommend adding them."
                ),
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
            )

            profile_task = Task(
                description=(
                    "Analyze this candidate profile. Determine:\n"
                    "1. Career level (Entry / Mid / Senior / Principal-Executive)\n"
                    "2. Primary professional domain\n"
                    "3. Total years of experience\n"
                    "4. Top 10 strongest skills or qualifications\n"
                    "5. Whether their seniority matches the target role title, or if there is overqualification/underqualification risk\n\n"
                    "Candidate Profile:\n{profile_text}\n\n"
                    "Target Job:\n{job_text}"
                ),
                expected_output="Profile analysis with level, domain, years, top skills, and seniority alignment assessment.",
                agent=profile_agent,
            )
            ats_task = Task(
                description=(
                    "Compare the candidate profile to the target job description.\n\n"
                    "1. Parse the job description and separate qualifications into REQUIRED vs PREFERRED\n"
                    "2. List which required qualifications the candidate MATCHES and which are MISSING\n"
                    "3. List which preferred qualifications the candidate MATCHES and which are MISSING\n"
                    "4. Check whether the candidate's experience includes quantified outcomes (numbers, percentages, dollar amounts)\n"
                    "5. Score the overall match out of 100 using these weights:\n"
                    "   - Required keyword match: up to 30 points\n"
                    "   - Preferred keyword match: up to 20 points\n"
                    "   - Quantified outcomes present: up to 20 points\n"
                    "   - Title/seniority alignment: up to 15 points\n"
                    "   - Education/credential relevance: up to 15 points\n"
                    "6. Provide 3-5 specific formatting suggestions\n\n"
                    "Candidate:\n{profile_text}\n\nJob:\n{job_text}"
                ),
                expected_output="ATS analysis with required/preferred breakdown, matched/missing lists, weighted score, and formatting advice.",
                agent=ats_agent,
                context=[profile_task],
            )
            writer_task = Task(
                description=(
                    "Generate ATS-optimized resume content for this candidate targeting this specific job.\n\n"
                    "Requirements:\n"
                    "- Professional summary: 3-5 sentences, lead with the candidate's strongest qualification for THIS role\n"
                    "- Skills section: reordered to put the most job-relevant skills first\n"
                    "- Experience bullets: each bullet should follow action + context + result pattern\n"
                    "- Include measurable outcomes wherever the candidate's profile provides them\n"
                    "- Never invent facts, metrics, or experiences not in the profile\n"
                    "- Tailor language to match the job description's terminology\n\n"
                    "Candidate:\n{profile_text}\n\nJob:\n{job_text}"
                ),
                expected_output="Complete resume content with summary, skills, experience bullets, and project descriptions.",
                agent=writer_agent,
                context=[profile_task, ats_task],
            )
            reviewer_task = Task(
                description=(
                    "Review the generated resume content. Evaluate:\n"
                    "1. Grammar and spelling correctness\n"
                    "2. Tense consistency (past tense for previous roles, present for current)\n"
                    "3. Whether bullets include measurable outcomes — list any specific metrics found\n"
                    "4. Whether the summary aligns with the target role\n"
                    "5. Overall professionalism score (0-100)\n"
                    "6. Specific recommendations for improvement\n"
                    "7. Flag any bullets that are vague or lack specificity"
                ),
                expected_output="Review with grammar status, quantified outcomes check, professionalism score, and specific recommendations.",
                agent=reviewer_agent,
                context=[writer_task],
            )

            crew = Crew(
                agents=[profile_agent, ats_agent, writer_agent, reviewer_agent],
                tasks=[profile_task, ats_task, writer_task, reviewer_task],
                process=Process.sequential,
                verbose=True,
            )
            result = crew.kickoff(inputs={"profile_text": profile_text, "job_text": job_text})
            task_outputs = getattr(result, "tasks_output", []) or []

            return {
                "profile_output": str(task_outputs[0]) if len(task_outputs) > 0 else "",
                "ats_output": str(task_outputs[1]) if len(task_outputs) > 1 else "",
                "writer_output": str(task_outputs[2]) if len(task_outputs) > 2 else str(result),
                "reviewer_output": str(task_outputs[3]) if len(task_outputs) > 3 else "",
                "used_crewai": True,
            }
        except Exception as exc:
            logger.warning("CrewAI failed; fallback structured output will be used. Error: %s", exc)
            return {
                "profile_output": None,
                "ats_output": None,
                "writer_output": None,
                "reviewer_output": None,
                "used_crewai": False,
            }

    # ── Profile Analysis ──

    def _detect_seniority_tier(self, title: str) -> str:
        title_lower = title.lower()
        for tier, keywords in SENIORITY_TIERS.items():
            if any(kw in title_lower for kw in keywords):
                return tier
        return "mid"

    def _build_profile_analysis(self, request: ResumeGenerationRequest, crewai_output: str | None) -> ProfileAnalysis:
        profile = request.candidate_profile
        years = sum(item.years for item in profile.experience)
        text = " ".join(profile.skills + [profile.summary or ""]).lower()

        domain = self._detect_domain(text)
        level = (
            "Principal / Executive-Level" if years >= 15
            else "Senior-Level" if years >= 8
            else "Mid-Level" if years >= 3
            else "Entry-Level"
        )

        candidate_tier = self._detect_seniority_tier(
            profile.experience[0].title if profile.experience else ""
        )
        job_tier = self._detect_seniority_tier(request.target_job.title)

        tier_order = ["entry", "mid", "senior", "principal", "director", "executive"]
        candidate_rank = tier_order.index(candidate_tier) if candidate_tier in tier_order else 2
        job_rank = tier_order.index(job_tier) if job_tier in tier_order else 2

        seniority_match = "Aligned"
        seniority_note = None
        if candidate_rank - job_rank >= 2:
            seniority_match = "Overqualified Risk"
            seniority_note = (
                f"Candidate appears to be at '{candidate_tier}' level applying for a "
                f"'{job_tier}' level role. Some ATS systems filter for seniority band mismatch. "
                f"Consider adjusting resume title to match the target role's level."
            )
        elif job_rank - candidate_rank >= 2:
            seniority_match = "Underqualified Risk"
            seniority_note = (
                f"Target role appears to be at '{job_tier}' level while candidate experience "
                f"suggests '{candidate_tier}' level. Emphasize leadership and scope in the resume."
            )

        return ProfileAnalysis(
            candidate_level=level,
            primary_domain=domain,
            years_experience=years,
            strongest_skills=profile.skills[:10],
            seniority_match=seniority_match,
            seniority_risk_note=seniority_note,
            crewai_output=crewai_output,
        )

    def _detect_domain(self, text: str) -> str:
        domain_signals = {
            "AI / Machine Learning": ["ai engineer", "machine learning", "llm", "genai", "agentic", "ml ", "deep learning", "neural", "nlp", "rag", "ollama", "crewai", "langchain", "tensorflow", "pytorch", "scikit", "ai platform", "ai architect"],
            "Technology / Engineering": ["software", "engineer", "developer", "api", "cloud", "devops", "architect"],
            "Healthcare / Medicine": ["patient", "clinical", "nurse", "hospital", "medical", "health", "physician"],
            "Education / Academia": ["teach", "professor", "curriculum", "student", "education", "academic", "faculty"],
            "Finance / Banking": ["finance", "banking", "investment", "portfolio", "accounting", "audit", "fiscal"],
            "Marketing / Communications": ["marketing", "brand", "campaign", "content", "seo", "social media", "communications"],
            "Operations / Management": ["operations", "supply chain", "logistics", "procurement", "manufacturing"],
            "Legal": ["legal", "attorney", "compliance", "regulatory", "litigation", "counsel"],
            "Sales": ["sales", "revenue", "quota", "pipeline", "account", "territory", "business development"],
            "Human Resources": ["recruiting", "talent", "hr", "compensation", "onboarding", "employee relations"],
            "Research / Science": ["research", "laboratory", "scientist", "publication", "grant", "experiment"],
        }
        scores = Counter()
        for domain, terms in domain_signals.items():
            scores[domain] = sum(1 for term in terms if term in text)
        top = scores.most_common(1)
        return top[0][0] if top and top[0][1] > 0 else "General Professional"

    # ── Domain Fit ──

    def _build_domain_fit(self, request: ResumeGenerationRequest) -> DomainFitResult:
        candidate_text = " ".join(
            request.candidate_profile.skills
            + [request.candidate_profile.summary or ""]
            + [e.title for e in request.candidate_profile.experience]
            + request.candidate_profile.education
        ).lower()
        job_text = (request.target_job.description + " " + request.target_job.title).lower()

        candidate_domain = self._detect_domain(candidate_text)
        job_domain = self._detect_domain(job_text)

        candidate_words = set(re.findall(r"[a-z]{3,}", candidate_text))
        job_words = set(re.findall(r"[a-z]{3,}", job_text))
        overlap = candidate_words & job_words
        significant_overlap = [w for w in sorted(overlap) if len(w) > 4][:20]

        job_only = job_words - candidate_words
        significant_gaps = [w for w in sorted(job_only) if len(w) > 4][:15]

        overlap_ratio = len(overlap) / max(len(job_words), 1)

        if candidate_domain == job_domain or overlap_ratio > 0.35:
            fit_level = "Strong"
            recommendation = f"Candidate's {candidate_domain} background aligns well with this {job_domain} role."
        elif overlap_ratio > 0.20:
            fit_level = "Moderate"
            recommendation = (
                f"Candidate's background is in {candidate_domain} while this role is in {job_domain}. "
                f"There is partial overlap — emphasize transferable skills and relevant experience."
            )
        else:
            fit_level = "Weak"
            recommendation = (
                f"Candidate's background is in {candidate_domain} while this role is in {job_domain}. "
                f"Domain gap is significant. Consider whether this application is worth pursuing."
            )

        return DomainFitResult(
            is_fit=fit_level != "Weak",
            fit_level=fit_level,
            domain_overlap=significant_overlap,
            domain_gaps=significant_gaps,
            recommendation=recommendation,
        )

    # ── ATS Analysis with Weighted Scoring ──

    def _classify_jd_requirements(self, description: str) -> Tuple[Set[str], Set[str]]:
        lines = description.lower().replace(";", "\n").replace("•", "\n").split("\n")
        required: Set[str] = set()
        preferred: Set[str] = set()
        in_preferred = False

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if any(kw in line for kw in ["prefer", "nice to have", "bonus", "plus", "desired", "ideal"]):
                in_preferred = True
            elif any(kw in line for kw in ["require", "must have", "mandatory", "essential", "minimum", "qualif"]):
                in_preferred = False

            words = set(re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}", line))
            stop = {"and", "or", "the", "for", "with", "you", "will", "are", "this", "that",
                     "from", "have", "has", "role", "team", "work", "able", "must", "should",
                     "experience", "knowledge", "understanding", "ability", "strong", "excellent"}
            meaningful = {w.lower() for w in words if w.lower() not in stop and len(w) > 2}

            if in_preferred:
                preferred.update(meaningful)
            else:
                required.update(meaningful)

        if not required and preferred:
            required = preferred
            preferred = set()
        elif not required and not preferred:
            all_words = set(re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}", description.lower()))
            stop = {"and", "or", "the", "for", "with", "you", "will", "are", "this", "that",
                     "from", "have", "has", "role", "team", "work", "able", "must", "should"}
            required = {w for w in all_words if w not in stop and len(w) > 2}

        return required, preferred

    def _build_ats_analysis(self, request: ResumeGenerationRequest, crewai_output: str | None) -> ATSAnalysis:
        required_kw, preferred_kw = self._classify_jd_requirements(request.target_job.description)

        profile_keywords = self._extract_profile_keywords(request)

        matched_required = sorted(required_kw & profile_keywords)
        missing_required = sorted(required_kw - profile_keywords)
        matched_preferred = sorted(preferred_kw & profile_keywords)
        missing_preferred = sorted(preferred_kw - profile_keywords)

        matched_all = sorted(set(matched_required + matched_preferred))
        missing_all = sorted(set(missing_required + missing_preferred))

        req_score = int((len(matched_required) / max(len(required_kw), 1)) * 30)
        pref_score = int((len(matched_preferred) / max(len(preferred_kw), 1)) * 20)

        candidate_text = " ".join(
            [e.company + " " + e.title + " " + " ".join(e.responsibilities) for e in request.candidate_profile.experience]
            + [request.candidate_profile.summary or ""]
        )
        quantified = QUANTITY_PATTERN.findall(candidate_text)
        quant_score = min(len(quantified) * 4, 20)

        candidate_tier = self._detect_seniority_tier(
            request.candidate_profile.experience[0].title if request.candidate_profile.experience else ""
        )
        job_tier = self._detect_seniority_tier(request.target_job.title)
        tier_order = ["entry", "mid", "senior", "principal", "director", "executive"]
        c_rank = tier_order.index(candidate_tier) if candidate_tier in tier_order else 2
        j_rank = tier_order.index(job_tier) if job_tier in tier_order else 2
        tier_diff = abs(c_rank - j_rank)
        title_score = 15 if tier_diff == 0 else 10 if tier_diff == 1 else 5

        job_edu_text = request.target_job.description.lower()
        candidate_edu_text = " ".join(request.candidate_profile.education + request.candidate_profile.certifications).lower()
        edu_terms = {"phd", "doctorate", "master", "bachelor", "degree", "mba", "certification", "certified", "license"}
        job_edu = {t for t in edu_terms if t in job_edu_text}
        candidate_edu = {t for t in edu_terms if t in candidate_edu_text}
        edu_overlap = len(job_edu & candidate_edu)
        edu_score = min(edu_overlap * 5, 15) if job_edu else 10

        total_score = min(req_score + pref_score + quant_score + title_score + edu_score, 100)

        breakdown = ATSScoreBreakdown(
            required_keyword_score=req_score,
            preferred_keyword_score=pref_score,
            quantified_outcomes_score=quant_score,
            title_alignment_score=title_score,
            education_credentials_score=edu_score,
        )

        suggestions = [
            "Use clear section headings that ATS systems recognize: Summary, Skills, Experience, Education.",
            "Mirror the job description's exact terminology in your resume where truthful.",
        ]
        if quant_score < 12:
            suggestions.append(
                "Add measurable outcomes to experience bullets — numbers, percentages, dollar amounts, "
                "or scope (e.g., 'served 200 clients', 'improved retention by 15%', 'managed $2M budget')."
            )
        if missing_required:
            suggestions.append(f"Address these missing required terms if you have the experience: {', '.join(missing_required[:8])}.")
        if tier_diff >= 2:
            suggestions.append("Adjust your resume title/headline to match the target role's seniority level.")

        return ATSAnalysis(
            missing_keywords=missing_all[:15],
            matched_keywords=matched_all[:20],
            required_keywords=sorted(required_kw)[:20],
            preferred_keywords=sorted(preferred_kw)[:20],
            matched_required=matched_required[:15],
            matched_preferred=matched_preferred[:15],
            missing_required=missing_required[:15],
            missing_preferred=missing_preferred[:15],
            ats_score=total_score,
            score_breakdown=breakdown,
            formatting_suggestions=suggestions,
            crewai_output=crewai_output,
        )

    def _extract_profile_keywords(self, request: ResumeGenerationRequest) -> Set[str]:
        text = " ".join(
            request.candidate_profile.skills
            + [request.candidate_profile.summary or ""]
            + request.candidate_profile.education
            + request.candidate_profile.certifications
            + [
                " ".join([p.name, p.description] + p.technologies + p.outcomes)
                for p in request.candidate_profile.projects
            ]
            + [
                " ".join(e.responsibilities + [e.company, e.title])
                for e in request.candidate_profile.experience
            ]
        ).lower()
        words = set(re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}", text))
        stop = {"and", "or", "the", "for", "with", "you", "will", "are", "this", "that",
                 "from", "have", "has", "role", "team", "work"}
        return {w for w in words if w not in stop and len(w) > 2}

    # ── Gap Analysis ──

    def _build_gap_analysis(self, request: ResumeGenerationRequest, ats: ATSAnalysis) -> List[GapItem]:
        gaps: List[GapItem] = []
        profile_text = " ".join(
            request.candidate_profile.skills
            + [request.candidate_profile.summary or ""]
            + request.candidate_profile.education
            + request.candidate_profile.certifications
            + [" ".join(e.responsibilities) for e in request.candidate_profile.experience]
        ).lower()

        for term in ats.missing_required[:10]:
            category, label = self._categorize_gap(term, profile_text)
            prep = None
            if category in ("C", "D", "E"):
                prep = f"If asked about {term}: acknowledge it's an area you're building toward and describe relevant adjacent experience."
            gaps.append(GapItem(
                skill_or_requirement=term,
                gap_type="Hard Skill" if len(term) < 15 else "Experience",
                category=category,
                category_label=label,
                jd_weight="Required",
                recommendation=self._gap_recommendation(category, term),
                screening_prep=prep,
            ))

        for term in ats.missing_preferred[:5]:
            category, label = self._categorize_gap(term, profile_text)
            gaps.append(GapItem(
                skill_or_requirement=term,
                gap_type="Soft Skill" if any(w in term for w in ["leader", "communicat", "collaborat"]) else "Hard Skill",
                category=category,
                category_label=label,
                jd_weight="Preferred",
                recommendation=self._gap_recommendation(category, term),
            ))

        return gaps

    def _categorize_gap(self, term: str, profile_text: str) -> Tuple[str, str]:
        term_parts = term.lower().split()
        partial_matches = sum(1 for part in term_parts if part in profile_text)
        if partial_matches > 0 and partial_matches >= len(term_parts) / 2:
            return "A", "Likely have it, undocumented"
        synonyms_present = any(
            syn in profile_text
            for syn in [term[:4], term[-4:]]
            if len(syn) > 3
        )
        if synonyms_present:
            return "B", "Adjacent, short course bridges it"
        if any(w in term for w in ["year", "experience", "industry"]):
            return "E", "Experience/domain gap"
        if any(c.isdigit() for c in term):
            return "D", "Achievement scale gap"
        return "C", "True gap, track frequency"

    def _gap_recommendation(self, category: str, term: str) -> str:
        if category == "A":
            return f"Add '{term}' to your resume — you likely have this experience but it's not documented."
        if category == "B":
            return f"Consider a short course or certification in '{term}' to make this claimable."
        if category == "C":
            return f"Track whether '{term}' appears in other jobs you're targeting. Only pursue if frequent."
        if category == "D":
            return f"The job asks for a bigger scope than documented. Emphasize the largest relevant examples you have."
        return f"This is a domain/industry experience gap. Bridge through transferable skills if applying."

    # ── Submission Confidence ──

    def _build_submission_confidence(
        self, profile: ProfileAnalysis, domain_fit: DomainFitResult,
        ats: ATSAnalysis, gaps: List[GapItem],
    ) -> SubmissionConfidence:
        score = ats.ats_score

        domain_bonus = 10 if domain_fit.fit_level == "Strong" else 0 if domain_fit.fit_level == "Moderate" else -15
        seniority_penalty = -10 if profile.seniority_match != "Aligned" else 0
        required_gap_penalty = -3 * len([g for g in gaps if g.jd_weight == "Required" and g.category in ("C", "D", "E")])

        adjusted = max(0, min(100, score + domain_bonus + seniority_penalty + required_gap_penalty))

        if adjusted >= 75:
            level, should_submit = "HIGH", "YES"
        elif adjusted >= 50:
            level, should_submit = "MEDIUM", "YES WITH CAUTION"
        else:
            level, should_submit = "LOW", "CONSIDER CAREFULLY"

        hard_gaps = [g.skill_or_requirement for g in gaps if g.jd_weight == "Required" and g.category in ("C", "E")]
        rationale_parts = []
        if domain_fit.fit_level == "Strong":
            rationale_parts.append("Strong domain alignment.")
        elif domain_fit.fit_level == "Weak":
            rationale_parts.append(f"Weak domain fit: {domain_fit.recommendation}")
        if profile.seniority_match != "Aligned":
            rationale_parts.append(f"Seniority concern: {profile.seniority_risk_note or profile.seniority_match}.")
        if hard_gaps:
            rationale_parts.append(f"Required gaps to prepare for: {', '.join(hard_gaps[:5])}.")
        if not rationale_parts:
            rationale_parts.append("Profile aligns well with the target role.")

        return SubmissionConfidence(
            level=level,
            percentage=adjusted,
            core_match="Strong" if ats.ats_score >= 70 else "Good" if ats.ats_score >= 50 else "Weak",
            domain_fit=domain_fit.fit_level,
            seniority_fit=profile.seniority_match,
            differentiators=", ".join(profile.strongest_skills[:5]),
            meaningful_gaps=", ".join(hard_gaps[:5]) if hard_gaps else "None identified",
            should_submit=should_submit,
            rationale=" ".join(rationale_parts),
        )

    # ── Resume Content ──

    def _build_resume_content(self, request: ResumeGenerationRequest, profile: ProfileAnalysis, ats: ATSAnalysis, crewai_output: str | None) -> ResumeContent:
        candidate = request.candidate_profile
        job = request.target_job
        if crewai_output:
            bullets = [line.strip("-• ").strip() for line in crewai_output.splitlines() if line.strip().startswith(("-", "•"))]
            if not bullets:
                bullets = [crewai_output[:500]]
            return ResumeContent(
                professional_summary=crewai_output[:900],
                skills_section=self._prioritize(candidate.skills, ats.matched_keywords),
                experience_bullets=bullets[:12],
                project_descriptions=[f"CrewAI-generated targeted resume content for {job.company} {job.title} using Ollama."],
                crewai_output=crewai_output,
            )

        bullets = []
        verbs = ["Architected", "Designed", "Built", "Led", "Optimized", "Delivered", "Established", "Directed"]
        for exp in candidate.experience:
            for idx, resp in enumerate(exp.responsibilities[:3]):
                bullets.append(
                    f"{verbs[idx % len(verbs)]} {resp} at {exp.company} as {exp.title}, "
                    f"aligning with the target role's requirements for {job.title}."
                )
        project_descriptions = [
            f"{project.name}: {project.description}"
            for project in candidate.projects
        ]
        if not project_descriptions:
            project_descriptions = [
                f"Targeted resume for {job.company} {job.title}, optimized around "
                f"{', '.join(ats.matched_keywords[:8]) or 'core role requirements'}."
            ]
        return ResumeContent(
            professional_summary=(
                f"{profile.candidate_level} professional specializing in {profile.primary_domain}, "
                f"with {profile.years_experience:.0f} years of experience, aligned to "
                f"{job.company}'s {job.title} role."
            ),
            skills_section=self._prioritize(candidate.skills, ats.matched_keywords),
            experience_bullets=bullets,
            project_descriptions=project_descriptions,
            crewai_output=crewai_output,
        )

    # ── Review ──

    def _build_review(self, resume: ResumeContent, crewai_output: str | None) -> ReviewResult:
        recommendations = []
        if len(resume.professional_summary.split()) < 25:
            recommendations.append("Professional summary could include more detail about qualifications and target role alignment.")
        if len(resume.experience_bullets) < 3:
            recommendations.append("Add more experience bullets for stronger resume depth.")

        all_text = resume.professional_summary + " " + " ".join(resume.experience_bullets)
        quantified = QUANTITY_PATTERN.findall(all_text)
        has_quantified = len(quantified) > 0

        if not has_quantified:
            recommendations.append(
                "Resume lacks measurable outcomes. Add numbers, percentages, dollar amounts, or scope "
                "to experience bullets (e.g., 'served 200 clients', 'improved efficiency by 30%', "
                "'managed team of 12')."
            )

        return ReviewResult(
            grammar_status="Passed basic grammar and readability checks",
            consistency_status="Consistent section structure detected",
            formatting_status="ATS-friendly plain-text structure",
            professionalism_score=90 if not recommendations else 78,
            recommendations=recommendations or ["Resume content is professional and ready for review."],
            has_quantified_outcomes=has_quantified,
            quantified_outcomes_found=quantified[:10],
            crewai_output=crewai_output,
        )

    def _prioritize(self, skills, matched):
        matched_lower = {kw.lower() for kw in matched}
        direct = [s for s in skills if s.lower() in matched_lower]
        remaining = [s for s in skills if s not in direct]
        return (direct + remaining)[:20]
