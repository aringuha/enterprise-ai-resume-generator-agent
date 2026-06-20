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
    crewai_output: Optional[str] = None

class ATSAnalysis(BaseModel):
    missing_keywords: List[str]
    matched_keywords: List[str]
    ats_score: int
    formatting_suggestions: List[str]
    crewai_output: Optional[str] = None

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
    ats_analysis: ATSAnalysis
    resume_content: ResumeContent
    review: ReviewResult
    status: str
