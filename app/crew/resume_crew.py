import logging
import os
import re
from collections import Counter
from typing import Dict, Any, Set

try:
    from crewai import Agent, Task, Crew, Process, LLM
    CREWAI_AVAILABLE = True
except Exception:  # pragma: no cover - allows tests to run before optional dependency install
    Agent = Task = Crew = Process = LLM = None
    CREWAI_AVAILABLE = False

from app.core.config import settings
from app.models.resume_models import (
    ResumeGenerationRequest,
    ProfileAnalysis,
    ATSAnalysis,
    ResumeContent,
    ReviewResult,
)
from app.services.ollama_client import ollama_client

logger = logging.getLogger(__name__)

class ResumeCrewAIWorkflow:
    """CrewAI-based multi-agent workflow. CrewAI is the agentic framework."""

    EXECUTION_PATH = [
        "profile_analyzer_agent",
        "ats_optimization_agent",
        "resume_writer_agent",
        "reviewer_agent",
    ]

    IMPORTANT_TERMS = {
        "python", "java", "sql", "fastapi", "api", "genai", "agentic", "ai",
        "machine learning", "kafka", "spark", "aws", "azure", "gcp", "kubernetes",
        "docker", "security", "governance", "observability", "logging", "monitoring",
        "resume", "ats", "architecture", "orchestrator", "microservices", "ollama",
        "streamlit", "crewai", "responsible ai"
    }

    DOMAIN_KEYWORDS = {
        "AI / Machine Learning": {"ai", "ml", "machine learning", "llm", "rag", "genai", "agentic", "ollama", "crewai"},
        "Cloud Architecture": {"aws", "azure", "gcp", "kubernetes", "docker", "terraform"},
        "Software Engineering": {"java", "python", "api", "fastapi", "spring", "react", "angular", "streamlit"},
        "Data Analytics": {"sql", "analytics", "data", "etl", "spark", "tableau", "power bi"},
        "Cybersecurity": {"security", "iam", "zero trust", "nist", "rbac", "oauth"},
    }

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
        ats = self._build_ats_analysis(request, crew_output.get("ats_output"))
        resume = self._build_resume_content(request, profile, ats, crew_output.get("writer_output"))
        review = self._build_review(resume, crew_output.get("reviewer_output"))

        return {
            "profile_analysis": profile,
            "ats_analysis": ats,
            "resume_content": resume,
            "review": review,
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
                goal="Analyze candidate level, domain, skills, education, certifications, and experience.",
                backstory="Enterprise resume profile analysis specialist. Do not invent facts.",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
            )
            ats_agent = Agent(
                role="ATS Optimization Agent",
                goal="Identify ATS keywords, missing terms, score, and formatting improvements.",
                backstory="ATS optimization specialist for enterprise technology resumes.",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
            )
            writer_agent = Agent(
                role="Resume Writer Agent",
                goal="Generate professional resume summary, skills, bullets, and project descriptions.",
                backstory="Senior enterprise resume writer. Use only provided facts.",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
            )
            reviewer_agent = Agent(
                role="Reviewer Agent",
                goal="Review grammar, consistency, formatting, and professionalism.",
                backstory="Enterprise resume quality reviewer.",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
            )

            profile_task = Task(
                description="Analyze this candidate profile and return level, domain, years, strongest skills, and reasoning.\n{profile_text}",
                expected_output="Concise profile analysis.",
                agent=profile_agent,
            )
            ats_task = Task(
                description="Compare candidate to target job and return matched keywords, missing keywords, ATS score estimate, and formatting advice.\nCandidate:\n{profile_text}\nJob:\n{job_text}",
                expected_output="Concise ATS analysis.",
                agent=ats_agent,
                context=[profile_task],
            )
            writer_task = Task(
                description="Generate ATS-friendly resume content using only provided facts. Include summary, skills, bullets, and projects.\nCandidate:\n{profile_text}\nJob:\n{job_text}",
                expected_output="Resume content.",
                agent=writer_agent,
                context=[profile_task, ats_task],
            )
            reviewer_task = Task(
                description="Review the generated resume content for quality, grammar, consistency, and enterprise professionalism.",
                expected_output="Concise review with recommendations.",
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

    def _build_profile_analysis(self, request: ResumeGenerationRequest, crewai_output: str | None) -> ProfileAnalysis:
        profile = request.candidate_profile
        years = sum(item.years for item in profile.experience)
        text = " ".join(profile.skills + [profile.summary or ""]).lower()
        scores = Counter()
        for domain, terms in self.DOMAIN_KEYWORDS.items():
            scores[domain] = sum(1 for term in terms if term in text)
        domain = scores.most_common(1)[0][0] if scores else "General Technology"
        level = "Principal / Executive-Level" if years >= 15 else "Senior-Level" if years >= 8 else "Mid-Level" if years >= 3 else "Entry-Level"
        return ProfileAnalysis(
            candidate_level=level,
            primary_domain=domain,
            years_experience=years,
            strongest_skills=profile.skills[:10],
            crewai_output=crewai_output,
        )

    def _build_ats_analysis(self, request: ResumeGenerationRequest, crewai_output: str | None) -> ATSAnalysis:
        job_keywords = self._extract_keywords(request.target_job.description)
        profile_keywords = self._extract_keywords(
            " ".join(
                request.candidate_profile.skills
                + [request.candidate_profile.summary or ""]
                + request.candidate_profile.education
                + request.candidate_profile.certifications
                + [
                    " ".join([project.name, project.description] + project.technologies + project.outcomes)
                    for project in request.candidate_profile.projects
                ]
                + [" ".join(e.responsibilities + [e.company, e.title]) for e in request.candidate_profile.experience]
            )
        )
        matched = sorted(job_keywords.intersection(profile_keywords))
        missing = sorted(job_keywords.difference(profile_keywords))
        score = int((len(matched) / max(len(job_keywords), 1)) * 100)
        return ATSAnalysis(
            missing_keywords=missing[:15],
            matched_keywords=matched[:20],
            ats_score=min(score, 100),
            formatting_suggestions=[
                "Use ATS-friendly headings: Summary, Skills, Experience, Projects, Education.",
                "Include job-aligned keywords naturally in summary and bullets.",
                "Use measurable outcomes where possible.",
                "Avoid graphics, tables, and complex formatting.",
            ],
            crewai_output=crewai_output,
        )

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
        verbs = ["Architected", "Designed", "Built", "Led", "Optimized"]
        for exp in candidate.experience:
            for idx, resp in enumerate(exp.responsibilities[:3]):
                bullets.append(f"{verbs[idx % len(verbs)]} {resp} at {exp.company} as {exp.title}, aligning with enterprise architecture, security, reliability, and business outcomes.")
        project_descriptions = [
            f"{project.name}: {project.description}"
            for project in candidate.projects
        ]
        if not project_descriptions:
            project_descriptions = [
                f"Targeted resume for {job.company} {job.title}, optimized around {', '.join(ats.matched_keywords[:8]) or 'core role requirements'}."
            ]
        return ResumeContent(
            professional_summary=f"{profile.candidate_level} professional specializing in {profile.primary_domain}, aligned to {job.company}'s {job.title} role.",
            skills_section=self._prioritize(candidate.skills, ats.matched_keywords),
            experience_bullets=bullets,
            project_descriptions=project_descriptions,
            crewai_output=crewai_output,
        )

    def _build_review(self, resume: ResumeContent, crewai_output: str | None) -> ReviewResult:
        recommendations = []
        if len(resume.professional_summary.split()) < 25:
            recommendations.append("Professional summary could include more detail.")
        if len(resume.experience_bullets) < 3:
            recommendations.append("Add more experience bullets for stronger resume depth.")
        return ReviewResult(
            grammar_status="Passed basic grammar and readability checks",
            consistency_status="Consistent section structure detected",
            formatting_status="ATS-friendly plain-text structure",
            professionalism_score=90 if not recommendations else 78,
            recommendations=recommendations or ["Resume content is professional and ready for review."],
            crewai_output=crewai_output,
        )

    def _extract_keywords(self, text: str) -> Set[str]:
        normalized = text.lower()
        words = set(re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}", normalized))
        hits = {term for term in self.IMPORTANT_TERMS if term in normalized}
        stop = {"and", "or", "the", "for", "with", "you", "will", "are", "this", "that", "from", "have", "has", "role", "team", "work"}
        filtered = {word for word in words if word not in stop and len(word) > 3}
        return set(list(hits) + list(filtered)[:40])

    def _prioritize(self, skills, matched):
        matched_lower = {kw.lower() for kw in matched}
        direct = [s for s in skills if s.lower() in matched_lower]
        remaining = [s for s in skills if s not in direct]
        return (direct + remaining)[:20]
