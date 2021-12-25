# Import Telegram Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, RegexHandler
from telegram.ext import ConversationHandler, CallbackQueryHandler, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

# Import PKG
from vars import *

# Enable Logging
convLogger = logging.getLogger(__name__)
convLogger.addHandler(ConvLogHandler)

errorLogger = logging.getLogger(__name__)
errorLogger.addHandler(ErrorLogHandler)


#################### DEF: ECHO ####################

def echo(update, context):
  convLog(update, convLogger)
  
  message = '\U000026A0 *서버 점검 중입니다.*\n테슬라 오로라는 더 나은 서비스를 제공하기 위해 아주 가끔씩 꼭 필요한 점검만을 진행하고 있습니다\U0001F925\n점검이 종료되는대로 알림을 보내드릴게요:)'
  update.message.reply_text(message, reply_markup = ReplyKeyboardRemove(), parse_mode = 'Markdown')


#################### EXECUTION ####################

def main():
  updater = Updater(telegram_token, use_context = True)

  updater.dispatcher.add_handler(MessageHandler(Filters.all, echo))
  updater.start_polling(timeout = 1, drop_pending_updates = True)
  updater.idle()

if __name__ == '__main__':
  main()