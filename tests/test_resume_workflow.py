from app.crew.resume_crew import ResumeCrewAIWorkflow
from app.models.resume_models import CandidateProfile, ExperienceItem, ProjectItem, ResumeGenerationRequest, TargetJob


def make_request(years=5):
    return ResumeGenerationRequest(
        candidate_profile=CandidateProfile(
            name="Test User",
            summary="AI engineer building FastAPI, CrewAI, Ollama, Kubernetes, and governance workflows.",
            skills=["Python", "FastAPI", "CrewAI", "Ollama", "Kubernetes", "Governance"],
            experience=[
                ExperienceItem(
                    company="Example Corp",
                    title="AI Engineer",
                    years=years,
                    responsibilities=[
                        "built AI resume generator",
                        "designed CrewAI workflow",
                        "implemented monitoring",
                    ],
                )
            ],
            projects=[
                ProjectItem(
                    name="Enterprise AI Resume Generator",
                    description="Built a CrewAI and FastAPI resume workflow.",
                    technologies=["CrewAI", "FastAPI", "Ollama"],
                    outcomes=["Improved ATS targeting"],
                )
            ],
            education=["MS Computer Science"],
            certifications=["AWS Solutions Architect"],
        ),
        target_job=TargetJob(
            title="Principal AI Architect",
            company="Example Bank",
            description="Needs GenAI, FastAPI, CrewAI, Ollama, Kubernetes, governance, observability, and security.",
        ),
    )


def test_workflow_fallback_builds_structured_resume(monkeypatch):
    workflow = ResumeCrewAIWorkflow()
    monkeypatch.setattr(
        workflow,
        "_run_crewai",
        lambda profile_text, job_text: {
            "profile_output": None,
            "ats_output": None,
            "writer_output": None,
            "reviewer_output": None,
            "used_crewai": False,
        },
    )

    result = workflow.run(make_request())

    assert result["used_crewai"] is False
    assert result["execution_path"] == ResumeCrewAIWorkflow.EXECUTION_PATH
    assert result["profile_analysis"].candidate_level == "Mid-Level"
    assert result["profile_analysis"].primary_domain == "AI / Machine Learning"
    assert "FastAPI" in result["resume_content"].skills_section
    assert result["resume_content"].project_descriptions[0].startswith("Enterprise AI Resume Generator")
    assert result["ats_analysis"].ats_score > 0
    assert result["review"].formatting_status == "ATS-friendly plain-text structure"


def test_profile_level_boundaries():
    workflow = ResumeCrewAIWorkflow()

    assert workflow._build_profile_analysis(make_request(years=1), None).candidate_level == "Entry-Level"
    assert workflow._build_profile_analysis(make_request(years=3), None).candidate_level == "Mid-Level"
    assert workflow._build_profile_analysis(make_request(years=8), None).candidate_level == "Senior-Level"
    assert workflow._build_profile_analysis(make_request(years=15), None).candidate_level == "Principal / Executive-Level"


def test_crewai_writer_output_is_trimmed_into_bullets():
    workflow = ResumeCrewAIWorkflow()
    request = make_request()
    profile = workflow._build_profile_analysis(request, None)
    ats = workflow._build_ats_analysis(request, None)

    resume = workflow._build_resume_content(
        request,
        profile,
        ats,
        "- Led AI platform delivery\n• Improved ATS scoring\nplain paragraph",
    )

    assert resume.experience_bullets == ["Led AI platform delivery", "Improved ATS scoring"]
    assert resume.professional_summary.startswith("- Led AI platform delivery")
