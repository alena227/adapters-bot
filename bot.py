import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from sheets import save_partnership_response, save_meeting_response
from config import PARTNERSHIP_MEETINGS, MEETING_PERIODS, ACTIVE_PERIODS, PERIOD_MEETINGS

load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =============================================================================
# СОСТОЯНИЯ ДИАЛОГА
# =============================================================================
(
    CHOOSE_TYPE,
    # Пробное напарничество
    P_MEETING, P_YOUR_NAME, P_PARTNER_NAME, P_EASE,
    P_LIKED, P_DISLIKED, P_RESPONSIBILITIES, P_RATING, P_COMMENTS,
    # Собрания
    M_PERIOD, M_NUMBER, M_LECTURE_RATING, M_LECTURE_LIKED,
    M_LECTURE_DISLIKED, M_INT1_RATING, M_INT1_CONDUCTOR,
    M_INT1_LIKED, M_INT1_DISLIKED, M_INT2_RATING, M_INT2_CONDUCTOR,
    M_INT2_LIKED, M_INT2_DISLIKED, M_COMMENTS,
) = range(24)

# =============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================================

def rating_keyboard(include_zero: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура оценки от 1 до 10 (опционально с кнопкой «Не было»)."""
    rows = []
    if include_zero:
        rows.append([InlineKeyboardButton("❌ Не было", callback_data="0")])
    rows.append([InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(1, 6)])
    rows.append([InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(6, 11)])
    return InlineKeyboardMarkup(rows)


def make_keyboard(options: dict, cols: int = 1) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру из словаря {callback_data: label}."""
    items = list(options.items())
    rows = []
    for i in range(0, len(items), cols):
        rows.append([
            InlineKeyboardButton(label, callback_data=key)
            for key, label in items[i : i + cols]
        ])
    return InlineKeyboardMarkup(rows)


async def _answer(update: Update, text: str, reply_markup=None):
    """Универсальная отправка — работает и с callback, и с обычным сообщением."""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


# =============================================================================
# СТАРТ / ВЫБОР ТИПА
# =============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Пробное напарничество", callback_data="partnership")],
        [InlineKeyboardButton("📋 Собрание", callback_data="meeting")],
    ])
    text = (
        "Привет! Это бот обратной связи\n"
        "Общественного Института Адаптеры ИКНК Политех.\n\n"
        "Выбери тип обратной связи:"
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=keyboard)
    else:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
    return CHOOSE_TYPE


async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "partnership":
        await query.edit_message_text(
            "Выбери собрание, по напарнику которого даёшь обратную связь:",
            reply_markup=make_keyboard(PARTNERSHIP_MEETINGS, cols=2),
        )
        return P_MEETING
    else:
        await query.edit_message_text(
            "Выбери период обучения, в котором было собрание:",
            reply_markup=make_keyboard(MEETING_PERIODS),
        )
        return M_PERIOD


# =============================================================================
# ВЕТКА: ПРОБНОЕ НАПАРНИЧЕСТВО
# =============================================================================

async def p_meeting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["meeting_key"] = query.data
    context.user_data["meeting_label"] = PARTNERSHIP_MEETINGS[query.data]
    await query.edit_message_text("Введи свою фамилию и имя:")
    return P_YOUR_NAME


async def p_your_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["your_name"] = update.message.text.strip()
    await update.message.reply_text("Введи фамилию и имя своего напарника:")
    return P_PARTNER_NAME


async def p_partner_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["partner_name"] = update.message.text.strip()
    await update.message.reply_text(
        "Насколько легко тебе было общаться с напарником? (от 1 до 10)",
        reply_markup=rating_keyboard(),
    )
    return P_EASE


