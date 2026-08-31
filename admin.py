import json
import logging
import re
import shutil
import time
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

import responses

logger = logging.getLogger(__name__)

DATA_PATH = responses.DATA_PATH
BACKUP_DIR = DATA_PATH.parent / "backups"

# States untuk ConversationHandler
CHOOSING_CATEGORY, CHOOSING_FIELD, TYPING_VALUE, CONFIRM_LIST_ACTION, TYPING_LIST_VALUE = range(5)

FIELD_SCHEMA = {
    "info_umum": {
        "label": "Info Umum",
        "fields": {
            "nama": {"label": "Nama Tempat", "path": ["info_umum", "nama"], "type": "text"},
            "deskripsi": {"label": "Deskripsi", "path": ["info_umum", "deskripsi"], "type": "list"},
        },
    },
    "lokasi": {
        "label": "Lokasi",
        "fields": {
            "alamat": {"label": "Alamat", "path": ["lokasi", "alamat"], "type": "text"},
            "maps": {"label": "Link Google Maps", "path": ["lokasi", "maps"], "type": "url"},
        },
    },
    "tarif": {
        "label": "Tarif",
        "fields": {
            "dewasa": {"label": "Harga Dewasa (Rp)", "path": ["tarif", "dewasa"], "type": "int"},
            "anak": {"label": "Harga Anak (Rp)", "path": ["tarif", "anak"], "type": "int"},
            "catatan": {"label": "Catatan Harga", "path": ["tarif", "catatan"], "type": "text"},
        },
    },
    "jam_operasional": {
        "label": "Jam Operasional",
        "fields": {
            "senin_jumat": {
                "label": "Senin-Jumat",
                "path": ["jam_operasional", "senin_jumat"],
                "type": "text",
            },
            "sabtu_minggu": {
                "label": "Sabtu-Minggu",
                "path": ["jam_operasional", "sabtu_minggu"],
                "type": "text",
            },
        },
    },
    "fasilitas": {
        "label": "Fasilitas",
        "fields": {
            "fasilitas": {"label": "Daftar Fasilitas", "path": ["fasilitas"], "type": "list"},
        },
    },
    "kontak": {
        "label": "Kontak",
        "fields": {
            "nama_kontak": {"label": "Nama Kontak", "path": ["kontak", "nama"], "type": "text"},
            "telepon": {"label": "Telepon/WA", "path": ["kontak", "telepon"], "type": "phone"},
            "instagram": {"label": "Instagram", "path": ["kontak", "Instagram"], "type": "url"},
        },
    },
}

_URL_RE = re.compile(r"^https?://\S+$")
_PHONE_RE = re.compile(r"^[0-9+\-\s]+$")


def _is_admin(user_id: int) -> bool:
    whitelist = responses.get_data().get("admin_whitelist", [])
    return user_id in whitelist


def _backup_data() -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = BACKUP_DIR / f"data.json.bak.{timestamp}"
    shutil.copy2(DATA_PATH, backup_path)
    return backup_path


def _get_nested(data: dict, path: list):
    node = data
    for key in path:
        node = node[key]
    return node


def _set_nested(data: dict, path: list, value) -> None:
    node = data
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value


def _save_data(data: dict) -> None:
    _backup_data()
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    responses.reload_data()


def _find_field_def(category_key: str, field_key: str) -> dict | None:
    category = FIELD_SCHEMA.get(category_key)
    if not category:
        return None
    return category["fields"].get(field_key)


def _validate_and_cast(field_type: str, raw_text: str):
    raw_text = raw_text.strip()

    if not raw_text:
        return False, "Value cannot be empty. try again, or /batal for cancellation."

    if field_type == "text":
        return True, raw_text

    if field_type == "int":
        cleaned = re.sub(r"[^\d]", "", raw_text)
        if not cleaned:
            return False, "make sure input is numeric"
        return True, int(cleaned)

    if field_type == "url":
        if not _URL_RE.match(raw_text):
            return False, "make sure notation of link"
        return True, raw_text

    if field_type == "phone":
        if not _PHONE_RE.match(raw_text):
            return False, "make sure phone number format"
        return True, raw_text

    return True, raw_text


async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    if not _is_admin(user_id):
        logger.warning(f"User {user_id} trying access /admin but not on whitelist.")
        await update.message.reply_text(
            "sorry, you are not admin."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "*Admin Panel — Goa Raja Bot*\n\nchoose item for changes:",
        parse_mode="Markdown",
        reply_markup=_category_keyboard(),
    )
    return CHOOSING_CATEGORY


