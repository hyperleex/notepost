import logging
import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    PicklePersistence,
    MessageHandler,
    filters
)

from bot.core.config import TELEGRAM_BOT_TOKEN, LOG_LEVEL
from bot.core.strings import MSG_COMMAND_UNKNOWN
# from bot.db.session import engine, SessionLocal, create_db_and_tables # For DB init if needed here
# from bot.db.crud import get_admin, create_admin # For admin check decorator or start command

# Actual handler imports
from bot.handlers.admin import start_command_handler
# from bot.handlers.post_creation import post_creation_conversation_handler # Example for future

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=LOG_LEVEL
)
logger = logging.getLogger(__name__)

# placeholder_start function has been removed as start_command_handler is now used.

async def unknown_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"Unknown command: {update.message.text} from {update.effective_user.id if update.effective_user else 'unknown'}")
    await update.message.reply_text(MSG_COMMAND_UNKNOWN)


def create_application() -> Application:
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN is not set. Bot cannot start.")
        raise ValueError("TELEGRAM_BOT_TOKEN is not set.")

    persistence = PicklePersistence(filepath="./telegram_poster_bot_persistence.pickle")

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .persistence(persistence)
        .build()
    )

    # Register actual handlers
    application.add_handler(CommandHandler("start", start_command_handler)) # Use the real handler

    # Actual handlers will be added here later, e.g.
    # application.add_handler(post_creation_conversation_handler)

    # Handler for unknown commands - must be added after all other CommandHandlers
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command_handler))

    # TODO: Setup JobQueue for scheduled tasks
    # job_queue = application.job_queue
    # job_queue.run_repeating(some_task_callback, interval=60, first=10) # Example: run every 60s

    return application

def main() -> None:
    try:
        # Optional: DB Initialization (Alembic is preferred for schema management)
        # from bot.db.session import create_db_and_tables as init_db
        # logger.info("Initializing database and tables if necessary...")
        # init_db()
        # logger.info("Database initialization check complete.")

        application = create_application()
        logger.info("Bot application created. Starting polling...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except ValueError as ve:
        logger.critical(f"Bot startup failed due to ValueError: {ve}")
    except Exception as e:
        logger.critical(f"Bot startup failed due to an unexpected error: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting bot directly from main.py")
    main()
