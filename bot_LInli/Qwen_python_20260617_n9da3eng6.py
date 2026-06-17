import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters
)
from dotenv import load_dotenv
from cases import CASES, get_case

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния диалога
SELECTING_CASE, INVESTIGATING, FINAL_ANSWER = range(3)

# Хранилище прогресса пользователей
user_progress = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Начать расследование", callback_data="start_case")],
        [InlineKeyboardButton("📋 Список дел", callback_data="list_cases")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🕵️ *Добро пожаловать в Детективное Агентство!*\n\n"
        "Я — ваш помощник в раскрытии запутанных дел.\n"
        "Собирайте улики, допрашивайте подозреваемых и находите преступника!\n\n"
        "Выберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "start_case":
        await show_case_list(query)
    elif query.data == "list_cases":
        await show_case_list(query)
    elif query.data == "about":
        await query.edit_message_text(
            "🕵️ *Детектив-бот v1.0*\n\n"
            "Создан для любителей головоломок и детективов.\n"
            "В базе 3 дела. Новые расследования — скоро!\n\n"
            "Автор идеи: ты 😎",
            parse_mode='Markdown'
        )
    elif query.data.startswith("case_"):
        case_id = int(query.data.split("_")[1])
        await start_case(query, case_id)
    elif query.data.startswith("suspect_"):
        suspect_num = query.data.split("_")[1]
        await investigate_suspect(query, suspect_num)
    elif query.data.startswith("solve_"):
        await ask_for_solution(query)
    elif query.data.startswith("answer_"):
        answer = int(query.data.split("_")[1])
        await check_solution(query, answer)
    elif query.data == "back_to_menu":
        await start(query, context)


async def show_case_list(query):
    keyboard = []
    for case in CASES:
        keyboard.append([InlineKeyboardButton(case["title"], callback_data=f"case_{case['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")])
    
    await query.edit_message_text(
        "📋 *Выберите дело для расследования:*\n\n"
        "Каждое дело содержит:\n"
        "• Описание преступления\n"
        "• 3 подозреваемых\n"
        "• Возможность допроса каждого\n"
        "• Финальный выбор преступника",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def start_case(query, case_id):
    case = get_case(case_id)
    if not case:
        await query.edit_message_text("❌ Дело не найдено")
        return
    
    user_progress[query.from_user.id] = {
        "case_id": case_id,
        "interrogated": set()
    }
    
    keyboard = [
        [InlineKeyboardButton("👤 Допросить подозреваемого 1", callback_data="suspect_1")],
        [InlineKeyboardButton("👤 Допросить подозреваемого 2", callback_data="suspect_2")],
        [InlineKeyboardButton("👤 Допросить подозреваемого 3", callback_data="suspect_3")],
        [InlineKeyboardButton("⚖️ Вынести вердикт", callback_data=f"solve_{case_id}")]
    ]
    
    await query.edit_message_text(
        f"*{case['title']}*\n\n{case['intro']}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def investigate_suspect(query, suspect_num):
    user_id = query.from_user.id
    progress = user_progress.get(user_id)
    
    if not progress:
        await query.edit_message_text("❌ Сначала выберите дело")
        return
    
    case = get_case(progress["case_id"])
    clue = case["clues"].get(suspect_num)
    
    progress["interrogated"].add(suspect_num)
    
    interrogated_count = len(progress["interrogated"])
    
    keyboard = []
    for i in ["1", "2", "3"]:
        status = "✅ " if i in progress["interrogated"] else "👤 "
        keyboard.append([InlineKeyboardButton(f"{status}Подозреваемый {i}", callback_data=f"suspect_{i}")])
    keyboard.append([InlineKeyboardButton("⚖️ Вынести вердикт", callback_data=f"solve_{case['case_id'] if 'case_id' in case else case['id']}")])
    
    await query.edit_message_text(
        f"{clue}\n\n_Допрошено подозреваемых: {interrogated_count}/3_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def ask_for_solution(query):
    user_id = query.from_user.id
    progress = user_progress.get(user_id)
    
    if not progress:
        await query.edit_message_text("❌ Сначала выберите дело")
        return
    
    interrogated = len(progress["interrogated"])
    warning = ""
    if interrogated < 3:
        warning = f"\n\n⚠️ _Вы допросили только {interrogated}/3 подозреваемых. Уверены в выборе?_"
    
    keyboard = [
        [InlineKeyboardButton("👤 Подозреваемый 1", callback_data="answer_1")],
        [InlineKeyboardButton("👤 Подозреваемый 2", callback_data="answer_2")],
        [InlineKeyboardButton("👤 Подозреваемый 3", callback_data="answer_3")],
        [InlineKeyboardButton("🔙 Вернуться к уликам", callback_data=f"case_{progress['case_id']}")]
    ]
    
    await query.edit_message_text(
        f"⚖️ *Кто преступник?*\n\nВыберите подозреваемого:{warning}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def check_solution(query, answer):
    user_id = query.from_user.id
    progress = user_progress.get(user_id)
    
    if not progress:
        await query.edit_message_text("❌ Сначала выберите дело")
        return
    
    case = get_case(progress["case_id"])
    
    if answer == case["answer"]:
        keyboard = [
            [InlineKeyboardButton("🔍 Новое дело", callback_data="start_case")],
            [InlineKeyboardButton("🏠 В главное меню", callback_data="back_to_menu")]
        ]
        await query.edit_message_text(
            case["solution"],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        keyboard = [
            [InlineKeyboardButton("⚖️ Попробовать снова", callback_data=f"solve_{case['id']}")],
            [InlineKeyboardButton("🔙 К уликам", callback_data=f"case_{case['id']}")]
        ]
        await query.edit_message_text(
            case["wrong"],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🕵️ *Команды бота:*\n\n"
        "/start — начать работу\n"
        "/help — помощь\n"
        "/cases — список дел\n\n"
        "Или просто нажимайте на кнопки! 😉",
        parse_mode='Markdown'
    )


async def cases_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for case in CASES:
        keyboard.append([InlineKeyboardButton(case["title"], callback_data=f"case_{case['id']}")])
    
    await update.message.reply_text(
        "📋 *Список доступных дел:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN не установлен в переменных окружения!")
    
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cases", cases_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🚀 Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()