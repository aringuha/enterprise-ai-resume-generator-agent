from io import BytesIO

import pdfplumber

try:
    from docx import Document
except Exception:  # pragma: no cover - optional dependency guard
    Document = None


SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
}


def extract_text_from_upload(content: bytes, content_type: str | None, filename: str | None = None) -> str:
    content_type = content_type or ""
    filename = filename or ""
    lowered_name = filename.lower()

    if content_type == "application/pdf" or lowered_name.endswith(".pdf"):
        text_parts = []
        with pdfplumber.open(BytesIO(content)) as pdf:
            for page in pdf.pages:
                text_parts.append(page.extract_text() or "")
        return "\n".join(part for part in text_parts if part).strip()

    if (
        content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or lowered_name.endswith(".docx")
    ):
        if Document is None:
            raise ValueError("DOCX parsing requires python-docx.")
        document = Document(BytesIO(content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text).strip()

    if content_type.startswith("text/") or lowered_name.endswith((".txt", ".md")):
        return content.decode("utf-8", errors="ignore").strip()

    raise ValueError("Unsupported file type. Use PDF, DOCX, TXT, or MD.")


def build_resume_text(result) -> str:
    resume = result.resume_content
    ats = result.ats_analysis
    review = result.review
    lines = [
        result.candidate_name,
        f"Target: {result.target_role} at {result.target_company}",
        "",
        "Professional Summary",
        resume.professional_summary,
        "",
        "Skills",
        ", ".join(resume.skills_section),
        "",
        "Experience",
    ]
    lines.extend(f"- {bullet}" for bullet in resume.experience_bullets)
    lines.extend(["", "Projects"])
    lines.extend(f"- {project}" for project in resume.project_descriptions)
    lines.extend([
        "",
        "ATS Analysis",
        f"Score: {ats.ats_score}",
        f"Matched Keywords: {', '.join(ats.matched_keywords)}",
        f"Missing Keywords: {', '.join(ats.missing_keywords)}",
        "",
        "Reviewer Notes",
        f"Professionalism Score: {review.professionalism_score}",
    ])
    lines.extend(f"- {item}" for item in review.recommendations)
    return "\n".join(lines).strip() + "\n"
