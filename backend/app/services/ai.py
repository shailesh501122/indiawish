import openai
import os
from pydantic import BaseModel

openai.api_key = os.getenv("OPENAI_API_KEY", "your-key-here")

class AIDescriptionRequest(BaseModel):
    title: str
    category: str

class AIPriceSuggestionRequest(BaseModel):
    title: str
    category: str
    condition: str

def generate_description(title: str, category: str):
    # In a real app this would call OpenAI. For now returning a mock response to avoid billing errors.
    return f"This is an AI-generated premium description for a {title} in the {category} category. It is highly optimized for search."

def suggest_price(title: str, category: str, condition: str):
    # Mock logic
    return 1500.0