async def p_ease(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["ease"] = query.data
    await query.edit_message_text("Что тебе понравилось в работе с напарником?")
    return P_LIKED


async def p_liked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["liked"] = update.message.text.strip()
    await update.message.reply_text("А что не понравилось?")
    return P_DISLIKED


async def p_disliked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["disliked"] = update.message.text.strip()
    await update.message.reply_text(
        "Равномерно ли были распределены обязанности между вами?\n"
        "Насколько ответственно твой напарник подошёл к работе?"
    )
    return P_RESPONSIBILITIES


async def p_responsibilities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["responsibilities"] = update.message.text.strip()
    await update.message.reply_text(
        "Оцени своего напарника (от 1 до 10):",
        reply_markup=rating_keyboard(),
    )
    return P_RATING


async def p_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["rating"] = query.data
    await query.edit_message_text("Любые комментарии и пожелания:")
    return P_COMMENTS


async def p_comments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["comments"] = update.message.text.strip()
    try:
        save_partnership_response(context.user_data)
        await update.message.reply_text(
            "Спасибо за заполнение! Обратная связь сохранена ✅\n\n"
            "Чтобы оставить ещё одну — напиши /start"
        )
    except Exception as e:
        logger.error(f"Ошибка при сохранении напарничества: {e}")
        await update.message.reply_text(
            "Спасибо! Но при сохранении возникла ошибка ❌\n"
            "Обратись к администратору бота.\n\n"
            "Чтобы начать заново — /start"
        )
    context.user_data.clear()
    return ConversationHandler.END


# =============================================================================
# ВЕТКА: СОБРАНИЯ
# =============================================================================

async def m_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    period_key = query.data
    context.user_data["period_key"] = period_key
    context.user_data["period_label"] = MEETING_PERIODS[period_key].replace("🌸 ", "").replace("☀️ ", "").replace("🍂 ", "")

    if period_key not in ACTIVE_PERIODS:
        await query.edit_message_text(
            "Эти собрания ещё не начались — ожидай! 🕐\n\n"
            "Чтобы начать заново — /start"
        )
        return ConversationHandler.END

    meetings = PERIOD_MEETINGS.get(period_key, {})
    await query.edit_message_text(
        "Выбери номер собрания:",
        reply_markup=make_keyboard(meetings, cols=3),
    )
    return M_NUMBER


async def m_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["meeting_number"] = query.data
    period_key = context.user_data["period_key"]
    context.user_data["meeting_label"] = PERIOD_MEETINGS[period_key][query.data]

    await query.edit_message_text(
        "Оцени лекцию, если она была (от 1 до 10).\n"
        "Если лекции не было — нажми «Не было»:",
        reply_markup=rating_keyboard(include_zero=True),
    )
    return M_LECTURE_RATING


async def m_lecture_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    val = query.data
    context.user_data["lecture_rating"] = "Не было" if val == "0" else val

    if val == "0":
        context.user_data["lecture_liked"] = "—"
        context.user_data["lecture_disliked"] = "—"
        await query.edit_message_text(
            "Оцени 1 интерактив (от 1 до 10):",
            reply_markup=rating_keyboard(),
        )
        return M_INT1_RATING

    await query.edit_message_text("Что понравилось на лекции?")
    return M_LECTURE_LIKED


async def m_lecture_liked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lecture_liked"] = update.message.text.strip()
    await update.message.reply_text("Что не понравилось на лекции?")
    return M_LECTURE_DISLIKED


async def m_lecture_disliked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lecture_disliked"] = update.message.text.strip()
    await update.message.reply_text(
        "Оцени 1 интерактив (от 1 до 10):",
        reply_markup=rating_keyboard(),
    )
    return M_INT1_RATING


async def m_int1_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["int1_rating"] = query.data
    await query.edit_message_text("Кто проводил 1 интерактив?")
    return M_INT1_CONDUCTOR


async def m_int1_conductor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["int1_conductor"] = update.message.text.strip()
    await update.message.reply_text("Что понравилось в 1 интерактиве?")
    return M_INT1_LIKED


async def m_int1_liked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["int1_liked"] = update.message.text.strip()
    await update.message.reply_text("Что не понравилось в 1 интерактиве?")
    return M_INT1_DISLIKED


async def m_int1_disliked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["int1_disliked"] = update.message.text.strip()
    await update.message.reply_text(
        "Оцени 2 интерактив (от 1 до 10):",
        reply_markup=rating_keyboard(),
    )
    return M_INT2_RATING


async def m_int2_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["int2_rating"] = query.data
    await query.edit_message_text("Кто проводил 2 интерактив?")
    return M_INT2_CONDUCTOR


async def m_int2_conductor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["int2_conductor"] = update.message.text.strip()
    await update.message.reply_text("Что понравилось во 2 интерактиве?")
    return M_INT2_LIKED


async def m_int2_liked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["int2_liked"] = update.message.text.strip()
    await update.message.reply_text("Что не понравилось во 2 интерактиве?")
    return M_INT2_DISLIKED


async def m_int2_disliked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["int2_disliked"] = update.message.text.strip()
    await update.message.reply_text("Любые комментарии и пожелания:")
    return M_COMMENTS


async def m_comments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["comments"] = update.message.text.strip()
    try:
        save_meeting_response(context.user_data)
        await update.message.reply_text(
            "Спасибо за заполнение! Обратная связь сохранена ✅\n\n"
            "Чтобы оставить ещё одну — напиши /start"
        )
    except Exception as e:
        logger.error(f"Ошибка при сохранении собрания: {e}")
        await update.message.reply_text(
            "Спасибо! Но при сохранении возникла ошибка ❌\n"
            "Обратись к администратору бота.\n\n"
            "Чтобы начать заново — /start"
        )
    context.user_data.clear()
    return ConversationHandler.END


# =============================================================================
# СЛУЖЕБНЫЕ ОБРАБОТЧИКИ
# =============================================================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Заполнение отменено. Напиши /start чтобы начать заново."
    )
    return ConversationHandler.END


