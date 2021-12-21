import logging, logging.handlers

# Telegram Chat Bot Token
telegram_token = '2141967252:AAHbOShngBVTV8gon0EKo99zt3K_UMknMNM'


GOTO_MENU, \
START_JOIN, RESUME_GET_TOKEN, MAIN_MENU, \
JOIN_AGREEMENT, JOIN_GET_NAME, JOIN_GET_PHONE, JOIN_GET_EMAIL, JOIN_GET_TOKEN, JOIN_DEFAULT_VEH, \
STATUS, \
CONT_MENU, CONT_BACK, CONT_TEMP_INPUT, CONT_TEMP_CONFIRM, CONT_CHRGLMIT_INPUT, \
SCHEDULING_MENU, \
SENTRY_MENU, SENTRY_ADD_DAY, SENTRY_ADD_TIME, SENTRY_ADD_ONOFF, SENTRY_DELETE, SENTRY_BACK, \
PREVENT_MENU, PREVENT_ADD_DAY, PREVENT_ADD_TIME, PREVENT_ADD_REMAIN, PREVENT_DELETE, PREVENT_BACK, \
REMIND_MENU, \
REMIND_CHRGCOMP_SELECT, REMIND_CHRGCOMP_BACK, \
REMIND_CHRGTIME_SELECT, REMIND_CHRGTIME_BACK, \
SETTING_MENU, SETTING_TOKEN, SETTING_ACCOUNT, SETTING_DEFAULT_VEH, \
SETTING_MOD_NAME, SETTING_MOD_PHONE, SETTING_MOD_EMAIL, \
SETTING_WITHDRAWAL, SETTING_BACK = range(43)


# Enable Logging
logging.basicConfig(
  format = '[%(asctime)s][%(name)s][%(levelname)s] %(message)s',
  datefmt = '%Y/%m/%d][%H:%M:%S',
  level = logging.INFO )

ErrorLogHandler = logging.handlers.TimedRotatingFileHandler(filename = 'logs/error.log', when = 'midnight', interval = 1, encoding = 'utf-8')
ErrorLogHandler.setFormatter(logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s', datefmt = '%Y/%m/%d][%H:%M:%S'))
ErrorLogHandler.setLevel(logging.ERROR)
ErrorLogHandler.suffix = '%Y%m%d'

SchedLogHandler = logging.handlers.TimedRotatingFileHandler(filename = 'logs/schedule.log', when = 'midnight', interval = 1, encoding = 'utf-8')
SchedLogHandler.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s', datefmt = '%Y/%m/%d][%H:%M:%S'))
SchedLogHandler.setLevel(logging.INFO)
SchedLogHandler.suffix = '%Y%m%d'

ConvLogHandler = logging.handlers.TimedRotatingFileHandler(filename = 'logs/conversation.log', when = 'midnight', interval = 1, encoding = 'utf-8')
ConvLogHandler.setFormatter(logging.Formatter('[%(asctime)s][%(name)s] %(message)s', datefmt = '%Y/%m/%d][%H:%M:%S'))
ConvLogHandler.setLevel(logging.INFO)
ConvLogHandler.suffix = '%Y%m%d'

# Global DEF
def getUsername(update):
  _a = ''
  if update.effective_message.from_user.last_name: _a += update.effective_message.from_user.last_name
  if update.effective_message.from_user.first_name: _a += update.effective_message.from_user.first_name
  return _a

def convLog(update, convLogger):
  if update.message.text:
    convLogger.info(getUsername(update) + '({}) : '.format(update.message.chat_id) + update.message.text)
  elif update.message.sticker:
    convLogger.info(getUsername(update) + '({}) : '.format(update.message.chat_id) + update.message.sticker.emoji)