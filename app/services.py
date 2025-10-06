from google import genai
from google.genai import types
from app.config import settings

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL
    
    def generate_questions(self, position: str) -> list:
        prompt = f"""
        Ты - технический рекрутер. Сгенерируй 10 строгих технических вопросов для собеседования на позицию {position}.
        Вопросы должны проверять:
        - Глубину знаний языка программирования и технологий
        - Практический опыт работы
        - Понимание архитектуры и best practices
        - Решение реальных задач
        
        Формат: только вопросы, каждый с новой строки, без номеров, без дополнительного текста.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            questions = [q.strip() for q in response.text.split('\n') if q.strip()]
            result = questions[:10] if len(questions) >= 10 else self._get_fallback_questions(position)
            print(f"✅ Сгенерировано {len(result)} вопросов для позиции {position}")
            return result
        except Exception as e:
            print(f"❌ Ошибка генерации вопросов: {e}")
            return self._get_fallback_questions(position)
    
    def _get_fallback_questions(self, position: str) -> list:
        """Fallback вопросы на случай ошибки API"""
        print("⚠️ Используются fallback вопросы")
        return [
            f"Какие основные технологии и фреймворки вы использовали в работе с {position}?",
            "Опишите архитектуру последнего проекта, над которым работали",
            "Как вы обеспечиваете качество и тестирование кода?",
            "Расскажите о самом сложном техническом вызове в вашей карьере",
            "Как вы оптимизируете производительность приложений?",
            "Какие шаблоны проектирования вы чаще всего используете и почему?",
            "Как вы организуете работу с базой данных в своих проектах?",
            "Расскажите о вашем опыте работы с системами контроля версий",
            "Как вы подходите к рефакторингу legacy кода?",
            "Какие методы вы используете для отладки сложных проблем?"
        ]
    
    def generate_feedback(self, position: str, questions: list, answers: list) -> str:
        print(f"📊 Генерация фидбэка для позиции: {position}")
        print(f"❓ Количество вопросов: {len(questions)}")
        print(f"✅ Количество ответов: {len(answers)}")
        
        if len(questions) != len(answers):
            error_msg = f"Ошибка: количество вопросов ({len(questions)}) и ответов ({len(answers)}) не совпадает. Пожалуйста, попробуйте начать собеседование заново."
            print(f"❌ {error_msg}")
            return error_msg
        
        qa_pairs = "\n".join([
            f"ВОПРОС {i+1}: {q}\nОТВЕТ КАНДИДАТА: {a}\n" 
            for i, (q, a) in enumerate(zip(questions, answers))
        ])
        
        prompt = f"""
        Ты - старший технический специалист, проводящий анализ результатов собеседования на позицию {position}.
        
        ВОПРОСЫ И ОТВЕТЫ КАНДИДАТА:
        {qa_pairs}
        
        Проанализируй технические навыки кандидата и дай развернутую оценку по следующим критериям:
        
        1. ТЕХНИЧЕСКАЯ КОМПЕТЕНТНОСТЬ:
           - Знание языка программирования и технологий
           - Понимание архитектурных принципов
           - Опыт решения практических задач
        
        2. СИЛЬНЫЕ СТОРОНЫ:
           - Конкретные технические навыки, которые выделяют кандидата
           - Глубина знаний в ключевых областях
        
        3. ОБЛАСТИ ДЛЯ РАЗВИТИЯ:
           - Конкретные пробелы в знаниях
           - Навыки, требующие улучшения
           - Рекомендации по обучению
        
        4. ИТОГОВАЯ РЕКОМЕНДАЦИЯ:
           - Готов ли кандидат к позиции {position}
           - Конкретные аргументы за и против
           - Уровень: Junior/Middle/Senior (если применимо)
        
        Будь строгим, объективным и конструктивным. Основывай оценку только на технических ответах.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            print("✅ Фидбэк успешно сгенерирован")
            return response.text
        except Exception as e:
            error_msg = f"Ошибка при генерации фидбэка: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg

gemini_service = GeminiService()