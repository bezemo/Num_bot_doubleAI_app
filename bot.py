# bot.py  (добавлен выбор ИИ + вызов двух моделей)
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
from telegram.error import BadRequest, TimedOut, Forbidden, TelegramError
from config import settings
from db import init_db, get_cached_report, save_report
from numerology import calculate
from utils import detect_mode_and_date
from yandex_gpt import generate_via_yandex, generate_fallback_via_yandex
from deepseek_client import generate_via_deepseek
from build_report import build_report_structure
from date_parser import find_dates
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------- вспомогательные ----------
async def _safe_answer(query) -> bool:
    try:
        await query.answer()
        return True
    except (BadRequest, TimedOut) as e:
        logger.warning("Просрочен/невалидный query: %s", e)
        return False


async def _reply(update: Update, text: str) -> None:
    if update.message:
        await update.message.reply_text(text)
    else:
        await update.callback_query.message.reply_text(text)


async def send_long_message(update: Update, text: str) -> None:
    for chunk in (text[i : i + 4000] for i in range(0, len(text), 4000)):
        await _reply(update, chunk)


# ---------- генерация текста ----------
async def generate_text(
    structure: List[str], mode: str, ai: str
) -> str:
    if ai == "deepseek":
        return generate_via_deepseek(structure, mode)
    # по умолчанию – YandexGPT
    return generate_via_yandex(structure, mode)


# ---------- логика расчёта ----------
async def _proceed_with_date(
    update: Update, context: ContextTypes.DEFAULT_TYPE, date_str: str, mode: str
) -> None:
    user_id = update.effective_user.id
    context.user_data["last_valid_date"] = date_str
    context.user_data["hint_given"] = False

    ai = context.user_data.get("ai", "yandex")
    cache_key = f"{user_id}|{date_str}|{mode}|{ai}"

    cached = get_cached_report(user_id, date_str, mode)
    if cached:
        await _reply(update, cached)
        return

    try:
        data = calculate(date_str)
        structure = build_report_structure(data, mode)
        final_text = await generate_text(structure, mode, ai)
        save_report(user_id, date_str, mode, final_text)
        await send_long_message(update, final_text)
    except Exception:
        logger.exception("Ошибка генерации")
        await _reply(update, "Произошла ошибка. Попробуй позже.")


# ---------- команды ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(
        update,
        "Введи свою дату рождения — и я создам твой личный эзотерический портрет.",
    )


async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("🔮 Базовый (default)", callback_data="default")],
        [InlineKeyboardButton("🌙 Глубокий (deep)", callback_data="deep")],
        [InlineKeyboardButton("🌈 Мастер (master)", callback_data="master")],
    ]
    await update.message.reply_text(
        "Выбери режим расчёта:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def ai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("☁️ YandexGPT", callback_data="ai_yandex")],
        [InlineKeyboardButton("🦔 DeepSeek (локально)", callback_data="ai_deepseek")],
    ]
    await update.message.reply_text(
        "Выбери модель ИИ:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def set_ai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await _safe_answer(query)
    chosen = query.data.split("_")[1]  # ai_yandex / ai_deepseek
    context.user_data["ai"] = chosen
    await query.message.reply_text(f"✅ Модель ИИ установлена: {chosen}")


async def date_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await _safe_answer(query)
    _, date_str = query.data.split("|", 1)
    mode = context.user_data.get("mode", "master")
    await query.message.reply_text(f"Берём дату: {date_str}")
    await _proceed_with_date(update, context, date_str, mode)


# ---------- основной обработчик ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    user_id = update.effective_user.id

    if text.lower() == "сделай расчёт по дате":
        last_date = context.user_data.get("last_valid_date")
        if not last_date:
            await _reply(update, "Сначала введи дату рождения.")
            return
        mode = context.user_data.get("mode", "master")
        await _proceed_with_date(update, context, last_date, mode)
        return

    candidates = find_dates(text)
    if not candidates:
        if context.user_data.get("hint_given"):
            resp = generate_fallback_via_yandex(text)
            await _reply(update, resp)
            return
        context.user_data["hint_given"] = True
        resp = generate_fallback_via_yandex(text)
        await _reply(update, resp)
        return

    if len(candidates) == 1:
        mode = context.user_data.get("mode", "master")
        await _proceed_with_date(update, context, candidates[0], mode)
        return

    keyboard = [
        [InlineKeyboardButton(dt, callback_data=f"date_choice|{dt}")]
        for dt in candidates
    ]
    await update.message.reply_text(
        "Нашёл несколько дат – выбери нужную:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text.strip() if update.message else ""
    response = generate_fallback_via_yandex(user_text)
    await _reply(update, response)


# ---------- обработчик ошибок ----------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        raise context.error
    except Forbidden:
        logger.warning(
            "Пользователь заблокировал бота: %s",
            update.effective_user.id if update else "?",
        )
    except TelegramError as e:
        logger.exception("Telegram-ошибка: %s", e)


# ---------- запуск ----------
def main() -> None:
    init_db()
    app = Application.builder().token(settings.telegram_token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mode", mode))
    app.add_handler(CommandHandler("ai", ai))
    app.add_handler(CallbackQueryHandler(set_ai, pattern="^ai_"))
    app.add_handler(CallbackQueryHandler(set_mode, pattern="^(default|deep|master)$"))
    app.add_handler(CallbackQueryHandler(date_selected, pattern="^date_choice\\|"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.ALL, fallback))
    app.add_error_handler(error_handler)

    logger.info("Бот запущен.")
    app.run_polling()


if __name__ == "__main__":
    main()