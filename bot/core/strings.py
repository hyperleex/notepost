# User-facing strings in Russian

# Welcome and General
MSG_WELCOME_NEW_USER = "Добро пожаловать, {user_mention}! Я ваш помощник для публикации постов. Используйте /help для списка команд."
MSG_WELCOME_EXISTING_USER = "Снова здравствуйте, {user_mention}! Используйте /help для списка команд."
MSG_HELP = (
    "Доступные команды:\n"
    "/start - Начало работы\n"
    "/newpost - Создать новый пост\n"
    "/channels - Управление каналами\n"
    # ... Add other commands as they are implemented
)
MSG_ERROR_GENERIC = "Произошла ошибка. Пожалуйста, попробуйте позже."
MSG_COMMAND_UNKNOWN = "Неизвестная команда. Используйте /help."

# Buttons
BTN_MAIN_MENU = "Главное меню"
BTN_CANCEL = "Отмена"
BTN_SKIP = "Пропустить"
BTN_BACK = "Назад"
BTN_YES = "Да"
BTN_NO = "Нет"

# Add more strings as features are developed, e.g., for /newpost steps, errors, confirmations
# Post Creation
MSG_POST_CREATION_CANCELLED = "Создание поста отменено."
MSG_POST_TEXT_PROMPT = "Введите текст для вашего поста (поддерживается Markdown/HTML):"
MSG_POST_SAVED_DRAFT = "Пост сохранен как черновик."
MSG_POST_SCHEDULED = "Пост запланирован на {publish_time}."
MSG_POST_PUBLISHED = "Пост успешно опубликован!"
