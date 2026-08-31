import logging
import os
import sys

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from intent_classifier import classify_intent
from responses import get_static_response, _format_foto
from admin import build_admin_conversation_handler

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    logger.error(
        "TELEGRAM_BOT_TOKEN belum diset. Jalankan dengan:\n"
        "  export TELEGRAM_BOT_TOKEN='token-dari-BotFather'\n"
        "  python bot.py\n"
        "atau taruh di file .env dan load dengan python-dotenv."
    )
    sys.exit(1)

VALID_LANGS = {"id", "en"}
DEFAULT_LANG = "id"

_START_CAPTION = {
    "id": (
        "Om Swastyastu, Selamat Datang di Goa Raja. "
        "Silakan tanya tanya seputar tempat wisata."
    ),
    "en": (
        "Om Swastyastu, welcome to Goa Raja. "
        "Feel free to ask anything about this tourist spot."
    ),
}

_LANGUAGE_USAGE = {
    "id": (
        "Gunakan /language id atau /language en untuk memilih bahasa.\n"
        f"Bahasa saat ini: {{current}}"
    ),
    "en": (
        "Use /language id or /language en to choose a language.\n"
        f"Current language: {{current}}"
    ),
}

_LANGUAGE_CONFIRM = {
    "id": "Baik, saya akan menjawab dalam Bahasa Indonesia mulai sekarang.",
    "en": "Alright, I'll reply in English from now on.",
}

_LANGUAGE_PROMPT = "Pilih bahasa / Choose your language:"

_LANGUAGE_KEYBOARD = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("🇮🇩 Bahasa Indonesia", callback_data="setlang:id"),
            InlineKeyboardButton("🇬🇧 English", callback_data="setlang:en"),
        ]
    ]
)


def _get_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("lang", DEFAULT_LANG)


def _has_chosen_lang(context: ContextTypes.DEFAULT_TYPE) -> bool:
    """True kalau user sudah pernah memilih/set bahasa sebelumnya (lewat tombol atau /language)."""
    return "lang" in context.user_data


async def _send_greeting(bot, chat_id: int, lang: str) -> None:
    """Kirim foto+sapaan sesuai bahasa. Dipakai oleh start() (user lama) dan
    language_button_callback() (user baru setelah memilih lewat tombol)."""
    caption_text = _START_CAPTION[lang]
    foto_path = _format_foto()

    if foto_path is None:
        await bot.send_message(chat_id=chat_id, text=caption_text)
        return

    try:
        with open(foto_path, "rb") as photo_file:
            await bot.send_photo(chat_id=chat_id, photo=photo_file, caption=caption_text)
    except FileNotFoundError:
        logger.warning(
            f"Foto sapaan tidak ditemukan di '{foto_path}'. "
            "Mengirim teks saja tanpa foto."
        )
        await bot.send_message(chat_id=chat_id, text=caption_text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # User baru (belum pernah pilih bahasa) -> tampilkan tombol pilihan dulu,
    # foto+sapaan dikirim setelah user tap salah satu tombol (lihat language_button_callback).
    if not _has_chosen_lang(context):
        await update.message.reply_text(_LANGUAGE_PROMPT, reply_markup=_LANGUAGE_KEYBOARD)
        return

    lang = _get_lang(context)
    await _send_greeting(context.bot, update.effective_chat.id, lang)


async def language_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk tap tombol pilih bahasa di /start. callback_data: 'setlang:id' / 'setlang:en'."""
    query = update.callback_query
    await query.answer()  # wajib, biar loading spinner di tombol Telegram hilang

    requested = query.data.split(":", 1)[1]
    if requested not in VALID_LANGS:
        requested = DEFAULT_LANG

    context.user_data["lang"] = requested
    logger.info(f"User {update.effective_user.id} memilih bahasa '{requested}' via tombol /start.")

    # Ganti pesan tombol jadi teks konfirmasi singkat (tombolnya hilang).
    await query.edit_message_text(_LANGUAGE_CONFIRM[requested])

    await _send_greeting(context.bot, update.effective_chat.id, requested)


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /language. Tanpa argumen -> tampilkan bahasa saat ini & cara pakai."""
    current_lang = _get_lang(context)
    args = context.args

    if not args:
        usage_lang = current_lang if current_lang in VALID_LANGS else DEFAULT_LANG
        await update.message.reply_text(
            _LANGUAGE_USAGE[usage_lang].format(current=current_lang)
        )
        return

    requested = args[0].strip().lower()
    if requested not in VALID_LANGS:
        usage_lang = current_lang if current_lang in VALID_LANGS else DEFAULT_LANG
        await update.message.reply_text(
            _LANGUAGE_USAGE[usage_lang].format(current=current_lang)
        )
        return

    context.user_data["lang"] = requested
    logger.info(f"User {update.effective_user.id} mengubah bahasa ke '{requested}'.")
    await update.message.reply_text(_LANGUAGE_CONFIRM[requested])


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_question = update.message.text
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    lang = _get_lang(context)

    logger.info(f"User {user_id} bertanya ({lang}): {user_question}")

    intent = classify_intent(user_question)
    response_text, photo_path = get_static_response(intent, lang)

    last_message_id = context.user_data.get("last_bot_message_id")
    if last_message_id is not None:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=last_message_id)
        except Exception as e:
            logger.warning(
                f"Gagal menghapus pesan lama (message_id={last_message_id}) "
                f"untuk user {user_id}: {e}"
            )

    sent_message = None
    if photo_path is not None:
        try:
            with open(photo_path, "rb") as photo_file:
                sent_message = await update.message.reply_photo(
                    photo=photo_file, caption=response_text
                )
        except FileNotFoundError:
            logger.warning(
                f"File '{photo_path}' tidak ditemukan saat mengirim, "
                "mengirim teks saja tanpa foto."
            )

    if sent_message is None:
        sent_message = await update.message.reply_text(response_text)

    context.user_data["last_bot_message_id"] = sent_message.message_id


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("language", set_language))
    app.add_handler(CallbackQueryHandler(language_button_callback, pattern=r"^setlang:"))
    app.add_handler(build_admin_conversation_handler())
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot mulai polling...")
    app.run_polling(poll_interval=1.0) 


if __name__ == "__main__":
    main()
