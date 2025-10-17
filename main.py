import telebot
import json
import os
from dotenv import load_dotenv
from telebot import types

# --- Настройка ---
load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

NOTES_FILE = "notes.json"


# --- Вспомогательные функции ---
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


# --- Клавиатура ---
def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("/note_list", "/note_add")
    kb.row("/note_find", "/note_edit")
    kb.row("/note_del", "/note_count", "/max")
    kb.row("/sum", "/about", "/hide")
    return kb


# --- Команды ---
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    text = (
        "*Заметки-бот*\n\n"
        "Доступные команды:\n"
        "/note_add <текст>\n"
        "/note_list\n"
        "/note_find <слово>\n"
        "/note_edit <id> <новый текст>\n"
        "/note_del <id>\n"
        "/note_count\n"
        "/max\n"
        "/sum\n"
        "/about\n"
        "/hide /show"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_keyboard())


@bot.message_handler(commands=["note_add"])
def note_add(message):
    text = message.text.replace("/note_add", "").strip()
    if not text:
        bot.reply_to(message, "Укажи текст заметки: /note_add <текст>")
        return

    user_id = message.from_user.id
    notes = get_user_notes(user_id)
    note_id = len(notes) + 1
    notes.append({"id": note_id, "text": text})
    save_user_notes(user_id, notes)
    bot.reply_to(message, f"Заметка #{note_id} добавлена!")


@bot.message_handler(commands=["note_list"])
def note_list(message):
    user_id = message.from_user.id
    notes = get_user_notes(user_id)
    if not notes:
        bot.reply_to(message, "📭 Нет заметок.")
        return
    text = "\n".join([f"{n['id']}. {n['text']}" for n in notes])
    bot.reply_to(message, f"Список заметок:\n{text}")


@bot.message_handler(commands=["note_find"])
def note_find(message):
    query = message.text.replace("/note_find", "").strip().lower()
    if not query:
        bot.reply_to(message, "Укажи слово для поиска: /note_find <слово>")
        return

    user_id = message.from_user.id
    notes = get_user_notes(user_id)
    found = [n for n in notes if query in n["text"].lower()]
    if not found:
        bot.reply_to(message, "Ничего не найдено.")
    else:
        text = "\n".join([f"{n['id']}. {n['text']}" for n in found])
        bot.reply_to(message, f"Найдено:\n{text}")


@bot.message_handler(commands=["note_edit"])
def note_edit(message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Используй формат: /note_edit <id> <новый текст>")
        return

    try:
        note_id = int(parts[1])
    except ValueError:
        bot.reply_to(message, "ID должен быть числом.")
        return

    new_text = parts[2]
    user_id = message.from_user.id
    notes = get_user_notes(user_id)

    for n in notes:
        if n["id"] == note_id:
            n["text"] = new_text
            save_user_notes(user_id, notes)
            bot.reply_to(message, f"Заметка #{note_id} изменена.")
            return

    bot.reply_to(message, f"Заметка #{note_id} не найдена.")


@bot.message_handler(commands=["note_del"])
def note_del(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Используй формат: /note_del <id>")
        return

    try:
        note_id = int(parts[1])
    except ValueError:
        bot.reply_to(message, "ID должен быть числом.")
        return

    user_id = message.from_user.id
    notes = get_user_notes(user_id)
    new_notes = [n for n in notes if n["id"] != note_id]

    if len(new_notes) == len(notes):
        bot.reply_to(message, f"Заметка #{note_id} не найдена.")
    else:
        save_user_notes(user_id, new_notes)
        bot.reply_to(message, f"Заметка #{note_id} удалена.")


@bot.message_handler(commands=["note_count"])
def note_count(message):
    user_id = message.from_user.id
    notes = get_user_notes(user_id)
    bot.reply_to(message, f"Всего заметок: {len(notes)}")


@bot.message_handler(commands=["max"])
def max_note(message):
    user_id = message.from_user.id
    notes = get_user_notes(user_id)
    if not notes:
        bot.reply_to(message, "Нет заметок.")
        return
    max_note = max(notes, key=lambda n: len(n["text"]))
    bot.reply_to(message, f"Самая длинная заметка:\n\n{max_note['text']}")


@bot.message_handler(commands=["sum"])
def sum_notes(message):
    user_id = message.from_user.id
    notes = get_user_notes(user_id)
    if not notes:
        bot.reply_to(message, "Нет заметок.")
        return
    total = sum(len(n["text"]) for n in notes)
    bot.reply_to(message, f"Общая длина всех заметок: {total} символов.")


@bot.message_handler(commands=["about"])
def about(message):
    bot.reply_to(
        message,
        "Этот бот создан на Python с использованием библиотеки *pyTelegramBotAPI*.\n"
        "Автор: Ко Антон \n"
        "Код доступен на GitHub.",
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["hide"])
def hide_keyboard(message):
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Клавиатура скрыта. Чтобы вернуть — /show", reply_markup=markup)


@bot.message_handler(commands=["show"])
def show_keyboard(message):
    bot.send_message(message.chat.id, "Клавиатура включена.", reply_markup=main_keyboard())


# --- Запуск ---
bot.delete_webhook()
bot.polling(none_stop=True)
