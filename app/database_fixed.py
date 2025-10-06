from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime

from app.config import settings

Base = declarative_base()

class InterviewSessionDB(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    user_id = Column(String, nullable=True)
    platform = Column(String, default="web")
    position = Column(String)
    questions = Column(Text)  # Храним как JSON строку
    answers = Column(Text)    # Храним как JSON строку  
    current_question = Column(Integer, default=0)
    status = Column(String, default="active")
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def get_questions(self):
        """Получить вопросы как список"""
        if self.questions:
            return json.loads(self.questions)
        return []
    
    def set_questions(self, questions_list):
        """Установить вопросы как JSON строку"""
        self.questions = json.dumps(questions_list, ensure_ascii=False)
    
    def get_answers(self):
        """Получить ответы как список"""
        if self.answers:
            return json.loads(self.answers)
        return []
    
    def set_answers(self, answers_list):
        """Установить ответы как JSON строку"""
        self.answers = json.dumps(answers_list, ensure_ascii=False)

# SQLite для разработки
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)