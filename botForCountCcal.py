import sqlite3
from datetime import datetime

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# НАСТРОЙКИ
# =========================

TOKEN = "8451168162:AAF_4a1Icz3FnUowMbas-BOoKuK9WjGDCXc"
DAILY_LIMIT = 1500

# =========================
# БАЗА ДАННЫХ
# =========================

conn = sqlite3.connect("calories.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS calories (
    chat_id INTEGER,
    date TEXT,
    consumed INTEGER
)
""")

conn.commit()

# =========================
# ВСПОМОГАТЕЛЬНОЕ
# =========================

def get_today():
    return datetime.now().strftime("%Y-%m-%d")


def get_consumed(chat_id):
    today = get_today()

    cursor.execute(
        "SELECT consumed FROM calories WHERE chat_id=? AND date=?",
        (chat_id, today),
    )

    result = cursor.fetchone()

    if result:
        return result[0]

    cursor.execute(
        "INSERT INTO calories (chat_id, date, consumed) VALUES (?, ?, ?)",
        (chat_id, today, 0),
    )

    conn.commit()

    return 0


def update_consumed(chat_id, value):
    today = get_today()

    cursor.execute(
        "UPDATE calories SET consumed=? WHERE chat_id=? AND date=?",
        (value, chat_id, today),
    )

    conn.commit()

# =========================
# КОМАНДЫ
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет 👋\n\n"
        "Я считаю КАЛОРИИ для ВАШЕГО ЧАТА 🔥\n\n"
        "Напиши:\n"
        "@бот 450\n"
        "и я добавлю в общий счёт"
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    consumed = get_consumed(chat_id)
    remaining = DAILY_LIMIT - consumed

    await update.message.reply_text(
        f"🍔 Съедено в чате: {consumed} ккал\n"
        f"🔥 Осталось: {remaining} ккал"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    today = get_today()

    cursor.execute(
        "UPDATE calories SET consumed=0 WHERE chat_id=? AND date=?",
        (chat_id, today),
    )

    conn.commit()

    await update.message.reply_text(
        "Счетчик чата сброшен ✅"
    )

# =========================
# ОСНОВНАЯ ЛОГИКА
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or not message.text:
        return

    text = message.text
    bot_username = context.bot.username.lower()

    # реагируем только если упомянули бота
    if f"@{bot_username}" not in text.lower():
        return

    chat_id = update.effective_chat.id

    cleaned_text = text.lower().replace(f"@{bot_username}", "").strip()

    if not cleaned_text.isdigit():
        await message.reply_text(
            "После @бота нужно число 🙂\n\nПример:\n@бот 450"
        )
        return

    calories = int(cleaned_text)

    consumed = get_consumed(chat_id)
    new_total = consumed + calories

    update_consumed(chat_id, new_total)

    remaining = DAILY_LIMIT - new_total

    # =========================
    # ЦЕЛЬ ДОСТИГНУТА
    # =========================

    if new_total >= DAILY_LIMIT:
        await message.reply_text(
            f"🔥 ЦЕЛЬ ДОСТИГНУТА!\n"
            f"Вы молодцы ❤️❤️❤️\n\n"
            f"🍔 Всего в чате: {new_total} ккал\n"
            f"🎯 Лимит: {DAILY_LIMIT} ккал"
        )
        return

    # обычный ответ
    await message.reply_text(
        f"➕ Добавлено: {calories} ккал\n\n"
        f"🍔 Всего в чате: {new_total} ккал\n"
        f"🔥 Осталось: {remaining} ккал"
    )

# =========================
# ЗАПУСК
# =========================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("reset", reset))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("Бот запущен ✅")
    app.run_polling()


if __name__ == "__main__":
    main()