def _category_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(cat["label"], callback_data=f"cat:{key}")]
        for key, cat in FIELD_SCHEMA.items()
    ]
    buttons.append([InlineKeyboardButton("Tutup", callback_data="close")])
    return InlineKeyboardMarkup(buttons)


def _field_keyboard(category_key: str) -> InlineKeyboardMarkup:
    category = FIELD_SCHEMA[category_key]
    buttons = [
        [InlineKeyboardButton(f["label"], callback_data=f"field:{category_key}:{fkey}")]
        for fkey, f in category["fields"].items()
    ]
    buttons.append([InlineKeyboardButton("back", callback_data="back_to_category")])
    return InlineKeyboardMarkup(buttons)


def _list_action_keyboard(category_key: str, field_key: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("add item", callback_data=f"listadd:{category_key}:{field_key}")],
        [InlineKeyboardButton("delete item", callback_data=f"listdel:{category_key}:{field_key}")],
        [InlineKeyboardButton("reveal all", callback_data=f"listview:{category_key}:{field_key}")],
        [InlineKeyboardButton("back", callback_data="back_to_category")],
    ]
    return InlineKeyboardMarkup(buttons)


async def handle_category_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "close":
        await query.edit_message_text("Admin panel closed.")
        return ConversationHandler.END

    category_key = query.data.split(":", 1)[1]
    context.user_data["admin_category"] = category_key
    category = FIELD_SCHEMA[category_key]

    await query.edit_message_text(
        f"{category['label']}\n\nchoose category for changes:",
        reply_markup=_field_keyboard(category_key),
    )
    return CHOOSING_FIELD


async def handle_back_to_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "*Admin Panel — Goa Raja Bot*\n\nchoose category for changes:",
        parse_mode="Markdown",
        reply_markup=_category_keyboard(),
    )
    return CHOOSING_CATEGORY


async def handle_field_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    _, category_key, field_key = query.data.split(":", 2)
    field_def = _find_field_def(category_key, field_key)

    if field_def is None:
        await query.edit_message_text("field not found. send /admin to try again.")
        return ConversationHandler.END

    context.user_data["admin_category"] = category_key
    context.user_data["admin_field"] = field_key

    if field_def["type"] == "list":
        current = _get_nested(responses.get_data(), field_def["path"])
        preview = "\n".join(f"  {i+1}. {item}" for i, item in enumerate(current)) or "  (empty)"
        await query.edit_message_text(
            f"*{field_def['label']}* — currently:\n{preview}\n\nchoose action:",
            parse_mode="Markdown",
            reply_markup=_list_action_keyboard(category_key, field_key),
        )
        return CONFIRM_LIST_ACTION

    current = _get_nested(responses.get_data(), field_def["path"])
    await query.edit_message_text(
        f"*{field_def['label']}*\ncurrent value: `{current}`\n\n"
        f"type new value, or /batal to cancel.",
        parse_mode="Markdown",
    )
    return TYPING_VALUE


