import os
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from .llm import PROFILE, extract_candidate_profile, match_job, stream_answer
from .models import ChatRequest, JobMatchRequest
from .resume import extract_resume_text

load_dotenv()

app = FastAPI(title="AI Candidate Agent API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uploaded profiles intentionally live only in process memory. Each upload
# receives its own opaque ID, so requests select their own candidate instead of
# sharing a global "active" resume. Add a database when persistence is needed.
uploaded_profiles: dict[str, dict] = {}


def profile_for(candidate_id: str | None) -> dict:
    if candidate_id is None:
        return PROFILE
    profile = uploaded_profiles.get(candidate_id)
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Uploaded candidate not found. Upload the resume again.",
        )
    return profile


@app.get("/")
def root():
    return {"message": "AI Candidate Agent API is running"}


@app.get("/health")
def health():
    return {"status": "ok", "groq_configured": bool(os.getenv("GROQ_API_KEY"))}


@app.post("/resumes")
async def upload_resume(file: UploadFile = File(...)):
    """Create a temporary, candidate-specific profile from a resume upload."""
    try:
        resume_text = extract_resume_text(file.filename, await file.read())
        profile = extract_candidate_profile(resume_text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        # Do not leak provider internals or a resume's contents in the response.
        print("RESUME PROCESSING ERROR:", repr(exc))
        raise HTTPException(status_code=500, detail="Unable to process this resume.") from exc

    candidate_id = str(uuid4())
    uploaded_profiles[candidate_id] = profile
    return {
        "candidate_id": candidate_id,
        "profile": profile,
        "message": "Resume processed. Chat and job matching now use this candidate.",
    }


@app.post("/chat")
def chat(request: ChatRequest):
    profile = profile_for(request.candidate_id)

    def generate():
        try:
            for chunk in stream_answer(request.question, request.history, profile):
                yield chunk

        except Exception as e:
            print("STREAM ERROR:", repr(e))
            yield f"\n\n[ERROR] {str(e)}"

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/job-match")
def job_match(request: JobMatchRequest):
    try:
        return match_job(request.job_description, profile_for(request.candidate_id))
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})
