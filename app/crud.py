from sqlalchemy.orm import Session
from app.database import InterviewSessionDB
from app.models import InterviewSession
from datetime import datetime

def create_session(db: Session, session_data: InterviewSession):
    db_session = InterviewSessionDB(
        session_id=session_data.session_id,
        user_id=session_data.user_id,
        platform=session_data.platform,
        position=session_data.position,
        questions=session_data.questions or [],
        answers=session_data.answers or [],
        current_question=session_data.current_question,
        status=session_data.status,
        created_at=session_data.created_at
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_session(db: Session, session_id: str):
    return db.query(InterviewSessionDB).filter(InterviewSessionDB.session_id == session_id).first()

def update_session(db: Session, session_id: str, update_data: dict):
    db_session = db.query(InterviewSessionDB).filter(InterviewSessionDB.session_id == session_id).first()
    if db_session:
        for key, value in update_data.items():
            # Особенная обработка для списков
            if key in ['questions', 'answers'] and value is None:
                value = []
            setattr(db_session, key, value)
        db.commit()
        db.refresh(db_session)
    return db_session

def get_user_sessions(db: Session, user_id: str):
    return db.query(InterviewSessionDB).filter(InterviewSessionDB.user_id == user_id).order_by(InterviewSessionDB.created_at.desc()).all()