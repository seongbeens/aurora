from telegram.ext import Updater, CommandHandler, MessageHandler, RegexHandler
from telegram.ext import ConversationHandler, CallbackQueryHandler, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Bot

from api import *

NOTI_INPUT, NOTI_CONFIRM, PNOTI_PHOTO_INPUT, PNOTI_TEXT_INPUT, PNOTI_CONFIRM = range(5)

# 회원 수(오늘 가입자 수)
# 차량 수

# 실시간 공지 기능
# chat_id로 회원정보 조회
# veh_id로 차량정보 조회

# Telegram
telegram_token = '5050977880:AAGz6a_cZYVWXurdDMbAbr_shqejjJ4uDis' #테슬라오로라
bot = Bot(token = telegram_token)
telegram_token = '2141967252:AAHbOShngBVTV8gon0EKo99zt3K_UMknMNM' #라딘이
updater = Updater(telegram_token, use_context = True)

# Enable logging
logger = logging.getLogger('admin')


def adminAuthentication(chat_id):
  if chat_id == 1704527105: return True
  else: return False

def build_button(texts, callback_header = '') : # make button list
    lists, h = [], 0
    text_header = callback_header

    if callback_header != '': text_header += ','

    for i in texts:
      lists.append([])
      for j in i: lists[h].append(InlineKeyboardButton(j, callback_data = text_header + j))
      h += 1

    return lists

def build_menu(buttons):
    menu, h = [], 0

    for i in buttons:
      menu.append([])
      for j in i: menu[h].append(j)
      h += 1

    return menu

class Report:
  def result(self, update, context):
    if adminAuthentication(update.message.chat_id):
      # Counts Vars
      counts_allUsers, counts_actualUsers, counts_recreateUsers, counts_vehicles = 0, 0, 0, 0

      for i in sql.inquiryAccounts(['vehicle_counts']):
        if not None in i:
          if i[1] > 0:
            counts_allUsers += 1
            counts_actualUsers += 1
          else:
            counts_allUsers += 1
        else:
          counts_allUsers += 1

      for i in sql.inquiryAccounts(['date_recreate']):
        if not None in i:
          counts_recreateUsers += 1
      
      for i in sql.inquiryVehicles():
        counts_vehicles += 1
      
      try:
        conn = sql.connect()
        counts_todayUsers = conn.cursor().execute("SELECT * FROM Accounts "\
        + "WHERE DATE(date_create) = CURRENT_DATE()")
      
        counts_oldUsers = conn.cursor().execute("SELECT * FROM Accounts "\
        + "WHERE DATE(date_recent) < CURRENT_DATE()-90")
      
      finally:
        conn.close()

      update.message.reply_text('가입한 전체 회원은 *{}명*,\n차량이 정상 등록된 사용자는 *{}명*,\n재가입자는 *{}명*, 오늘 하루 가입자는 *{}명*,\n90일 이상 장기 미접속자는 *{}명*,\n등록된 전체 차량은 *{}대*입니다.'
        .format(str(counts_allUsers), str(counts_actualUsers), str(counts_recreateUsers), str(counts_todayUsers), str(counts_oldUsers), str(counts_vehicles)), parse_mode = 'Markdown')

      return ConversationHandler.END
    
    else: return ConversationHandler.END


class Notice:
  def input(self, update, context):
    if adminAuthentication(update.message.chat_id):
      update.message.reply_text('*공지할 메세지를 입력하세요.*', parse_mode = 'Markdown')

      return NOTI_INPUT
    
    else: return ConversationHandler.END

  def confirm(self, update, context):
    self.message = update.message.text
    
    buttons = build_button([['전송', '취소']], 'NOTICE')
    reply_markup = InlineKeyboardMarkup(build_menu(buttons))

    update.message.reply_text('*메세지를 보낼까요?*', reply_markup = reply_markup, parse_mode = 'Markdown')

    return NOTI_CONFIRM
  
  def execution(self, update, context):
    if update.callback_query.data.split(',')[0] == 'NOTICE':
      if update.callback_query.data.split(',')[1] == '전송':
        text = '*공지사항을 전달하는 중입니다...*'
        context.bot.edit_message_text(text = text, parse_mode = 'Markdown',
                                    chat_id = update.callback_query.message.chat_id,
                                    message_id = update.callback_query.message.message_id)

        for i in sql.inquiryAccounts(['vehicle_counts']):
          if not None in i:
            if i[1] > 0:
              # if i[0] == 1704527105:
                try:
                  reply_markup = ReplyKeyboardMarkup(
                    [['\U0001F920']], one_time_keyboard = True, resize_keyboard = True)
                  bot.send_message(chat_id = i[0],
                    text = self.message, reply_markup = reply_markup, parse_mode = 'Markdown')
                    #text = self.message, reply_markup = reply_markup, parse_mode = 'Markdown', disable_notification = True)
                  logger.info('Sending message. ({})'.format(i[0]))
                  time.sleep(0.01)
                except Exception as e:
                  logger.warning(e)
          
        logger.info('Done sending messages.')
        text = '*전송이 완료되었습니다.*'
    
      else:
        text = '*전송이 취소되었습니다.*'

      context.bot.edit_message_text(text = text, parse_mode = 'Markdown',
                                    chat_id = update.callback_query.message.chat_id,
                                    message_id = update.callback_query.message.message_id)

    return ConversationHandler.END


