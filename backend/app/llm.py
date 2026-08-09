import json, os
from pathlib import Path
from groq import Groq
from .prompts import SYSTEM_PROMPT

PROFILE = json.loads((Path(__file__).parent / "candidate.json").read_text(encoding="utf-8"))

def get_client():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is missing. Create backend/.env from backend/.env.example.")
    return Groq(api_key=key)

def build_messages(question, history):
    messages = [{"role":"system","content":SYSTEM_PROMPT+"\n\nCANDIDATE PROFILE:\n"+json.dumps(PROFILE,indent=2)}]
    for m in history[-12:]:
        messages.append({"role":m.role,"content":m.content})
    messages.append({"role":"user","content":question})
    return messages

def stream_answer(question, history):
    completion = get_client().chat.completions.create(
        model=os.getenv("GROQ_MODEL","llama-3.3-70b-versatile"),
        messages=build_messages(question, history), temperature=0.1, stream=True)
    for chunk in completion:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

def match_job(job_description):
    prompt = f'''Compare the job description with the candidate profile.
Return JSON with keys: suitable (boolean), matching_skills (array),
missing_or_unverified_skills (array), strengths (array), recommendation (string).
Only use explicit profile facts.
JOB DESCRIPTION:
{job_description}'''
    response = get_client().chat.completions.create(
        model=os.getenv("GROQ_MODEL","llama-3.3-70b-versatile"),
        messages=[{"role":"system","content":SYSTEM_PROMPT+"\n\nCANDIDATE PROFILE:\n"+json.dumps(PROFILE)},
                  {"role":"user","content":prompt}],
        temperature=0, response_format={"type":"json_object"})
    return json.loads(response.choices[0].message.content)
