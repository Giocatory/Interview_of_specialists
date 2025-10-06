from app.database import SessionLocal, InterviewSessionDB
import json

def test_db():
    db = SessionLocal()
    try:
        # Создаем тестовую запись
        test_session = InterviewSessionDB(
            session_id="test_session",
            position="Python Developer",
            questions=["Question 1", "Question 2", "Question 3"],
            answers=["Answer 1", "Answer 2", "Answer 3"],
            current_question=3
        )
        db.add(test_session)
        db.commit()
        
        # Читаем обратно
        session = db.query(InterviewSessionDB).filter(InterviewSessionDB.session_id == "test_session").first()
        print(f"Вопросы: {session.questions}, тип: {type(session.questions)}")
        print(f"Ответы: {session.answers}, тип: {type(session.answers)}")
        print(f"Количество ответов: {len(session.answers)}")
        
        # Очищаем тестовую запись
        db.delete(session)
        db.commit()
        
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_db()