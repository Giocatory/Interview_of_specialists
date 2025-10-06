from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.models import InterviewStart, PositionRequest, AnswerRequest, InterviewSession
from app.services import gemini_service
from app.config import settings
from app.database_fixed import get_db, init_db, InterviewSessionDB
from app.crud_fixed import create_session, get_session, update_session_answers, update_session_complete, update_session_questions

app = FastAPI(
    title="Нейро-HR AI Interview System",
    description="AI-powered technical interviews using Gemini",
    version="3.0.0"
)

# Инициализация БД при запуске
@app.on_event("startup")
def startup_event():
    init_db()
    print("✅ Database initialized")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory="app/templates")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/start_interview")
async def start_interview(data: InterviewStart, db: Session = Depends(get_db)):
    if not data.start:
        raise HTTPException(status_code=400, detail="Interview not started")
    
    session_id = str(uuid.uuid4())
    session_data = InterviewSession(
        session_id=session_id,
        user_id=data.user_id,
        platform=data.platform,
        position="",
        questions=[],
        current_question=0,
        answers=[],
        status="active",
        created_at=datetime.now()
    )
    
    create_session(db, session_data)
    
    return {
        "session_id": session_id,
        "message": "🎯 Добро пожаловать в Нейро-HR! Я помогу провести техническое собеседование. На какую позицию вы проводите собеседование?"
    }

@app.post("/api/set_position")
async def set_position(data: PositionRequest, db: Session = Depends(get_db)):
    db_session = get_session(db, data.session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    print(f"🔄 Установка позиции: {data.position}")
    
    # Обновляем user_id если пришел из телеграма
    if data.user_id and not db_session.user_id:
        db_session.user_id = data.user_id
        db.commit()
    
    questions = gemini_service.generate_questions(data.position)
    print(f"📋 Сгенерировано вопросов: {len(questions)}")
    
    update_session_questions(db, data.session_id, questions, data.position)
    
    return {
        "question": questions[0],
        "current_question": 1,
        "total_questions": len(questions),
        "position": data.position
    }

@app.post("/api/answer_question")
async def answer_question(data: AnswerRequest, db: Session = Depends(get_db)):
    db_session = get_session(db, data.session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    current_questions = db_session.get_questions()
    current_answers = db_session.get_answers()
    current_question_index = db_session.current_question
    
    print(f"📝 Получен ответ для вопроса {current_question_index + 1}")
    print(f"📊 Текущие ответы до добавления: {len(current_answers)}")
    
    # Добавляем новый ответ
    current_answers.append(data.answer)
    new_question_index = current_question_index + 1
    
    print(f"📊 Ответы после добавления: {len(current_answers)}")
    
    # Проверяем завершение собеседования
    if new_question_index >= len(current_questions):
        print(f"🎯 Собеседование завершено! Вопросов: {len(current_questions)}, Ответов: {len(current_answers)}")
        
        # Все вопросы отвечены - генерируем фидбэк
        feedback = gemini_service.generate_feedback(
            db_session.position,
            current_questions,
            current_answers
        )
        
        update_session_complete(db, data.session_id, current_answers, feedback)
        
        return {
            "interview_complete": True,
            "feedback": feedback,
            "total_questions": len(current_questions),
            "position": db_session.position
        }
    else:
        # Продолжаем собеседование - сохраняем ответы
        update_session_answers(db, data.session_id, current_answers, new_question_index)
        
        next_question = current_questions[new_question_index]
        print(f"➡️ Следующий вопрос: {new_question_index + 1}")
        
        return {
            "question": next_question,
            "current_question": new_question_index + 1,
            "total_questions": len(current_questions),
            "interview_complete": False
        }

@app.get("/api/session/{session_id}")
async def get_session_endpoint(session_id: str, db: Session = Depends(get_db)):
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    # Отладочная информация
    questions = session.get_questions()
    answers = session.get_answers()
    
    print(f"🔍 Сессия {session_id}:")
    print(f"   Вопросов: {len(questions)}")
    print(f"   Ответов: {len(answers)}")
    print(f"   Текущий вопрос: {session.current_question}")
    print(f"   Ответы: {answers}")
    
    return {
        "session_id": session.session_id,
        "position": session.position,
        "questions": questions,
        "answers": answers,
        "current_question": session.current_question,
        "status": session.status
    }

@app.get("/api/user/{user_id}/sessions")
async def get_user_sessions(user_id: str, db: Session = Depends(get_db)):
    from app.crud_fixed import get_user_sessions
    sessions = get_user_sessions(db, user_id)
    
    result = []
    for session in sessions:
        result.append({
            "session_id": session.session_id,
            "position": session.position,
            "questions": session.get_questions(),
            "answers": session.get_answers(),
            "current_question": session.current_question,
            "status": session.status,
            "created_at": session.created_at
        })
    
    return {"user_id": user_id, "sessions": result}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Проверяем подключение к БД
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        print(f"Database health check error: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy", 
        "model": settings.GEMINI_MODEL,
        "database": db_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )