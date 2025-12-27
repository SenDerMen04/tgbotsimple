import os
import logging
import telebot
from telebot import types
from dotenv import load_dotenv

import db
import openrouter
from logging_config import setup_logging

load_dotenv()
setup_logging()
log = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("Нет TOKEN в .env")

bot = telebot.TeleBot(TOKEN)
db.init_db()

INSTRUMENTS = {
    "vocal": "Вокал 🎤",
    "guitar": "Гитара 🎸",
    "bass": "Бас 🎵",
    "drums": "Барабаны 🥁",
    "keys": "Клавиши 🎹",
    "other": "Другое 🎶"
}

# ===== KEYBOARDS =====
def kb_start():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🎤 Я музыкант", "🎶 У меня есть группа")
    return kb

def kb_main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("👤 Профиль", "✏️ Редактировать профиль")
    kb.row("📋 Мои заявки", "❌ Отменить заявку")
    kb.row("➕ Создать заявку", "🔍 Найти музыкантов")
    kb.row("ℹ️ О боте")
    return kb

def kb_instruments():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    items = list(INSTRUMENTS.keys())
    for i in range(0, len(items), 2):
        kb.row(*[INSTRUMENTS[k] for k in items[i:i+2]])
    return kb

# ===== START =====
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎸 BandFinderBot\n\nКто вы?",
        reply_markup=kb_start()
    )

@bot.message_handler(commands=["menu"])
def menu(message):
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=kb_main_menu())

# ===== BUTTON HANDLERS =====
@bot.message_handler(func=lambda m: m.text in ["🎤 Я музыкант", "🎶 У меня есть группа"])
def handle_start_buttons(message):
    if message.text == "🎤 Я музыкант":
        musician_start(message)
    else:
        band_owner_start(message)

def band_owner_start(message):
    bot.send_message(
        message.chat.id,
        "🎼 Отлично! Вы можете создавать заявки для поиска музыкантов или смотреть свои заявки.",
        reply_markup=kb_main_menu()
    )

@bot.message_handler(func=lambda m: m.text in ["👤 Профиль", "✏️ Редактировать профиль", 
                                               "📋 Мои заявки", "❌ Отменить заявку",
                                               "➕ Создать заявку", "🔍 Найти музыкантов",
                                               "ℹ️ О боте"])
def handle_menu_buttons(message):
    text = message.text
    if text == "👤 Профиль":
        profile(message)
    elif text == "✏️ Редактировать профиль":
        edit_profile(message)
    elif text == "📋 Мои заявки":
        my_requests(message)
    elif text == "❌ Отменить заявку":
        cancel_request(message)
    elif text == "➕ Создать заявку":
        create_request_btn(message)
    elif text == "🔍 Найти музыкантов":
        search_musicians_btn(message)
    elif text == "ℹ️ О боте":
        about_bot(message)

# ===== HELPERS =====
def ask_location(chat_id):
    msg = bot.send_message(chat_id, "📍 Укажите ваше местоположение (город, район, адрес):")
    return msg

# ===== MUSICIAN FLOW =====
def musician_start(message):
    msg = bot.send_message(message.chat.id, "Ваш инструмент:", reply_markup=kb_instruments())
    bot.register_next_step_handler(msg, musician_instrument)

def musician_instrument(message):
    instrument = next((k for k, v in INSTRUMENTS.items() if v == message.text), "other")
    msg = bot.send_message(message.chat.id, "Сколько лет вы играете?")
    bot.register_next_step_handler(msg, musician_experience, instrument)

def musician_experience(message, instrument):
    try:
        exp = int(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "Введите число.")
        return
    msg = bot.send_message(message.chat.id, "Укажите жанры (через запятую):")
    bot.register_next_step_handler(msg, musician_genres, instrument, exp)

def musician_genres(message, instrument, exp):
    genres = message.text
    msg = bot.send_message(message.chat.id, "Напишите немного о себе:")
    bot.register_next_step_handler(msg, musician_about, instrument, exp, genres)

def musician_about(message, instrument, exp, genres):
    about = message.text
    msg = ask_location(message.chat.id)
    bot.register_next_step_handler(msg, musician_location, instrument, exp, genres, about)

def musician_location(message, instrument, exp, genres, about):
    location_text = message.text.strip()
    if not location_text:
        msg = ask_location(message.chat.id)
        bot.register_next_step_handler(msg, musician_location, instrument, exp, genres, about)
        return

    db.register_musician(
        message.from_user.id,
        instrument,
        exp,
        genres,
        location_text,
        about
    )

    bot.send_message(
        message.chat.id,
        "✅ Профиль музыканта сохранён!",
        reply_markup=kb_main_menu()
    )

# ===== BAND / CREATE REQUEST FLOW =====
def create_request_btn(message):
    msg = bot.send_message(message.chat.id, "Кого ищете? Выберите инструмент:", reply_markup=kb_instruments())
    bot.register_next_step_handler(msg, band_instrument)

def band_instrument(message):
    instrument = next((k for k, v in INSTRUMENTS.items() if v == message.text), "other")
    msg = bot.send_message(message.chat.id, "Минимальный стаж музыканта (лет):")
    bot.register_next_step_handler(msg, band_experience, instrument)

def band_experience(message, instrument):
    try:
        min_exp = int(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "Введите число лет стажа.")
        return
    msg = ask_location(message.chat.id)
    bot.register_next_step_handler(msg, band_location, instrument, min_exp)

def band_location(message, instrument, min_exp):
    location_text = message.text.strip()
    if not location_text:
        msg = ask_location(message.chat.id)
        bot.register_next_step_handler(msg, band_location, instrument, min_exp)
        return
    msg = bot.send_message(message.chat.id, "Опишите группу (жанр, опыт, цели):", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, band_description, instrument, min_exp, location_text)

def band_description(message, instrument, min_exp, location_text):
    description = message.text or "Без описания"
    genre = openrouter.analyze_band_description(description)["genre"]

    req_id = db.create_band_request(
        message.from_user.id,
        instrument,
        genre,
        description,
        location_text,
        min_exp
    )

    # Поиск музыкантов с фильтром по стажу
    musicians = db.find_musicians_by_text_location(instrument, location_text, min_exp)

    bot.send_message(
        message.chat.id,
        f"🎼 Заявка создана\n🎧 Жанр: {genre}\n👥 Найдено: {len(musicians)}",
        reply_markup=kb_main_menu()
    )

    for m in musicians:
        send_musician_alert(m, req_id, genre)

def send_musician_alert(m, req_id, genre):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🤝 Откликнуться", callback_data=f"accept_{req_id}"))
    bot.send_message(
        m["telegram_id"],
        f"🎸 Группа ищет музыканта\n🎧 Жанр: {genre}\n📍 {m['location_text']}\n🎼 Опыт: {m['experience']} лет\n💬 О себе: {m['about']}",
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("accept_"))
def accept(call):
    req_id = int(call.data.split("_")[1])
    if not db.assign_musician(req_id, call.from_user.id):
        bot.answer_callback_query(call.id, "Заявка уже закрыта", show_alert=True)
        return
    req = db.get_band_request(req_id)
    bot.send_message(req["band_id"], f"🎉 Музыкант найден!\nВы откликнулись!")
    bot.answer_callback_query(call.id, "Вы откликнулись!")

# ===== PROFILE =====
def profile(message):
    user = db.get_musician_profile(message.from_user.id)
    if not user:
        bot.send_message(message.chat.id, "Вы ещё не зарегистрированы как музыкант.")
        return
    bot.send_message(
        message.chat.id,
        f"🎸 Ваш профиль:\nИнструмент: {user['instrument']}\nОпыт: {user['experience']} лет\nЖанры: {user['genres']}\nЛокация: {user['location_text']}\n💬 О себе: {user['about']}"
    )

# ===== EDIT PROFILE =====
def edit_profile(message):
    msg = bot.send_message(message.chat.id, "Что хотите изменить? (инструмент/опыт/жанры/о себе)")
    bot.register_next_step_handler(msg, edit_choice)

def edit_choice(message):
    choice = message.text.lower()
    if choice == "инструмент":
        msg = bot.send_message(message.chat.id, "Выберите новый инструмент:", reply_markup=kb_instruments())
        bot.register_next_step_handler(msg, edit_instrument)
    elif choice == "опыт":
        msg = bot.send_message(message.chat.id, "Введите новый опыт (лет):")
        bot.register_next_step_handler(msg, edit_experience)
    elif choice == "жанры":
        msg = bot.send_message(message.chat.id, "Введите новые жанры через запятую:")
        bot.register_next_step_handler(msg, edit_genres)
    elif choice == "о себе":
        msg = bot.send_message(message.chat.id, "Напишите о себе:")
        bot.register_next_step_handler(msg, edit_about)
    else:
        bot.send_message(message.chat.id, "Неверный выбор.")

def edit_instrument(message):
    instrument = next((k for k, v in INSTRUMENTS.items() if v == message.text), "other")
    with db._connect() as conn:
        conn.execute("UPDATE musicians SET instrument=? WHERE telegram_id=?", (instrument, message.from_user.id))
        conn.commit()
    bot.send_message(message.chat.id, f"Инструмент обновлён на {message.text}")

def edit_experience(message):
    try:
        exp = int(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "Введите число.")
        return
    with db._connect() as conn:
        conn.execute("UPDATE musicians SET experience=? WHERE telegram_id=?", (exp, message.from_user.id))
        conn.commit()
    bot.send_message(message.chat.id, f"Опыт обновлён на {exp} лет")

def edit_genres(message):
    genres = message.text
    with db._connect() as conn:
        conn.execute("UPDATE musicians SET genres=? WHERE telegram_id=?", (genres, message.from_user.id))
        conn.commit()
    bot.send_message(message.chat.id, f"Жанры обновлены: {genres}")

def edit_about(message):
    about = message.text
    with db._connect() as conn:
        conn.execute("UPDATE musicians SET about=? WHERE telegram_id=?", (about, message.from_user.id))
        conn.commit()
    bot.send_message(message.chat.id, f"О себе обновлено!")

# ===== MY REQUESTS =====
def my_requests(message):
    requests = db.get_band_requests(message.from_user.id)
    if not requests:
        bot.send_message(message.chat.id, "У вас нет активных заявок.")
        return
    text = "📋 Ваши заявки:\n\n"
    for r in requests:
        status = "Закрыта" if r["accepted_by"] else "Ожидание"
        text += f"#{r['id']} | {r['instrument']} | {r['genre']} | {status}\n"
    bot.send_message(message.chat.id, text)

# ===== CANCEL =====
def cancel_request(message):
    msg = bot.send_message(message.chat.id, "Введите ID заявки для отмены:")
    bot.register_next_step_handler(msg, cancel_confirm)

def cancel_confirm(message):
    try:
        req_id = int(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "Неверный ID.")
        return
    with db._connect() as conn:
        cur = conn.execute("DELETE FROM band_requests WHERE id=? AND band_id=?", (req_id, message.from_user.id))
        conn.commit()
    if cur.rowcount:
        bot.send_message(message.chat.id, f"Заявка #{req_id} отменена.")
    else:
        bot.send_message(message.chat.id, "Не удалось отменить заявку.")

# ===== SEARCH MUSICIANS =====
def search_musicians_btn(message):
    msg = bot.send_message(message.chat.id, "Введите инструмент и минимальный стаж (через пробел), например: Гитара 5")
    bot.register_next_step_handler(msg, search_musicians_by_instrument)

def search_musicians_by_instrument(message):
    try:
        parts = message.text.strip().split()
        instrument_text = parts[0]
        min_exp = int(parts[1])
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "Неверный формат. Пример: Гитара 5")
        return

    musicians = db.find_musicians_by_text_location(instrument_text, "%", min_exp)
    if not musicians:
        bot.send_message(message.chat.id, "Музыкантов не найдено.")
        return
    text = "Найденные музыканты:\n"
    for m in musicians:
        text += f"🎸 {m['instrument']} | {m['experience']} лет | 💬 {m['about']} | 📍 {m['location_text']}\n"
    bot.send_message(message.chat.id, text)

# ===== ABOUT BOT =====
def about_bot(message):
    text = (
        "🎸 BandFinderBot\n\n"
        "Команды:\n"
        "/start - начать работу\n"
        "/menu - открыть главное меню\n\n"
        "В меню можно:\n"
        "- 👤 Профиль: посмотреть ваш профиль музыканта\n"
        "- ✏️ Редактировать профиль: изменить инструмент, опыт, жанры, описание о себе\n"
        "- 📋 Мои заявки: посмотреть заявки вашей группы\n"
        "- ❌ Отменить заявку: удалить заявку группы\n"
        "- ➕ Создать заявку: создать заявку на поиск музыканта\n"
        "- 🔍 Найти музыкантов: поиск музыкантов по инструменту и стажу\n"
        "- ℹ️ О боте: информация и список команд"
    )
    bot.send_message(message.chat.id, text)

# ===== RUN =====
if __name__ == "__main__":
    print("🎸 BandFinderBot запущен")
    bot.infinity_polling(skip_pending=True)
