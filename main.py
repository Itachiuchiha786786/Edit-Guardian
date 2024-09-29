import html
import logging
from telegram import Update, Bot, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from config import TELEGRAM_TOKEN, OWNER_ID

# Set up logging for bot activity
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
trusted_users = set()
edited_message_log = {}

# Start Command
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    mention = f"<a href='tg://user?id={user.id}'>{html.escape(user.first_name)}</a>"
    
    # Send welcome message
    update.message.reply_html(f'Hello! {mention}! I am Edit Guardian bot. I delete edited messages except for trusted users and my creator.')
    update.message.reply_html("To become a trusted user, request approval from the bot owner.")
    
    # Send an video (start video) to the user
    video_path = "https://files.catbox.moe/xbj93j.mp4"  # Replace with the actual path to your image
    with open(video_path, 'rb') as video:
        context.bot.send_video(chat_id=update.message.chat_id, video=video, caption="Welcome to the Edit Guardian bot!")

# Trusted User Commands (Owner only)
def add_trusted(update: Update, context: CallbackContext):
    user = update.effective_user
    
    if user.id != OWNER_ID:
        update.message.reply_text("Only the bot owner can use this command.")
        return

    try:
        target_id = int(context.args[0])
        trusted_users.add(target_id)
        update.message.reply_text(f"User with ID {target_id} has been added to the trusted list.")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /addtrusted <user_id>")

def remove_trusted(update: Update, context: CallbackContext):
    user = update.effective_user
    
    if user.id != OWNER_ID:
        update.message.reply_text("Only the bot owner can use this command.")
        return

    try:
        target_id = int(context.args[0])
        if target_id in trusted_users:
            trusted_users.remove(target_id)
            update.message.reply_text(f"User with ID {target_id} has been removed from the trusted list.")
        else:
            update.message.reply_text("This user is not in the trusted list.")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /removetrusted <user_id>")

# Function to log edited messages
def log_edit(update: Update, edited_message):
    chat_id = update.effective_chat.id
    message_id = edited_message.message_id
    user_id = edited_message.from_user.id

    if chat_id not in edited_message_log:
        edited_message_log[chat_id] = {}

    # Log original and edited message
    edited_message_log[chat_id][message_id] = {
        "user_id": user_id,
        "original_text": edited_message.text or '',
        "edited_text": edited_message.text or ''
    }
    
    logger.info(f"Logged edited message from {user_id} in chat {chat_id}")

# Function to check for edits and send video
def check_edit(update: Update, context: CallbackContext):
    bot: Bot = context.bot

    # Check if the update is an edited message
    if update.edited_message:
        edited_message = update.edited_message
        
        # Get chat ID, message ID, and user who edited the message
        chat_id = edited_message.chat_id
        message_id = edited_message.message_id
        user_id = edited_message.from_user.id

        # Create the mention for the user
        user_mention = f"<a href='tg://user?id={user_id}'>{html.escape(edited_message.from_user.first_name)}</a>"
        
        # Log the edit
        log_edit(update, edited_message)
        
        # Delete the message if the user is not the owner or trusted
        if user_id != OWNER_ID and user_id not in trusted_users:
            bot.delete_message(chat_id=chat_id, message_id=message_id)
            
            # Notify the group
            bot.send_message(chat_id=chat_id, text=f"{user_mention} just edited a message. It was deleted.", parse_mode='HTML')

            # Notify the owner with details
            bot.send_message(chat_id=OWNER_ID, text=f"User {user_mention} edited a message in chat {chat_id}. Original message was: '{edited_message.text}'. It was deleted.", parse_mode='HTML')

            # Send a video when a user edits a message
            video_path = "https://files.catbox.moe/s5dndg.mp4"  # Replace with the actual path to your video
            with open(video_path, 'rb') as video:
                bot.send_video(chat_id=chat_id, video=video, caption=f"{user_mention}, please refrain from editing your messages.")

# Main function to start the bot
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Start command handler
    dp.add_handler(CommandHandler("start", start))
    
    # Add/Remove trusted user commands (owner only)
    dp.add_handler(CommandHandler("addtrusted", add_trusted))
    dp.add_handler(CommandHandler("removetrusted", remove_trusted))

    # Message edit handler
    dp.add_handler(MessageHandler(Filters.update.edited_message, check_edit))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
