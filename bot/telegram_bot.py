import os
import requests
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler
)
import logging
from datetime import datetime

# Настройки
API_BASE_URL = "http://127.0.0.1:8000/api"  # URL вашего FastAPI
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_BOT_TOKEN = "81....."

# Состояния разговора
START, POSITION, INTERVIEW = range(3)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.setup_handlers()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начало работы с ботом"""
        user = update.message.from_user
        context.user_data['user_id'] = str(user.id)
        
        await update.message.reply_text(
            "🧠 Добро пожаловать в Нейро-HR бот!\n\n"
            "Я проведу техническое собеседование и дам подробную обратную связь.\n\n"
            "Для начала собеседования отправьте /interview\n"
            "Для просмотра истории отправьте /history",
            reply_markup=ReplyKeyboardRemove()
        )
        return START

    async def start_interview(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начало нового собеседования"""
        try:
            user_id = context.user_data.get('user_id')
            
            # Создаем сессию через API
            response = requests.post(f"{API_BASE_URL}/start_interview", json={
                "start": True,
                "user_id": user_id,
                "platform": "telegram"
            })
            
            if response.status_code == 200:
                data = response.json()
                context.user_data['session_id'] = data['session_id']
                
                await update.message.reply_text(
                    data['message'],
                    reply_markup=ReplyKeyboardRemove()
                )
                return POSITION
            else:
                await update.message.reply_text("❌ Ошибка при запуске собеседования. Попробуйте позже.")
                return START
        except Exception as e:
            logger.error(f"Error starting interview: {e}")
            await update.message.reply_text("❌ Ошибка при запуске собеседования. Попробуйте позже.")
            return START

    async def set_position(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Установка позиции для собеседования"""
        try:
            position = update.message.text
            session_id = context.user_data.get('session_id')
            user_id = context.user_data.get('user_id')
            
            # Устанавливаем позицию через API
            response = requests.post(f"{API_BASE_URL}/set_position", json={
                "session_id": session_id,
                "position": position,
                "user_id": user_id
            })
            
            if response.status_code == 200:
                data = response.json()
                context.user_data['current_question'] = 1
                context.user_data['total_questions'] = data['total_questions']
                context.user_data['position'] = data['position']
                
                await update.message.reply_text(
                    f"🎯 Позиция: {data['position']}\n"
                    f"📊 Вопрос {data['current_question']} из {data['total_questions']}:\n\n"
                    f"{data['question']}",
                    reply_markup=ReplyKeyboardRemove()
                )
                return INTERVIEW
            else:
                await update.message.reply_text("❌ Ошибка при установке позиции. Попробуйте еще раз.")
                return POSITION
        except Exception as e:
            logger.error(f"Error setting position: {e}")
            await update.message.reply_text("❌ Ошибка при установке позиции. Попробуйте еще раз.")
            return POSITION

    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ответа на вопрос"""
        try:
            answer = update.message.text
            session_id = context.user_data.get('session_id')
            user_id = context.user_data.get('user_id')

            # Отправляем ответ через API
            response = requests.post(f"{API_BASE_URL}/answer_question", json={
                "session_id": session_id,
                "answer": answer,
                "user_id": user_id
            })

            if response.status_code == 200:
                data = response.json()

                if data.get('interview_complete'):
                    # Собеседование завершено
                    feedback = data['feedback']

                    # Проверяем, не является ли фидбэк ошибкой
                    if "Ошибка:" in feedback:
                        await update.message.reply_text(
                            "❌ Произошла ошибка при обработке результатов. Пожалуйста, начните собеседование заново.\n\n"
                            "Для нового собеседования отправьте /interview",
                            reply_markup=ReplyKeyboardRemove()
                        )
                        return START

                    # Разбиваем фидбэк на части если он слишком длинный для Telegram
                    if len(feedback) > 4096:
                        for i in range(0, len(feedback), 4096):
                            part = feedback[i:i + 4096]
                            await update.message.reply_text(part)
                    else:
                        await update.message.reply_text(feedback)

                    await update.message.reply_text(
                        "✅ Собеседование завершено!\n\n"
                        "Для нового собеседования отправьте /interview\n"
                        "Для просмотра истории отправьте /history",
                        reply_markup=ReplyKeyboardRemove()
                    )
                    return START
                else:
                    # Следующий вопрос
                    context.user_data['current_question'] = data['current_question']

                    await update.message.reply_text(
                        f"📊 Вопрос {data['current_question']} из {data['total_questions']}:\n\n"
                        f"{data['question']}",
                        reply_markup=ReplyKeyboardRemove()
                    )
                    return INTERVIEW
            else:
                await update.message.reply_text("❌ Ошибка при обработке ответа. Попробуйте еще раз.")
                return INTERVIEW
        except Exception as e:
            logger.error(f"Error handling answer: {e}")
            await update.message.reply_text("❌ Ошибка при обработке ответа. Попробуйте еще раз.")
            return INTERVIEW

    async def show_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать историю собеседований"""
        try:
            user_id = context.user_data.get('user_id')
            
            response = requests.get(f"{API_BASE_URL}/user/{user_id}/sessions")
            
            if response.status_code == 200:
                data = response.json()
                sessions = data.get('sessions', [])
                
                if not sessions:
                    await update.message.reply_text("📝 У вас еще не было собеседований.")
                    return START
                
                message = "📋 История ваших собеседований:\n\n"
                
                for session in sessions[-5:]:  # Последние 5 собеседований
                    status = "✅ Завершено" if session['status'] == 'completed' else "🟡 В процессе"
                    date = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00')).strftime("%d.%m.%Y %H:%M")
                    message += f"• {session['position']} - {status}\n"
                    message += f"  Дата: {date}\n"
                    if session['status'] == 'completed':
                        message += f"  Вопросов: {len(session['questions'])}\n\n"
                
                await update.message.reply_text(message)
            else:
                await update.message.reply_text("❌ Ошибка при получении истории.")
        except Exception as e:
            logger.error(f"Error showing history: {e}")
            await update.message.reply_text("❌ Ошибка при получении истории.")
        
        return START

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отмена собеседования"""
        await update.message.reply_text(
            "Собеседование отменено. Для начала нового отправьте /start",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    def setup_handlers(self):
        """Настройка обработчиков"""
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                START: [
                    CommandHandler("interview", self.start_interview),
                    CommandHandler("history", self.show_history),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.start)
                ],
                POSITION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_position)
                ],
                INTERVIEW: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_answer)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        self.application.add_handler(conv_handler)

    def run(self):
        """Запуск бота"""
        print("🤖 Telegram бот запущен...")
        self.application.run_polling()

if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN не установлен в environment variables")
        print("❌ Убедитесь, что переменная TELEGRAM_BOT_TOKEN установлена в .env файле")
        exit(1)
    
    bot = TelegramBot()
    bot.run()