import telebot
import json
import os
from dotenv import load_dotenv
from telebot import types


load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

NOTES_FILE = "notes.json"


def model_1(question: str) -> str:
    return f"[Модель 1] Краткий ответ: {question}"

def model_3(question: str) -> str:
    return f"[Модель 3] Подробное объяснение запроса: {question}"

def model_7(question: str) -> str:
    return (
        "[Модель 7] Бинарный поиск — это алгоритм поиска элемента "
        "в отсортированном массиве, который на каждом шаге делит массив пополам.\n\n"
        f"Запрос: {question}"
    )

MODELS = {
    1: model_1,
    3: model_3,
    7: model_7
}


def load_all_notes():
    if not os.path.exists(NOTES_FILE):
        return {}
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_all_notes(data):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_notes(user_id):
    data = load_all_notes()
    return data.get(str(user_id), [])

def save_user_notes(user_id, notes):
    data = load_all_notes()
    data[str(user_id)] = notes
    save_all_notes(data)


def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("/note_add", "/note_list")
    kb.row("/note_find", "/note_edit")
    kb.row("/note_del", "/note_count", "/max")
    kb.row("/sum", "/about")
    kb.row("/hide")
    return kb


@bot.message_handler(commands=["start", "help"])
def start(message):
    text = (
        "📘 *Учебный Telegram-бот*\n\n"
        "Команды заметок:\n"
        "/note_add <текст>\n"
        "/note_list\n"
        "/note_find <слово>\n"
        "/note_edit <id> <текст>\n"
        "/note_del <id>\n"
        "/note_count\n"
        "/max\n"
        "/sum\n\n"
        "Команды моделей:\n"
        "/ask_model <ID> <вопрос>\n\n"
        "Пример:\n"
        "`/ask_model 7 Объясни бинарный поиск`"
    )
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )


@bot.message_handler(commands=["ask_model"])
def ask_model(message):
    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        bot.reply_to(
            message,
            "❗ Формат:\n/ask_model <ID> <вопрос>\n\n"
            "Пример:\n/ask_model 7 Объясни бинарный поиск"
        )
        return

    try:
        model_id = int(parts[1])
    except ValueError:
        bot.reply_to(message, "❗ ID модели должен быть числом.")
        return

    question = parts[2]

    if model_id not in MODELS:
        bot.reply_to(message, f"⚠️ Модель с ID={model_id} не существует.")
        return

    response = MODELS[model_id](question)
    bot.reply_to(message, response)


@bot.message_handler(commands=["note_add"])
def note_add(message):
    text = message.text.replace("/note_add", "").strip()
    if not text:
        bot.reply_to(message, "❗ Используй: /note_add <текст>")
        return

    user_id = message.from_user.id
    notes = get_user_notes(user_id)
    note_id = len(notes) + 1
    notes.append({"id": note_id, "text": text})
    save_user_notes(user_id, notes)

    bot.reply_to(message, f"✅ Заметка #{note_id} добавлена")

@bot.message_handler(commands=["note_list"])
def note_list(message):
    notes = get_user_notes(message.from_user.id)
    if not notes:
        bot.reply_to(message, "📭 Нет заметок")
        return

    result = "\n".join(f"{n['id']}. {n['text']}" for n in notes)
    bot.reply_to(message, result)

@bot.message_handler(commands=["note_find"])
def note_find(message):
    query = message.text.replace("/note_find", "").strip().lower()
    notes = get_user_notes(message.from_user.id)
    found = [n for n in notes if query in n["text"].lower()]

    if not found:
        bot.reply_to(message, "Ничего не найдено")
    else:
        bot.reply_to(message, "\n".join(f"{n['id']}. {n['text']}" for n in found))

@bot.message_handler(commands=["note_edit"])
def note_edit(message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Используй: /note_edit <id> <текст>")
        return

    try:
        note_id = int(parts[1])
    except ValueError:
        bot.reply_to(message, "ID должен быть числом")
        return

    notes = get_user_notes(message.from_user.id)
    for n in notes:
        if n["id"] == note_id:
            n["text"] = parts[2]
            save_user_notes(message.from_user.id, notes)
            bot.reply_to(message, "✏️ Заметка обновлена")
            return

    bot.reply_to(message, "Заметка не найдена")

@bot.message_handler(commands=["note_del"])
def note_del(message):
    try:
        note_id = int(message.text.split()[1])
    except:
        bot.reply_to(message, "Используй: /note_del <id>")
        return

    notes = get_user_notes(message.from_user.id)
    new_notes = [n for n in notes if n["id"] != note_id]

    if len(new_notes) == len(notes):
        bot.reply_to(message, "Заметка не найдена")
    else:
        save_user_notes(message.from_user.id, new_notes)
        bot.reply_to(message, "🗑 Заметка удалена")

@bot.message_handler(commands=["note_count"])
def note_count(message):
    notes = get_user_notes(message.from_user.id)
    bot.reply_to(message, f"Всего заметок: {len(notes)}")

@bot.message_handler(commands=["max"])
def max_note(message):
    notes = get_user_notes(message.from_user.id)
    if not notes:
        bot.reply_to(message, "Нет заметок")
        return
    m = max(notes, key=lambda n: len(n["text"]))
    bot.reply_to(message, f"Самая длинная заметка:\n{m['text']}")

@bot.message_handler(commands=["sum"])
def sum_notes(message):
    notes = get_user_notes(message.from_user.id)
    total = sum(len(n["text"]) for n in notes)
    bot.reply_to(message, f"Суммарная длина: {total} символов")


@bot.message_handler(commands=["about"])
def about(message):
    bot.reply_to(
        message,
        "🤖 Учебный Telegram-бот\n"
        "Python + pyTelegramBotAPI\n"
        "Реализованы CRUD и работа с моделями"
    )

@bot.message_handler(commands=["hide"])
def hide(message):
    bot.send_message(
        message.chat.id,
        "Клавиатура скрыта",
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(commands=["show"])
def show(message):
    bot.send_message(
        message.chat.id,
        "Клавиатура включена",
        reply_markup=main_keyboard()
    )


bot.delete_webhook()
bot.polling(none_stop=True)
