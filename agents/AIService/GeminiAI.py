import os
import re
import json
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv
from ..models import *

load_dotenv()


def _local_extract(text: str) -> Dict[str, Any]:
    # Lightweight heuristic fallback when API is not configured
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phone_match = re.search(r"(\+?\d[\d\s()\-]{8,})", text)
    linkedin_match = re.search(r"https?://(www\.)?linkedin\.com/[^\s]+", text, re.I)
    github_match = re.search(r"https?://(www\.)?github\.com/[^\s]+", text, re.I)

    # Naive skills extraction
    known_skills = [
        "python",
        "django",
        "drf",
        "rest",
        "sql",
        "postgres",
        "mysql",
        "mongodb",
        "react",
        "next",
        "node",
        "aws",
        "gcp",
        "azure",
        "docker",
        "kubernetes",
        "git",
        "linux",
        "pandas",
        "numpy",
        "tensorflow",
        "pytorch",
    ]
    lower = text.lower()
    skills: List[Dict[str, Any]] = []
    for s in known_skills:
        if re.search(rf"\b{s}\b", lower):
            skills.append({"name": s})

    header = {
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
        "linkedin": linkedin_match.group(0) if linkedin_match else None,
        "github": github_match.group(0) if github_match else None,
    }

    return {
        "header": header,
        "summary": "",
        "skills": skills,
        "experience": [],
        "education": [],
        "projects": [],
        "extras": {},
        "confidence": 0.3,
    }


def extract_resume(text: str) -> Dict[str, Any]:
    """
    Minimal text-based extractor used by AIService.__init__.
    Falls back to the lightweight local heuristic extraction.
    """
    return _local_extract(text)


from pydantic_ai import Agent, BinaryContent, PromptedOutput

EXTRACTION_PROMPT = """
You are a resume extraction agent. 
Your job is to read a candidate’s CV and return structured data that matches the following fields: full name, portfolio URL, phone number, country, LinkedIn URL, education background, and skills. 
The education background should include the institution, joined date, certification, course, and completion date. The skills should include the skill name, skill category, proficiency level, and years of experience. 
Return the information as valid JSON that fits this structure exactly, using null where information is missing. Extract only factual details from the CV without guessing or adding information.
If the candidate has multiple education records or skills, include all of them in their respective lists. Keep date formats consistent, such as “2020-09” or “September 2020”. 
Group related skills into categories and provide proficiency levels such as “Beginner”, “Intermediate”, or “Advanced”.
Avoid explanations or formatting
"""
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider


class ResumeExtractionAgent:
    def __init__(self, open_router: bool):
        self.agent = Agent(
            model=OpenAIChatModel(
                model_name="gpt-oss:120b",
                provider=OllamaProvider(
                    base_url="https://ollama.com/v1",
                    api_key=os.getenv("OLLAMA_API_KEY")
                )
            ),
            system_prompt=EXTRACTION_PROMPT,
            output_type=PromptedOutput(Profile),
        )

    def __call__(self, markdown):
        response = self.agent.run_sync(f"The user CV is: {markdown}")
        return response.output
