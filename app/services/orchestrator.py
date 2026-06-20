import logging

from app.crew.resume_crew import ResumeCrewAIWorkflow
from app.models.resume_models import ResumeGenerationRequest, ResumeGenerationResponse
from app.services.metrics import metrics_service
from app.services.ollama_client import ollama_client

logger = logging.getLogger(__name__)

class ResumeOrchestrator:
    AGENTIC_FRAMEWORK = "CrewAI sequential multi-agent crew"

    def __init__(self):
        self.crew_workflow = ResumeCrewAIWorkflow()

    def generate_resume(self, request: ResumeGenerationRequest) -> ResumeGenerationResponse:
        try:
            logger.info("Starting CrewAI resume generation workflow")
            result = self.crew_workflow.run(request)
            metrics_service.record_success()
            return ResumeGenerationResponse(
                candidate_name=request.candidate_profile.name,
                target_role=request.target_job.title,
                target_company=request.target_job.company,
                agentic_framework=self.AGENTIC_FRAMEWORK,
                orchestration_mode="CrewAI Process.sequential",
                llm_provider=ollama_client.provider_name(),
                crew_execution_path=result["execution_path"],
                profile_analysis=result["profile_analysis"],
                ats_analysis=result["ats_analysis"],
                resume_content=result["resume_content"],
                review=result["review"],
                status="success",
            )
        except Exception:
            metrics_service.record_failure()
            logger.exception("CrewAI resume generation workflow failed")
            raise
