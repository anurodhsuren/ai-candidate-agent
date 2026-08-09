# AI Candidate Agent

An AI-powered candidate representative that lets recruiters and visitors interact with a candidate's profile using natural language.

The application answers questions about the candidate's **resume, education, skills, and projects** using the candidate profile, and includes a **Job Description Matcher** for comparing a candidate against a role.

## Features

-  Resume-grounded AI chat
-  Conversation history for follow-up questions
-  Streaming AI responses
-  Job Description matching
-  Matching and missing/unverified skill analysis
-  Groq LLM integration
-  FastAPI backend
-  React + Vite frontend
-  Responsive interface
-  API key loaded through environment variables
-  Prompt rules to reduce hallucinations

## Architecture

```text
                    ┌──────────────────────┐
                    │      React UI        │
                    │      + Vite          │
                    └──────────┬───────────┘
                               │
                            Fetch API
                               │
                               ▼
                    ┌──────────────────────┐
                    │       FastAPI        │
                    │       Backend        │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │   Candidate Profile  │
                    │    candidate.json    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │       Groq LLM       │
                    │  Streaming Response  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      React Chat      │
                    └──────────────────────┘
```

## Tech Stack

### Frontend
- React
- JavaScript
- Vite
- CSS
- Fetch API
- Browser streaming APIs

### Backend
- Python
- FastAPI
- Pydantic
- Uvicorn
- Python-dotenv

### AI
- Groq API
- Prompt engineering
- Resume-grounded question answering
- Structured job matching

##  Project Structure

```text
ai-candidate-agent/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── llm.py
│   │   ├── models.py
│   │   ├── prompts.py
│   │   └── candidate.json
│   ├── .env.example
│   ├── requirements.txt
│   └── start.bat
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── .env.example
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
├── README.md
└── START_HERE.txt
```

# Getting Started

## Prerequisites

- Python 3.10+ (3.11 recommended)
- Node.js 18+
- npm
- A Groq API key

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-candidate-agent.git
cd ai-candidate-agent
```

Replace `YOUR_USERNAME` with your GitHub username.

# Backend Setup

```bash
cd backend
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configure Groq

Create:

```text
backend/.env
```

Add:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

**Never commit `.env` or your real API key to GitHub.**

Start the backend:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

Expected:

```json
{
  "status": "ok",
  "groq_configured": true
}
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

#  Frontend Setup

Open a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL, normally:

```text
http://localhost:5173
```

#  Example Questions

```text
Tell me about the candidate.
```

```text
What are the candidate's strongest technical skills?
```

```text
Tell me about the VectorDB project.
```

```text
Which project demonstrates RAG experience?
```

```text
Which project uses HNSW?
```

```text
What technologies has the candidate worked with?
```

The assistant is instructed to use the candidate profile rather than inventing candidate information.

#  Job Description Matching

Paste a job description into the Job Matcher.

The system analyzes:

- Candidate suitability
- Matching skills
- Missing or unverified skills
- Candidate strengths
- Recommendation

Workflow:

```text
Job Description
      ↓
AI analyzes requirements
      ↓
Compare with candidate profile
      ↓
Matching skills + gaps
      ↓
Recommendation
```

#  AI Grounding

The system prompt instructs the AI to:

- Use only the provided candidate information.
- Never invent candidate experience.
- Never claim unsupported skills.
- Clearly say when information is unavailable.
- Use conversation history to understand follow-up questions.
- Remain professional and concise.

# Conversation Memory

Previous messages are sent to the backend so follow-up questions can be understood.

Example:

```text
User:
Tell me about the candidate's projects.

AI:
The candidate has worked on ...

User:
Which one uses HNSW?

AI:
The VectorDB project uses HNSW...
```

Conversation history helps resolve references while candidate facts remain grounded in the profile.

# API Endpoints

## Health Check

```http
GET /health
```

## Chat

```http
POST /chat
```

Example:

```json
{
  "question": "Tell me about the candidate.",
  "history": []
}
```

The endpoint returns a streaming text response.

## Job Matching

```http
POST /job-match
```

Example:

```json
{
  "job_description": "We are looking for a Python developer with RAG experience..."
}
```

Returns structured job-matching information.

#  Security

Keep secrets in environment variables.

Never put API keys directly into:

- React source code
- Python source code
- `candidate.json`
- README files
- Git commits

Before pushing:

```bash
git status
```

Make sure `.env` is not listed as a file to commit.

#  Testing Checklist

- [ ] Backend starts successfully
- [ ] `/health` returns `status: ok`
- [ ] Groq API key is detected
- [ ] Chat request works
- [ ] Streaming responses work
- [ ] Conversation history works
- [ ] Job matcher works
- [ ] Missing information is not hallucinated
- [ ] Frontend communicates with backend
- [ ] Mobile layout works
- [ ] `.env` is not committed
- [ ] `node_modules` is not committed
- [ ] `.venv` is not committed

# Deployment

The application can be deployed as two services:

```text
                    GitHub
                       │
             ┌─────────┴─────────┐
             │                   │
             ▼                   ▼
         Frontend             Backend
          Vercel             Render/Koyeb
             │                   │
             └─────────┬─────────┘
                       │
                       ▼
                    Groq API
```

## Frontend

Deploy the React/Vite application to Vercel.

Set:

```env
VITE_API_URL=https://YOUR-BACKEND-URL
```

## Backend

Deploy the FastAPI application to a suitable Python hosting platform.

Set:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

Do not expose the Groq key to the frontend.

#  Future Improvements

- [ ] Dark mode
- [ ] Markdown rendering
- [ ] Copy response button
- [ ] Better typing/loading animation
- [ ] Resume download
- [ ] GitHub/LinkedIn integration
- [ ] Interview question generation
- [ ] Job-match score visualization
- [ ] Recruiter dashboard
- [ ] Authentication
- [ ] Persistent conversation storage
- [ ] Automated resume ingestion
- [ ] CI/CD deployment

# Candidate


Agentic AI Engineer / Computer Science Undergraduate

The included candidate profile contains information about education, technical skills, and projects such as the VectorDB/RAG pipeline.

# License

This project is intended as a personal portfolio project.

If you reuse the code, remove private candidate information before redistribution.
