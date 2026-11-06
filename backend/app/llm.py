import json
import os
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from groq import Groq
from groq.types.chat import ChatCompletionMessageParam

from .models import Message
from .prompts import SYSTEM_PROMPT

PROFILE = json.loads(
    (Path(__file__).parent / "candidate.json").read_text(encoding="utf-8")
)


def get_client():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Create backend/.env from backend/.env.example."
        )
    return Groq(api_key=key)


def build_messages(
    question: str, history: Sequence[Message], profile: dict
) -> list[ChatCompletionMessageParam]:
    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
            + "\n\nCANDIDATE PROFILE:\n"
            + json.dumps(profile, indent=2),
        }
    ]
    for m in history[-12:]:
        messages.append(
            cast(ChatCompletionMessageParam, {"role": m.role, "content": m.content})
        )
    messages.append({"role": "user", "content": question})
    return messages


def stream_answer(question: str, history: Sequence[Message], profile: dict | None = None):
    completion = get_client().chat.completions.create(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        messages=build_messages(question, history, profile or PROFILE),
        temperature=0.1,
        stream=True,
    )
    for chunk in completion:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def extract_candidate_profile(resume_text: str) -> dict:
    """Ask the model to turn arbitrary resume text into a grounded profile."""
    prompt = f"""Extract a structured candidate profile from the resume below.
Return valid JSON with these keys: name, title, contact, education, skills,
summary, projects, experience, certifications, extracurricular, key_strengths,
social_links. Use arrays/objects where appropriate. Include only facts stated in
the resume. Do not infer, embellish, or add placeholder facts.

RESUME TEXT:
{resume_text}
"""
    response = get_client().chat.completions.create(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        messages=[
            {
                "role": "system",
                "content": "You extract factual, structured resume data. Return JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("The model returned an empty candidate profile.")
    profile = json.loads(content)
    if not isinstance(profile, dict):
        raise ValueError("The model returned an invalid candidate profile.")
    return profile


def match_job(job_description: str, profile: dict | None = None):
    prompt = f"""Compare the job description with the candidate profile.
Return JSON with keys: suitable (boolean), matching_skills (array),
missing_or_unverified_skills (array), strengths (array), recommendation (string).
Only use explicit profile facts.
JOB DESCRIPTION:
{job_description}"""
    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
            + "\n\nCANDIDATE PROFILE:\n"
            + json.dumps(profile or PROFILE),
        },
        {"role": "user", "content": prompt},
    ]
    response = get_client().chat.completions.create(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        messages=messages,
        temperature=0,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("The model returned an empty response.")
    return json.loads(content)
