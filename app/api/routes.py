from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from app.core.security import verify_api_key
from app.models.resume_models import ResumeGenerationRequest, ResumeGenerationResponse
from app.services.document_parser import build_resume_text, extract_text_from_upload
from app.services.orchestrator import ResumeOrchestrator

router = APIRouter()
orchestrator = ResumeOrchestrator()

@router.post("/resume/generate", response_model=ResumeGenerationResponse, dependencies=[Depends(verify_api_key)])
def generate_resume(request: ResumeGenerationRequest):
    return orchestrator.generate_resume(request)

@router.get("/auth/validate", dependencies=[Depends(verify_api_key)])
def validate_auth():
    return {"status": "authenticated"}

@router.post("/documents/extract", dependencies=[Depends(verify_api_key)])
async def extract_document(file: UploadFile = File(...)):
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds 5 MB limit")
    try:
        text = extract_text_from_upload(content, file.content_type, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "character_count": len(text),
        "text": text,
    }

@router.post("/resume/export/text", response_class=PlainTextResponse, dependencies=[Depends(verify_api_key)])
def export_resume_text(result: ResumeGenerationResponse):
    return build_resume_text(result)
