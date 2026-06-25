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
    suggested_skill_to_learn: str = Field(description="If the rejection implies a specific technical skill is missing, output exactly that skill name here (e.g. 'Next.js'). Otherwise, leave empty.", default="")

def generate_status_insight(
    company: str, 
    role: str, 
    old_status: str, 
    new_status: str, 
    notes: str = "",
    tech_skills: List[str] = None,
    learning_skills: List[str] = None,
    recent_rejections: int = 0

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
            ("system", "You are an elite, highly strategic career coach acting as an AI Agent for a tech professional. The user just changed a job application's status. "
                       "Your goal is to provide a highly personalized, agentic insight correlating their current skills, what they want to learn, and their recent application track record.\n"
                       "If they were rejected and have a high rejection count, analyze their missing skills and suggest a pivot or specific learning goal. "
                       "If they moved to an interview, tell them which of their current skills to highlight.\n"
                       "Do not use generic cheerleading. Be concise, direct, and actionable.\n"
                       "Format the response perfectly matching the JSON schema."),
            ("user", "Company: {company}\nRole: {role}\nOld Status: {old_status}\nNew Status: {new_status}\nUser Notes: {notes}\n"
                     "User's Technical Skills: {tech_skills}\nUser's Learning Goals: {learning_skills}\n"
                     "User's Recent Rejections (last 14 days): {recent_rejections}\n\n{format_instructions}")
        ])

        chain = prompt | llm | parser

        result = chain.invoke({
            "company": company,
            "role": role,
            "old_status": old_status,
            "new_status": new_status,
            "notes": notes,
            "tech_skills": ", ".join(tech_skills) if tech_skills else "None specified",
            "learning_skills": ", ".join(learning_skills) if learning_skills else "None specified",
            "recent_rejections": recent_rejections,
            "format_instructions": parser.get_format_instructions()
        })

        return result

    except Exception as e:
        print(f"Error generating AI insight: {e}")
        return {
            "insight": f"Status updated to {new_status}. Good luck!",
            "action_items": []
        }