async def unexpected_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Пожалуйста, используй кнопки для выбора.\n"
        "Если что-то пошло не так — напиши /start чтобы начать заново."
    )


async def unexpected_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Используй текущие кнопки или напиши /start")


# =============================================================================
# ЗАПУСК БОТА
# =============================================================================

def main():
    token = os.getenv("TG_TOKEN") or os.getenv("BOT_TOKEN") or os.getenv("TOKEN") or "8739787950:AAFoGJwWROjm3FNPdFSdYV21A2cJuFU5JcA"

    app = Application.builder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_TYPE: [CallbackQueryHandler(choose_type, pattern="^(partnership|meeting)$")],

            # Напарничество
            P_MEETING:          [CallbackQueryHandler(p_meeting)],
            P_YOUR_NAME:        [MessageHandler(filters.TEXT & ~filters.COMMAND, p_your_name)],
            P_PARTNER_NAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, p_partner_name)],
            P_EASE:             [CallbackQueryHandler(p_ease)],
            P_LIKED:            [MessageHandler(filters.TEXT & ~filters.COMMAND, p_liked)],
            P_DISLIKED:         [MessageHandler(filters.TEXT & ~filters.COMMAND, p_disliked)],
            P_RESPONSIBILITIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_responsibilities)],
            P_RATING:           [CallbackQueryHandler(p_rating)],
            P_COMMENTS:         [MessageHandler(filters.TEXT & ~filters.COMMAND, p_comments)],

            # Собрания
            M_PERIOD:           [CallbackQueryHandler(m_period)],
            M_NUMBER:           [CallbackQueryHandler(m_number)],
            M_LECTURE_RATING:   [CallbackQueryHandler(m_lecture_rating)],
            M_LECTURE_LIKED:    [MessageHandler(filters.TEXT & ~filters.COMMAND, m_lecture_liked)],
            M_LECTURE_DISLIKED: [MessageHandler(filters.TEXT & ~filters.COMMAND, m_lecture_disliked)],
            M_INT1_RATING:      [CallbackQueryHandler(m_int1_rating)],
            M_INT1_CONDUCTOR:   [MessageHandler(filters.TEXT & ~filters.COMMAND, m_int1_conductor)],
            M_INT1_LIKED:       [MessageHandler(filters.TEXT & ~filters.COMMAND, m_int1_liked)],
            M_INT1_DISLIKED:    [MessageHandler(filters.TEXT & ~filters.COMMAND, m_int1_disliked)],
            M_INT2_RATING:      [CallbackQueryHandler(m_int2_rating)],
            M_INT2_CONDUCTOR:   [MessageHandler(filters.TEXT & ~filters.COMMAND, m_int2_conductor)],
            M_INT2_LIKED:       [MessageHandler(filters.TEXT & ~filters.COMMAND, m_int2_liked)],
            M_INT2_DISLIKED:    [MessageHandler(filters.TEXT & ~filters.COMMAND, m_int2_disliked)],
            M_COMMENTS:         [MessageHandler(filters.TEXT & ~filters.COMMAND, m_comments)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, unexpected_text),
            CallbackQueryHandler(unexpected_callback),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv)
    logger.info("Бот запущен...")
    import asyncio
    asyncio.set_event_loop(asyncio.new_event_loop())
    app.run_polling()


if __name__ == "__main__":
    main()
