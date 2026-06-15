import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ── Настройки ────────────────────────────────────────────
TOKEN = "8987372920:AAFCQMkD3y3EvUY7YIx02Cc_Ck5Nh0ypwZ8"
ADMIN_USERNAME = "@daniiltovpeco"  # куда слать результаты
ADMIN_CHAT_ID = None  # заполнится автоматически при первом /start от админа

# ── Шаги опроса ──────────────────────────────────────────
STEP1, STEP2, STEP3, PHONE = range(4)

logging.basicConfig(level=logging.INFO)

# ── /start ───────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN_CHAT_ID
    user = update.effective_user

    # Запоминаем chat_id админа автоматически
    if user.username and user.username.lower() == ADMIN_USERNAME.lstrip("@").lower():
        ADMIN_CHAT_ID = update.effective_chat.id

    context.user_data.clear()

    keyboard = [
        [InlineKeyboardButton("🏗 Новострой", callback_data="type_новострой")],
        [InlineKeyboardButton("🏠 Вторичка",  callback_data="type_вторичка")],
    ]
    await update.message.reply_text(
        "👋 Добро пожаловать!\n\n"
        "Я помогу подобрать недвижимость.\n"
        "Давайте начнём!\n\n"
        "📌 *Шаг 1 из 3* — Тип жилья:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STEP1

# ── Шаг 1 → выбор типа ───────────────────────────────────
async def step1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice = query.data.replace("type_", "")
    context.user_data["тип"] = choice

    keyboard = [
        [InlineKeyboardButton("1️⃣ 1-комнатная", callback_data="rooms_1")],
        [InlineKeyboardButton("2️⃣ 2-комнатная", callback_data="rooms_2")],
        [InlineKeyboardButton("3️⃣ 3-комнатная", callback_data="rooms_3")],
    ]
    await query.edit_message_text(
        f"✅ Выбрано: *{choice}*\n\n"
        "📌 *Шаг 2 из 3* — Количество комнат:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STEP2

# ── Шаг 2 → выбор комнат ─────────────────────────────────
async def step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice = query.data.replace("rooms_", "") + "-комнатная"
    context.user_data["комнаты"] = choice

    keyboard = [
        [InlineKeyboardButton("✨ Евроремонт",        callback_data="repair_евроремонт")],
        [InlineKeyboardButton("🪣 Белый вариант",     callback_data="repair_белый вариант")],
        [InlineKeyboardButton("🖌 Косметический ремонт", callback_data="repair_косметический ремонт")],
    ]
    await query.edit_message_text(
        f"✅ Выбрано: *{choice}*\n\n"
        "📌 *Шаг 3 из 3* — Состояние ремонта:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STEP3

# ── Шаг 3 → выбор ремонта → просим телефон ───────────────
async def step3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice = query.data.replace("repair_", "")
    context.user_data["ремонт"] = choice

    # Кнопка поделиться контактом
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Поделиться номером", request_contact=True)],
         [KeyboardButton("⏭ Пропустить")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await query.edit_message_text(
        f"✅ Выбрано: *{choice}*\n\n"
        "📞 Оставьте номер телефона, чтобы мы могли с вами связаться.\n"
        "_(или нажмите «Пропустить»)_",
        parse_mode="Markdown"
    )
    await query.message.reply_text(
        "👇 Нажмите кнопку ниже:",
        reply_markup=keyboard
    )
    return PHONE

# ── Получаем телефон (или пропуск) ───────────────────────
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if update.message.contact:
        phone = update.message.contact.phone_number
    elif update.message.text and update.message.text == "⏭ Пропустить":
        phone = "не указан"
    else:
        phone = update.message.text  # если написал вручную

    context.user_data["телефон"] = phone

    # Подтверждение пользователю
    await update.message.reply_text(
        "✅ *Спасибо! Ваша заявка принята.*\n\n"
        f"🏗 Тип: {context.user_data.get('тип')}\n"
        f"🛏 Комнат: {context.user_data.get('комнаты')}\n"
        f"🔨 Ремонт: {context.user_data.get('ремонт')}\n\n"
        "Мы свяжемся с вами в ближайшее время! 🤝",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

    # Отправка админу
    admin_text = (
        "🔔 *Новая заявка!*\n\n"
        f"👤 Имя: {user.full_name}\n"
        f"🆔 Username: @{user.username or 'нет'}\n"
        f"📱 Телефон: {phone}\n"
        f"🔗 Ссылка: tg://user?id={user.id}\n\n"
        f"🏗 Тип жилья: {context.user_data.get('тип')}\n"
        f"🛏 Комнат: {context.user_data.get('комнаты')}\n"
        f"🔨 Ремонт: {context.user_data.get('ремонт')}"
    )

    if ADMIN_CHAT_ID:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_text,
            parse_mode="Markdown"
        )
    else:
        # Если админ ещё не запустил бота — попробуем по username
        try:
            await context.bot.send_message(
                chat_id=ADMIN_USERNAME,
                text=admin_text,
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.warning(f"Не удалось отправить админу: {e}")

    return ConversationHandler.END

# ── Отмена ───────────────────────────────────────────────
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Отменено. Напишите /start чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ── main ─────────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()

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

    print("✅ Бот запущен! Нажми Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    main()
