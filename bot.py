import os
import sys
import re
import logging

# Ensure UTF-8 output encoding for Windows terminal unicode/emoji support
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from telegram import Update, Message
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import database as db

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER_IDS = [
    int(x.strip()) for x in os.getenv("ADMIN_USER_IDS", "").split(",") if x.strip().isdigit()
]

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize database
db.init_db()


def is_admin(user_id: int) -> bool:
    """Check if a user is an authorized admin."""
    if not ADMIN_USER_IDS:
        return True  # If no admin IDs specified in .env, allow all for easy setup
    return user_id in ADMIN_USER_IDS


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    welcome_text = (
        f"👋 **Namaste {user.first_name}!**\n\n"
        "🤖 **Telegram Lecture Auto-Forwarder & Batch Management Bot** me aapka swagat hai!\n\n"
        "Yeh Bot aapke Storage Channel (`Lectures dump`) se new lectures/videos automatically batch name ya keywords ke basis par alag-alag Batch Channels me send karega.\n\n"
        "📌 **Quick Setup Steps:**\n"
        "1. Bot ko apne **Storage Channel** aur sabhi **Batch Channels** me Admin banaye (Post Messages permission ke sath).\n"
        "2. `/setstorage <channel_id>` command se Storage Channel set karein.\n"
        "3. `/addbatch <channel_id> <Batch Name or Keyword>` se Batch register karein.\n"
        "4. Storage channel me lectures post hote hi Bot auto-detect karke forwarding chalu kar dega!\n\n"
        "💡 Helpful commands ke liye `/help` use karein."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "🛠 **Bot Setup & Command List Guide**\n\n"
        "🔹 **Admin Commands:**\n"
        "• `/setstorage <channel_id>` - Storage channel set karein.\n"
        "• `/addbatch <target_channel_id> <Batch Keyword>` - Batch mapping add karein.\n"
        "• `/removebatch <keyword_or_channel_id>` - Mapping delete karein.\n"
        "• `/listbatches` - All active batch mappings list karein.\n"
        "• `/mode <copy|forward>` - Mode change karein (`copy` = clean post, `forward` = normal forward).\n"
        "• `/stats` - Kitne lectures forward hue details dekhein.\n"
        "• `/getid` - Channel ya Group ID dekhne ke liye chat me run karein.\n\n"
        "📌 **Examples for your Batch Channels:**\n"
        "1️⃣ `/addbatch -1004368999268 GS Foundation`\n"
        "2️⃣ `/addbatch -1001234567890 Optional History`\n\n"
        "Aap kisi bhi order me `/addbatch` chala sakte hain! Sirf wahi lectures forward honge jinka batch mapped hai! 🎉"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def get_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Utility command to get Chat/Channel ID."""
    chat = update.effective_chat
    await update.message.reply_text(f"🆔 **Chat/Channel Details:**\n• Title: {chat.title or 'Private'}\n• ID: `{chat.id}`\n• Username: @{chat.username or 'N/A'}", parse_mode="Markdown")


async def set_storage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the main storage channel ID."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Aapko is command ko run karne ki permission nahi hai.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Usage: `/setstorage <channel_id_or_username>`\nExample: `/setstorage -1004477482852`", parse_mode="Markdown")
        return

    channel_input = context.args[0].strip()
    db.set_setting("storage_channel", channel_input)
    await update.message.reply_text(f"✅ **Storage Channel successfully set to:** `{channel_input}`", parse_mode="Markdown")


async def add_batch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Smart Add Batch Command.
    Supports any parameter order:
    - /addbatch -1004368999268 GS Foundation
    - /addbatch -1001234567890 Optional History
    """
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Aapko is command ko run karne ki permission nahi hai.")
        return

    raw_text = update.message.text.partition(' ')[2].strip()
    if not raw_text:
        await update.message.reply_text(
            "⚠️ Usage:\n"
            '`/addbatch <target_channel_id> <Exact Batch Keyword>`\n\n'
            "Example:\n"
            '`/addbatch -1004368999268 GS Foundation`\n'
            '`/addbatch -1001234567890 Optional History`',
            parse_mode="Markdown"
        )
        return

    tokens = raw_text.split()
    target_channel = None
    keyword_tokens = []

    # Smart detection of Channel ID (starts with -100 or @ or contains numeric ID)
    for token in tokens:
        clean_token = token.strip('"\'')
        if (clean_token.startswith("-100") or clean_token.startswith("@") or (clean_token.startswith("-") and clean_token[1:].isdigit())) and not target_channel:
            target_channel = clean_token
        else:
            keyword_tokens.append(token)

    if not target_channel or not keyword_tokens:
        await update.message.reply_text(
            "⚠️ Channel ID nahi mila! Please syntax check karein:\n"
            '`/addbatch -1004368999268 GS Foundation`',
            parse_mode="Markdown"
        )
        return

    keyword = " ".join(keyword_tokens).strip('"\'')
    batch_name = keyword

    # Store clean mapping
    if db.add_batch_mapping(keyword, target_channel, batch_name):
        await update.message.reply_text(
            f"✅ **Batch Mapping Added Successfully!**\n\n"
            f"🏷 **Exact Keyword:** `{keyword}`\n"
            f"📢 **Target Channel ID:** `{target_channel}`\n\n"
            f"🎯 Storage channel me keval wahi lectures copy honge jisme `{keyword}` word maujood hoga. Kisi aur batch ka lecture forward nahi hoga!",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Failed to add batch mapping.")


async def remove_batch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a batch mapping."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Admin permission required.")
        return

    raw_text = update.message.text.partition(' ')[2].strip().strip('"\'')
    if not raw_text:
        await update.message.reply_text("⚠️ Usage: `/removebatch <keyword_or_channel_id>`", parse_mode="Markdown")
        return

    if db.remove_batch_mapping(raw_text):
        await update.message.reply_text(f"🗑 Mapping for `{raw_text}` successfully removed!", parse_mode="Markdown")
    else:
        mappings = db.get_all_batch_mappings()
        removed_any = False
        for m in mappings:
            if m["target_channel"] == raw_text or m["tag"].lower() == raw_text.lower():
                db.remove_batch_mapping(m["tag"])
                removed_any = True

        if removed_any:
            await update.message.reply_text(f"🗑 Mappings for `{raw_text}` successfully removed!", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Mapping `{raw_text}` nahi mila.", parse_mode="Markdown")


async def list_batches_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all configured batch channels."""
    mappings = db.get_all_batch_mappings()
    storage_channel = db.get_setting("storage_channel", "Not Set")

    if not mappings:
        text = (
            f"📦 **Storage Channel:** `{storage_channel}`\n\n"
            f"⚠️ Abhi koi Batch Channel mapping add nahi ki gayi hai.\n"
            f"Add karne ke liye use karein:\n"
            '`/addbatch <channel_id> <Batch Keyword>`'
        )
        await update.message.reply_text(text, parse_mode="Markdown")
        return

    text = f"📦 **Storage Channel:** `{storage_channel}`\n\n📋 **Active Batch Channel Mappings ({len(mappings)}):**\n\n"
    for m in mappings:
        text += f"🔹 **Exact Keyword:** `{m['tag']}`\n  ├ **Batch Label:** {m['batch_name']}\n  └ **Target Channel:** `{m['target_channel']}`\n\n"

    await update.message.reply_text(text, parse_mode="Markdown")


async def set_mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle between 'copy' (clean post) and 'forward' (with forwarded tag)."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Admin permission required.")
        return

    if not context.args or context.args[0].lower() not in ["copy", "forward"]:
        await update.message.reply_text("⚠️ Usage: `/mode copy` ya `/mode forward`", parse_mode="Markdown")
        return

    mode = context.args[0].lower()
    db.set_setting("forward_mode", mode)
    await update.message.reply_text(f"🔄 **Forward Mode set to:** `{mode.upper()}`", parse_mode="Markdown")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display forwarding statistics."""
    stats = db.get_stats()
    text = f"📊 **Forwarding Statistics**\n\n"
    text += f"🚀 **Total Lectures Forwarded:** `{stats['total']}`\n\n"
    if stats['by_tag']:
        text += "🏷 **Breakdown by Keyword:**\n"
        for tag, count in stats['by_tag'].items():
            text += f"• `{tag}`: {count} posts\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def process_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Strict handler for Channel Posts in Storage Channel.
    Matches post text ONLY against explicitly set batch keywords.
    If no configured keyword matches, the post is COMPLETELY IGNORED.
    """
    post: Message = update.channel_post or update.message
    if not post:
        return

    storage_channel = db.get_setting("storage_channel", None)
    current_chat_id = str(post.chat.id)
    current_chat_username = f"@{post.chat.username}" if post.chat.username else None

    # Check if this post is from the configured Storage Channel
    if storage_channel:
        if current_chat_id != storage_channel and current_chat_username != storage_channel:
            logger.info(f"Post from channel {current_chat_id} ignored (Storage Channel is configured as {storage_channel}).")
            return

    # Extract caption or text from post
    text = post.text or post.caption or ""
    if not text:
        logger.info(f"Channel post ID {post.message_id} has no text or caption to analyze.")
        return

    logger.info(f"RECEIVED POST ID {post.message_id} in Storage Channel ({current_chat_id}). Caption:\n{text[:100]}...")

    text_lower = text.lower()
    all_mappings = db.get_all_batch_mappings()
    forward_mode = db.get_setting("forward_mode", "copy")

    matched_targets = set()

    # STRICT MATCHING: Only match if the exact configured keyword is present in text
    for mapping in all_mappings:
        keyword = mapping["tag"].lower()
        if keyword in text_lower:
            matched_targets.add((mapping["target_channel"], mapping["tag"], mapping["batch_name"]))

    if not matched_targets:
        logger.info(f"Post ID {post.message_id} does NOT match any active mapped channels. IGNORING POST.")
        return

    for target_channel, tag, batch_name in matched_targets:
        try:
            if forward_mode == "copy":
                # Copy message creates a fresh post without 'Forwarded from' header
                await post.copy(chat_id=target_channel)
                logger.info(f"Successfully COPIED message {post.message_id} to batch '{batch_name}' ({target_channel}).")
            else:
                # Forward message keeps original sender metadata
                await post.forward(chat_id=target_channel)
                logger.info(f"Successfully FORWARDED message {post.message_id} to batch '{batch_name}' ({target_channel}).")

            # Log to DB
            db.log_forwarding(post.message_id, tag, target_channel)

        except Exception as e:
            logger.error(f"Failed to send post {post.message_id} to {target_channel}: {e}")


from telegram.request import HTTPXRequest

def main():
    """Start the bot application."""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("❌ ERROR: BOT_TOKEN is missing in .env file!")
        return

    print("🚀 Starting Telegram Batch Forwarder Bot...")
    request_config = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0, write_timeout=30.0)
    app = ApplicationBuilder().token(BOT_TOKEN).request(request_config).build()

    # Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("getid", get_id_command))
    app.add_handler(CommandHandler("setstorage", set_storage_command))
    app.add_handler(CommandHandler("addbatch", add_batch_command))
    app.add_handler(CommandHandler("removebatch", remove_batch_command))
    app.add_handler(CommandHandler("listbatches", list_batches_command))
    app.add_handler(CommandHandler("mode", set_mode_command))
    app.add_handler(CommandHandler("stats", stats_command))

    # Channel Post Listener (triggers when a post or edited post arrives in channels)
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL & (filters.ALL), process_channel_post))
    
    # Also allow triggering in private chats or groups for testing
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, process_channel_post))

    print("✅ Bot is online and listening for channel posts!")
    app.run_polling(drop_pending_updates=True)



if __name__ == "__main__":
    main()
