import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

logging.basicConfig(level=logging.INFO)

TOKEN = "8987372920:AAFCQMkD3y3EvUY7YIx02Cc_Ck5Nh0ypwZ8"
ADMIN_CHAT_ID = 7023725772  # Замени на свой ID из @userinfobot

STEP1, STEP2, STEP3, PHONE = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("🏗 Новострой", callback_data="type_новострой")],
        [InlineKeyboardButton("🏠 Вторичка", callback_data="type_вторичка")],
    ]
    await update.message.reply_text(
        "👋 Добро пожаловать!\n\nПомогу подобрать недвижимость.\n\n📌 *Шаг 1 из 3* — Тип жилья:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STEP1

async def step1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["тип"] = query.data.replace("type_", "")
    keyboard = [
        [InlineKeyboardButton("1️⃣ 1-комнатная", callback_data="rooms_1")],
        [InlineKeyboardButton("2️⃣ 2-комнатная", callback_data="rooms_2")],
        [InlineKeyboardButton("3️⃣ 3-комнатная", callback_data="rooms_3")],
    ]
    await query.edit_message_text(
        f"✅ Выбрано: *{context.user_data['тип']}*\n\n📌 *Шаг 2 из 3* — Количество комнат:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STEP2

async def step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["комнаты"] = query.data.replace("rooms_", "") + "-комнатная"
    keyboard = [
        [InlineKeyboardButton("✨ Евроремонт", callback_data="repair_евроремонт")],
        [InlineKeyboardButton("🪣 Белый вариант", callback_data="repair_белый вариант")],
        [InlineKeyboardButton("🖌 Косметический ремонт", callback_data="repair_косметический ремонт")],
    ]
    await query.edit_message_text(
        f"✅ Выбрано: *{context.user_data['комнаты']}*\n\n📌 *Шаг 3 из 3* — Состояние ремонта:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STEP3

async def step3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["ремонт"] = query.data.replace("repair_", "")
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Поделиться номером", request_contact=True)],
         [KeyboardButton("⏭ Пропустить")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await query.edit_message_text(
        f"✅ Выбрано: *{context.user_data['ремонт']}*\n\n📞 Оставьте номер телефона для связи.\n_(или нажмите «Пропустить»)_",
        parse_mode="Markdown"
    )
    await query.message.reply_text("👇 Нажмите кнопку:", reply_markup=keyboard)
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if update.message.contact:
        phone = update.message.contact.phone_number
    elif update.message.text == "⏭ Пропустить":
        phone = "не указан"
    else:
        phone = update.message.text

    await update.message.reply_text(
        "✅ *Спасибо! Заявка принята.*\n\n"
        f"🏗 Тип: {context.user_data.get('тип')}\n"
        f"🛏 Комнат: {context.user_data.get('комнаты')}\n"
        f"🔨 Ремонт: {context.user_data.get('ремонт')}\n\n"
        "Мы свяжемся с вами! 🤝",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

    admin_text = (
        "🔔 *Новая заявка!*\n\n"
        f"👤 Имя: {user.full_name}\n"
        f"🆔 Username: @{user.username or 'нет'}\n"
        f"📱 Телефон: {phone}\n\n"
        f"🏗 Тип: {context.user_data.get('тип')}\n"
        f"🛏 Комнат: {context.user_data.get('комнаты')}\n"
        f"🔨 Ремонт: {context.user_data.get('ремонт')}"
    )

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text, parse_mode="Markdown")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено. Напишите /start чтобы начать заново.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STEP1: [CallbackQueryHandler(step1, pattern="^type_")],
            STEP2: [CallbackQueryHandler(step2, pattern="^rooms_")],
            STEP3: [CallbackQueryHandler(step3, pattern="^repair_")],
            PHONE: [
                MessageHandler(filters.CONTACT, get_phone),
                MessageHandler(filters.Regex("^⏭ Пропустить$"), get_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)
    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
