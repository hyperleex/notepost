import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.db.session import SessionLocal
import bot.db.crud as crud
from bot.core.strings import MSG_WELCOME_NEW_USER, MSG_WELCOME_EXISTING_USER, MSG_ERROR_GENERIC

logger = logging.getLogger(__name__)

async def start_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user:
        logger.warning("/start command received without effective_user")
        if update.message: # Check if message attribute exists
            await update.message.reply_text(MSG_ERROR_GENERIC)
        return

    user = update.effective_user
    db = None
    try:
        db = SessionLocal()
        admin = crud.get_admin(db, user.id)

        if not admin:
            admin = crud.create_admin(db, admin_id=user.id, first_name=user.first_name, username=user.username)
            logger.info(f"New admin registered: {user.id} ({user.username or 'no_username'})")
            welcome_message = MSG_WELCOME_NEW_USER.format(user_mention=user.mention_html())
        else:
            if admin.first_name != user.first_name or admin.username != user.username:
                admin.first_name = user.first_name
                admin.username = user.username
                db.commit()
                db.refresh(admin)
                logger.info(f"Admin details updated: {user.id}")

            if not admin.is_active:
                admin.is_active = True
                db.commit()
                logger.info(f"Admin reactivated: {user.id}")

            logger.info(f"Existing admin started: {user.id}")
            welcome_message = MSG_WELCOME_EXISTING_USER.format(user_mention=user.mention_html())

        if update.message: # Check if message attribute exists
             await update.message.reply_html(welcome_message)

    except Exception as e:
        logger.error(f"Error in /start command for user {user.id}: {e}", exc_info=True)
        if update.message: # Check if message attribute exists
            await update.message.reply_text(MSG_ERROR_GENERIC)
    finally:
        if db:
            db.close()