class PhotoNotice:
  def input_photo(self, update, context):
    if adminAuthentication(update.message.chat_id):
      update.message.reply_text('*공지할 사진을 전송하세요.*', parse_mode = 'Markdown')

      return PNOTI_PHOTO_INPUT
    
    else: return ConversationHandler.END

  def input_text(self, update, context):
    self.photo = context.bot.getFile(update.message.photo[-1].file_id).download('photo.jpg')
    update.message.reply_text('*공지할 메세지를 입력하세요.*', parse_mode = 'Markdown')

    return PNOTI_TEXT_INPUT

  def confirm(self, update, context):
    self.message = update.message.text
    
    buttons = build_button([['전송', '취소']], 'PNOTICE')
    reply_markup = InlineKeyboardMarkup(build_menu(buttons))

    update.message.reply_text('*메세지를 보낼까요?*', reply_markup = reply_markup, parse_mode = 'Markdown')

    return PNOTI_CONFIRM
  
  def execution(self, update, context):
    if update.callback_query.data.split(',')[0] == 'PNOTICE':
      if update.callback_query.data.split(',')[1] == '전송':
        text = '*공지사항을 전달하는 중입니다...*'
        context.bot.edit_message_text(text = text, parse_mode = 'Markdown',
                                    chat_id = update.callback_query.message.chat_id,
                                    message_id = update.callback_query.message.message_id)

        for i in sql.inquiryAccounts(['vehicle_counts']):
          if not None in i:
            if i[1] > 0:
              # if i[0] == 1704527105:
                try:
                  reply_markup = ReplyKeyboardMarkup(
                    [['\U0001F920']], one_time_keyboard = True, resize_keyboard = True)
                  bot.send_photo(chat_id = i[0],
                    photo = open('photo.jpg', 'rb'), caption = self.message, reply_markup = reply_markup, parse_mode = 'Markdown')
                    # disable_notification = True)
                  logger.info('Sending message. ({})'.format(i[0]))
                  time.sleep(0.01)
                except Exception as e:
                  logger.warning(e)
          
        logger.info('Done sending messages.')
        text = '*전송이 완료되었습니다.*'
    
      else:
        text = '*전송이 취소되었습니다.*'

      context.bot.edit_message_text(text = text, parse_mode = 'Markdown',
                                    chat_id = update.callback_query.message.chat_id,
                                    message_id = update.callback_query.message.message_id)

    return ConversationHandler.END

def sendDoc(update, context):
  url = 'logs/error.log'
  context.bot.send_document(chat_id = update.message.chat_id, document = url)
  # telegram.error.BadRequest: Invalid file http url specified: unsupported url protocol
  
  return ConversationHandler.END

def test_inlineURL(update, context):
  update.message.reply_text(
    'Subscribe to us on Facebook and Telegram:',
    reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton(text='on Facebook', url='https://facebook.com')],
        [InlineKeyboardButton(text='on Telegram', url='https://t.me')],
    ])
  )

#init
Noti = Notice()
PNoti = PhotoNotice()

test_conv_handler = ConversationHandler(
  entry_points = [CommandHandler('notice', Noti.input, pass_args = True),
                  CommandHandler('photo', PNoti.input_photo, pass_args = True),
                  CommandHandler('report', Report().result, pass_args = True),
                  CommandHandler('doc', sendDoc, pass_args = True)],
  states = {
    NOTI_INPUT:
      [MessageHandler(Filters.text, Noti.confirm)],
    NOTI_CONFIRM:
      [CallbackQueryHandler(Noti.execution)],
    PNOTI_PHOTO_INPUT:
      [MessageHandler(Filters.photo, PNoti.input_text)],
    PNOTI_TEXT_INPUT:
      [MessageHandler(Filters.text, PNoti.confirm)],
    PNOTI_CONFIRM:
      [CallbackQueryHandler(PNoti.execution)],
  },
  fallbacks = [CommandHandler('hey', Noti.input, pass_args = True)])

updater.dispatcher.add_handler(test_conv_handler)

updater.start_polling(timeout = 3, drop_pending_updates = True)
updater.idle()


# url='https://github.com/gc/TelegramBotDemo/raw/main/test.pdf'
# context.bot.send_document(chat_id=get_chat_id(update, context), document=url)



# try:
#     query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(reply_keyboard))
# except:
#     return