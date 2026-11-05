from fastapi import APIRouter

from ..models.schemas import ChatRequest, ChatResponse
from ..services.chat_service import answer_question

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    return answer_question(req.repository_id, req.question, [m.model_dump() for m in req.history])
