from sqlalchemy.orm import Session
from app.database_fixed import InterviewSessionDB
from app.models import InterviewSession
from datetime import datetime

def create_session(db: Session, session_data: InterviewSession):
    db_session = InterviewSessionDB(
        session_id=session_data.session_id,
        user_id=session_data.user_id,
        platform=session_data.platform,
        position=session_data.position,
        current_question=session_data.current_question,
        status=session_data.status,
        created_at=session_data.created_at
    )
    db_session.set_questions(session_data.questions or [])
    db_session.set_answers(session_data.answers or [])
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_session(db: Session, session_id: str):
    return db.query(InterviewSessionDB).filter(InterviewSessionDB.session_id == session_id).first()

def update_session_answers(db: Session, session_id: str, answers: list, current_question: int):
    """Специальная функция для обновления ответов"""
    db_session = db.query(InterviewSessionDB).filter(InterviewSessionDB.session_id == session_id).first()
    if db_session:
        print(f"💾 Сохранение {len(answers)} ответов в базу")
        db_session.set_answers(answers)
        db_session.current_question = current_question
        db.commit()
        db.refresh(db_session)
        print(f"✅ В базе теперь {len(db_session.get_answers())} ответов")
    return db_session

def update_session_complete(db: Session, session_id: str, answers: list, feedback: str):
    """Завершение собеседования"""
    db_session = db.query(InterviewSessionDB).filter(InterviewSessionDB.session_id == session_id).first()
    if db_session:
        db_session.set_answers(answers)
        db_session.status = "completed"
        db_session.feedback = feedback
        db_session.completed_at = datetime.now()
        db.commit()
        db.refresh(db_session)
    return db_session

def update_session_questions(db: Session, session_id: str, questions: list, position: str):
    """Обновление вопросов и позиции"""
    db_session = db.query(InterviewSessionDB).filter(InterviewSessionDB.session_id == session_id).first()
    if db_session:
        db_session.set_questions(questions)
        db_session.position = position
        db_session.current_question = 0
        db_session.set_answers([])
        db.commit()
        db.refresh(db_session)
    return db_session

def get_user_sessions(db: Session, user_id: str):
    return db.query(InterviewSessionDB).filter(InterviewSessionDB.user_id == user_id).order_by(InterviewSessionDB.created_at.desc()).all()