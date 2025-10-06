from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class InterviewStart(BaseModel):
    start: bool
    user_id: Optional[str] = None
    platform: Optional[str] = "web"

class PositionRequest(BaseModel):
    session_id: str
    position: str
    user_id: Optional[str] = None

class AnswerRequest(BaseModel):
    session_id: str
    answer: str
    user_id: Optional[str] = None

class InterviewSession(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    platform: str = "web"
    position: str
    questions: List[str]
    current_question: int
    answers: List[str]
    status: str = "active"
    feedback: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True