from typing import List, Optional
from pydantic import BaseModel, Field


class ExperienceItem(BaseModel):
    company: str
    title: str
    years: float = Field(ge=0)
    responsibilities: List[str]


class ProjectItem(BaseModel):
    name: str
    description: str
    technologies: List[str] = []
    outcomes: List[str] = []


class CandidateProfile(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str]
    experience: List[ExperienceItem]
    projects: List[ProjectItem] = []
    education: List[str] = []
    certifications: List[str] = []


class TargetJob(BaseModel):
    title: str
    company: str
    description: str


class ResumeGenerationRequest(BaseModel):
    candidate_profile: CandidateProfile
    target_job: TargetJob


class ProfileAnalysis(BaseModel):
    candidate_level: str
    primary_domain: str
    years_experience: float
    strongest_skills: List[str]
    seniority_match: str = "Aligned"
    seniority_risk_note: Optional[str] = None
    crewai_output: Optional[str] = None


class DomainFitResult(BaseModel):
    is_fit: bool = True
    fit_level: str = "Good"
    domain_overlap: List[str] = []
    domain_gaps: List[str] = []
    recommendation: str = ""


class GapItem(BaseModel):
    skill_or_requirement: str
    gap_type: str = "Hard Skill"
    category: str = "C"
    category_label: str = "True gap"
    jd_weight: str = "Required"
    recommendation: str = ""
    screening_prep: Optional[str] = None


class ATSScoreBreakdown(BaseModel):
    required_keyword_score: int = 0
    required_keyword_max: int = 30
    preferred_keyword_score: int = 0
    preferred_keyword_max: int = 20
    quantified_outcomes_score: int = 0
    quantified_outcomes_max: int = 20
    title_alignment_score: int = 0
    title_alignment_max: int = 15
    education_credentials_score: int = 0
    education_credentials_max: int = 15


class ATSAnalysis(BaseModel):
    missing_keywords: List[str]
    matched_keywords: List[str]
    required_keywords: List[str] = []
    preferred_keywords: List[str] = []
    matched_required: List[str] = []
    matched_preferred: List[str] = []
    missing_required: List[str] = []
    missing_preferred: List[str] = []
    ats_score: int
    score_breakdown: Optional[ATSScoreBreakdown] = None
    formatting_suggestions: List[str]
    crewai_output: Optional[str] = None


class SubmissionConfidence(BaseModel):
    level: str = "MEDIUM"
    percentage: int = 50
    core_match: str = ""
    domain_fit: str = ""
    seniority_fit: str = ""
    differentiators: str = ""
    meaningful_gaps: str = ""
    should_submit: str = "YES"
    rationale: str = ""


class ResumeContent(BaseModel):
    professional_summary: str
    skills_section: List[str]
    experience_bullets: List[str]
    project_descriptions: List[str]
    crewai_output: Optional[str] = None


class ReviewResult(BaseModel):
    grammar_status: str
    consistency_status: str
    formatting_status: str
    professionalism_score: int
    recommendations: List[str]
    has_quantified_outcomes: bool = False
    quantified_outcomes_found: List[str] = []
    crewai_output: Optional[str] = None


class ResumeGenerationResponse(BaseModel):
    candidate_name: str
    target_role: str
    target_company: str
    agentic_framework: str
    orchestration_mode: str
    llm_provider: str
    crew_execution_path: List[str]
    profile_analysis: ProfileAnalysis
    domain_fit: Optional[DomainFitResult] = None
    ats_analysis: ATSAnalysis
    resume_content: ResumeContent
    review: ReviewResult
    gap_analysis: List[GapItem] = []
    submission_confidence: Optional[SubmissionConfidence] = None
    status: str
