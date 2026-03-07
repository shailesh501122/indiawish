from fastapi import APIRouter, Depends
from ...services.ai import generate_description, suggest_price, AIDescriptionRequest, AIPriceSuggestionRequest

router = APIRouter()

@router.post("/generate-description")
def ai_description(request: AIDescriptionRequest):
    description = generate_description(request.title, request.category)
    return {"description": description}

@router.post("/suggest-price")
def ai_price(request: AIPriceSuggestionRequest):
    price = suggest_price(request.title, request.category, request.condition)
    return {"suggestedPrice": price}
