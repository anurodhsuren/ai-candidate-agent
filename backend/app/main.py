import os
from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from .models import ChatRequest, JobMatchRequest
from .llm import stream_answer, match_job

app = FastAPI(title="AI Candidate Agent API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "AI Candidate Agent API is running"}


@app.get("/health")
def health():
    return {"status": "ok", "groq_configured": bool(os.getenv("GROQ_API_KEY"))}


@app.post("/chat")
def chat(request: ChatRequest):

    def generate():
        try:
            for chunk in stream_answer(request.question, request.history):
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
        return match_job(request.job_description)
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})