async def handle_value_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    category_key = context.user_data.get("admin_category")
    field_key = context.user_data.get("admin_field")
    field_def = _find_field_def(category_key, field_key)

    if field_def is None:
        await update.message.reply_text("admin session failed, try again with /admin or make sure this user is admin.")
        return ConversationHandler.END

    ok, result = _validate_and_cast(field_def["type"], update.message.text)
    if not ok:
        await update.message.reply_text(f"{result}")
        return TYPING_VALUE  

    data = responses.get_data()
    data_copy = json.loads(json.dumps(data))
    _set_nested(data_copy, field_def["path"], result)

    try:
        _save_data(data_copy)
    except Exception as e:
        logger.error(f"failed to save data.json: {e}")
        await update.message.reply_text(
            "failed to save changes."
        )
        return ConversationHandler.END

    logger.info(
        f"Admin {update.effective_user.id} change {category_key}.{field_key} -> {result!r}"
    )
    await update.message.reply_text(
        f"*{field_def['label']}* successfully changes to:\n`{result}`\n\n"
        f"changes active, no need to restart bot.\n"
        f"send /admin for other fields change.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def handle_list_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    action, category_key, field_key = query.data.split(":", 2)
    field_def = _find_field_def(category_key, field_key)
    context.user_data["admin_category"] = category_key
    context.user_data["admin_field"] = field_key

    if action == "listview":
        current = _get_nested(responses.get_data(), field_def["path"])
        preview = "\n".join(f"  {i+1}. {item}" for i, item in enumerate(current)) or "  (kosong)"
        await query.edit_message_text(
            f"*{field_def['label']}*:\n{preview}\n\ntype /admin for back to menu.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    if action == "listadd":
        await query.edit_message_text(
            f"type teks to be added to *{field_def['label']}*, "
            f"or /batal for cancellation.",
            parse_mode="Markdown",
        )
        context.user_data["admin_list_action"] = "add"
        return TYPING_LIST_VALUE

    if action == "listdel":
        current = _get_nested(responses.get_data(), field_def["path"])
        if not current:
            await query.edit_message_text(
                f"*{field_def['label']}* empty, or cannot be deleted.\n"
                f"type /admin for back to menu.",
                parse_mode="Markdown",
            )
            return ConversationHandler.END
        preview = "\n".join(f"  {i+1}. {item}" for i, item in enumerate(current))
        await query.edit_message_text(
            f"*{field_def['label']}* — send item number for deletion:\n{preview}\n\n"
            f"or /batal for cancelation.",
            parse_mode="Markdown",
        )
        context.user_data["admin_list_action"] = "delete"
        return TYPING_LIST_VALUE

    await query.edit_message_text("unknown action. send /admin.")
    return ConversationHandler.END


async def handle_list_value_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    category_key = context.user_data.get("admin_category")
    field_key = context.user_data.get("admin_field")
    list_action = context.user_data.get("admin_list_action")
    field_def = _find_field_def(category_key, field_key)

    if field_def is None or list_action is None:
        await update.message.reply_text("admin session failed, try again with /admin or make sure this user is admin.")
        return ConversationHandler.END

    data = responses.get_data()
    data_copy = json.loads(json.dumps(data))
    current_list = _get_nested(data_copy, field_def["path"])

    if list_action == "add":
        new_item = update.message.text.strip()
        if not new_item:
            await update.message.reply_text("item cannot be empty. try again, or /batal.")
            return TYPING_LIST_VALUE
        current_list.append(new_item)
        result_msg = f"Item added: \"{new_item}\""

    elif list_action == "delete":
        raw = update.message.text.strip()
        if not raw.isdigit() or not (1 <= int(raw) <= len(current_list)):
            await update.message.reply_text(
                f"send number between 1 or {len(current_list)}, /batal."
            )
            return TYPING_LIST_VALUE
        removed = current_list.pop(int(raw) - 1)
        result_msg = f"Item deleted: \"{removed}\""

    else:
        await update.message.reply_text("Unknown Action")
        return ConversationHandler.END

    try:
        _save_data(data_copy)
    except Exception as e:
        logger.error(f"failed save data.json: {e}")
        await update.message.reply_text(
            "Error Saving changes"
        )
        return ConversationHandler.END

    logger.info(
        f"Admin {update.effective_user.id} update list {category_key}.{field_key}: {list_action}"
    )
    await update.message.reply_text(
        f"{result_msg}\n\nchanges active, call administrator for other fields changes."
    )
    return ConversationHandler.END


async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("admin_category", None)
    context.user_data.pop("admin_field", None)
    context.user_data.pop("admin_list_action", None)
    await update.message.reply_text("Canceled. changes not saved.")
    return ConversationHandler.END


def build_admin_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("admin", admin_start)],
        states={
            CHOOSING_CATEGORY: [
                CallbackQueryHandler(handle_category_choice, pattern=r"^(cat:|close)"),
            ],
            CHOOSING_FIELD: [
                CallbackQueryHandler(handle_field_choice, pattern=r"^field:"),
                CallbackQueryHandler(handle_back_to_category, pattern=r"^back_to_category$"),
            ],
            TYPING_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_value_input),
            ],
            CONFIRM_LIST_ACTION: [
                CallbackQueryHandler(handle_list_action, pattern=r"^(listadd|listdel|listview):"),
                CallbackQueryHandler(handle_back_to_category, pattern=r"^back_to_category$"),
            ],
            TYPING_LIST_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_list_value_input),
            ],
        },
        fallbacks=[CommandHandler("batal", admin_cancel)],
    )