import os
from typing import Any, Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

# Define the output structure
class StatusUpdateInsight(BaseModel):
    insight: str = Field(description="A concise, encouraging, and actionable insight about the status change.")
    action_items: List[str] = Field(description="List of 1-3 specific next steps for the user.")

def generate_status_insight(
    company: str, 
    role: str, 
    old_status: str, 
    new_status: str, 
    notes: str = ""
) -> Dict[str, Any]:
    """
    Generates an AI insight for a job application status change using LangChain and OpenRouter.
    """
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = "https://openrouter.ai/api/v1"
    model_name = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    if not api_key:
        return {
            "insight": f"Great job moving to {new_status}! Keep up the momentum.",
            "action_items": ["Review the job description", "Update your notes"]
        }

    try:
        llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model_name,
            temperature=0.7
        )

        parser = JsonOutputParser(pydantic_object=StatusUpdateInsight)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a supportive and strategic career coach. A user has just updated the status of a job application. Provide a brief, encouraging insight and 1-3 actionable next steps. Keep it professional but friendly."),
            ("user", "Company: {company}\nRole: {role}\nOld Status: {old_status}\nNew Status: {new_status}\nUser Notes: {notes}\n\n{format_instructions}")
        ])

        chain = prompt | llm | parser

        result = chain.invoke({
            "company": company,
            "role": role,
            "old_status": old_status,
            "new_status": new_status,
            "notes": notes,
            "format_instructions": parser.get_format_instructions()
        })

        return result

    except Exception as e:
        print(f"Error generating AI insight: {e}")
        return {
            "insight": f"Status updated to {new_status}. Good luck!",
            "action_items": []
        }
