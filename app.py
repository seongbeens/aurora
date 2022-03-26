# Import Telegram Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, RegexHandler
from telegram.ext import ConversationHandler, CallbackQueryHandler, Filters
#from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

# Import PKG
from join import *
from menu import *
import control

# Enable Logging
convLogger = logging.getLogger(__name__)
convLogger.addHandler(ConvLogHandler)

errorLogger = logging.getLogger(__name__)
errorLogger.addHandler(ErrorLogHandler)


#################### DEF: ENTRY POINT ####################

def start(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  basics = sql.inquiryAccount(update.message.chat_id, ['banned', 'nickname', 'phone', 'email'])
  tokens = sql.inquiryAccount(update.message.chat_id, ['token_refresh', 'token_access', 'default_vehicle'])
  
  # No Exist Telegram ID:
  if basics is None:
    message = '*오로라에 처음 오셨군요*\U0001F44B\U0001F44B\n서비스 가입하기를 눌러 진행해주세요.'
    keyboard = [['서비스 가입하기 \U0001F978']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return START_JOIN

  else:
    # Verify Banned User
    if basics[0] == 1: 
      message = '*서비스 이용이 제한되었습니다.*\n자세한 사항은 @TeslaAuroraCS 로 문의해주세요.'
      update.message.reply_text(message, parse_mode = 'Markdown')
    
      return ConversationHandler.END

    # Exist Telegram_id, Name, Phone Number, E-Mail:
    if not None in basics:

      # Exist Refresh/Access Token, Default Vehicle:
      if not None in tokens:        
        return mainMenu(update, context, rtn = 1)

      # No Exist Refresh/Access Token or Default Vehicle:
      else:
        message = '*다시 오신 것을 환영합니다*\U0001F970\n서버에 토큰 또는 차량 정보가 없어요:(\n등록을 진행하려면 아래 버튼을 누르세요.'
        keyboard = [['토큰 등록 계속하기']]

        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
        update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

        return RESUME_GET_TOKEN

    # No Exist Name, Phone Number, E-Mail:
    else:
      message = '*오로라에 처음 오셨군요*\U0001F44B\U0001F44B\n서비스 가입하기를 눌러 진행해주세요.'
      keyboard = [['서비스 가입하기 \U0001F978']]

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

      return START_JOIN

def mainMenu(update, context, rtn = None):
  if not rtn:
    # Logging Conversation
    convLog(update, convLogger)
  
  default_vehicle = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]
  vehicle_name = sql.inquiryVehicle(update.message.chat_id, default_vehicle, ['vehicle_name'])[0]
  vehicle_state = getVehCurrent(update.message.chat_id, default_vehicle)

  if vehicle_state == 401:
    message = '\U000026A0 *액세스 토큰이 만료되었습니다.*\n토큰을 자동으로 갱신하고 있어요\U0001F609\n잠시만 기다려주세요.'
    editable_msg = update.message.reply_text(message, parse_mode = 'Markdown')

    res = Token(update.message.chat_id).renewal()
    if res == 0:
      context.bot.deleteMessage(message_id = editable_msg.message_id, chat_id = update.message.chat_id)
      return mainMenu(update, context, rtn = 1)

    elif res == 1:
      return refreshToken(update, context, rtn = editable_msg)
      
    else:
      update.message.reply_text(str(res), parse_mode = 'Markdown')

  elif vehicle_state == 404:
    message = '\U000026A0 *액세스 토큰이 만료되었습니다.*\n토큰을 자동으로 갱신하고 있어요\U0001F609\n잠시만 기다려주세요.'
    editable_msg = update.message.reply_text(message, parse_mode = 'Markdown')
    
    return refreshToken(update, context, rtn = editable_msg)

  else:
    message = '이용하실 메뉴를 선택해주세요\U0001F636\n*{} 차량은 {}!*\n\n'.format(vehicle_name, state[vehicle_state])
    keyboard = [['\U0001F5F3 내 차 브리핑', '\U0001F697 커맨드 앤 컨트롤'],
                ['\U0001F6A6 스케줄링', '\U000023F0 오로라 알리미'],
                ['\U00002734 내 차 찾기', '\U0001F3DD 근처 충전소 찾기'],
                ['\U00002699 계정 및 연동 설정']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')
    
    message = '\U0001F38A *오로라 사용자들을 위한 소통방이 생겼어요!*\n@TeslaAurora 를 눌러 그룹에 들어와보세요:)'
    update.message.reply_text(message, parse_mode = 'Markdown')

  return MAIN_MENU

def refreshToken(update, context, rtn = None):
  if not rtn:
    # Logging Conversation
    convLog(update, convLogger)

  # Message
  message = '\U000026A0 *Tesla 계정 인증이 만료되었습니다.*\nTesla Refresh 토큰의 업데이트가 필요합니다.'
  if rtn: rtn.edit_text(message, parse_mode = 'Markdown')
  else: update.message.reply_text(message, parse_mode = 'Markdown')

  message = '*토큰 업데이트 방법을 알려드릴게요!*\n'\
          + '\U00002714 토큰 발급 앱을 실행합니다. '\
          + '설치 바로가기: [iOS](https://apps.apple.com/kr/app/auth-app-for-tesla/id1552058613) 또는 '\
          + '[Android](https://play.google.com/store/apps/details?id=net.leveugle.teslatokens)\n'\
          + '\U00002714 앱에서 Tesla 계정으로 로그인하고, Refresh 토큰의 값을 복사하세요.\n'\
          + '\U00002714 복사한 값을 정확히 아래에 붙혀 넣으면 됩니다.'
  update.message.reply_text(message, parse_mode = 'Markdown', disable_web_page_preview = True)

  message = '*Refresh Token을 입력해주세요.*\n\U000026A0 위 링크의 앱 이외의 경로로 발급한 토큰은 이용에 제한이 있을 수 있습니다.'
  update.message.reply_text(message, parse_mode = 'Markdown')

  return JOIN_GET_TOKEN


#################### DEF: ECHO & CANCEL ####################

def echo(update, context):
  conversation = ['/start', '/cancel']
  if update.message.text in conversation: pass
  else:
    # Logging Conversation
    convLog(update, convLogger)

    # Message
    message = '테슬라 오로라에 오신 것을 환영해요\U0001F60E\n'\
            + '서비스를 시작하시려면 /start를 입력하거나, 아래 버튼을 선택해주세요\U0001F9DA'
    keyboard = [['/start']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

def cancel(update, context):
  convLog(update, convLogger)
    
  update.message.reply_text('이용이 종료되었습니다\U0001F9DA\n다음 기회에 다시 찾아뵙기를 희망합니다\U0001F3C3',
                            reply_markup = ReplyKeyboardRemove())

  return ConversationHandler.END


#################### EXECUTION ####################

def main():
  updater = Updater(telegram_token, use_context = True)

  convHandler = ConversationHandler(
    entry_points = [MessageHandler(~Filters.regex('^(/cancel|/stop|/종료)$'), start, run_async = True)],
    states = {
      # COMMON
      GOTO_MENU:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.text, start, run_async = True)],

      # APP.PY
      START_JOIN:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^서비스 가입하기 \U0001F978$'), privacyAgreement)],
      RESUME_GET_TOKEN:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^토큰 등록 계속하기$'), getToken_resume)],
      EXPIRED_GET_TOKEN:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.text, verifyToken_expired, run_async = True)],
      EXPIRED_DEFAULT_VEH:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^\U0001F519'), start, run_async = True),
        MessageHandler(Filters.text, verifyVehicle_expired, run_async = True)],
      MAIN_MENU:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^\U0001F5F3'), STAT_Start, run_async = True),
        MessageHandler(Filters.regex('^\U0001F697'), control.menu),
        MessageHandler(Filters.regex('^\U0001F6A6'), SCHEDL_Menu),
        MessageHandler(Filters.regex('^\U000023F0'), REMIND_Menu),
        MessageHandler(Filters.regex('^\U0001F3DD'), NEAR_Start, run_async = True),
        MessageHandler(Filters.regex('^\U00002734'), FIND_Location, run_async = True),
        MessageHandler(Filters.regex('^\U00002699'), SETT_Menu),
        MessageHandler(~Filters.regex('^(/cancel|\U0001F5F3|\
        \U0001F697|\U000023F0|\U0001F6A6|\U0001F3DD|\U00002699)'), mainMenu)],

      # JOIN.PY
      JOIN_AGREEMENT:
        [MessageHandler(Filters.regex('^네, 동의합니다.$'), getName),
        MessageHandler(~Filters.regex('^네, 동의합니다.$'), privacyDisagree)],
      JOIN_GET_NAME:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^[가-힣]{2,8}$'), getPhone),
        MessageHandler(~Filters.regex('^[가-힣]{2,8}$'), incorrect_getName)],
      JOIN_GET_PHONE:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^01(?:0|1|[6-9])(\\d{3}|\\d{4})(\\d{4})$'), getEmail),
        MessageHandler(~Filters.regex('^01(?:0|1|[6-9])(\\d{3}|\\d{4})(\\d{4})$'), incorrect_getPhone)],
      JOIN_GET_EMAIL:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^([a-z0-9_\.-]+)@([\da-z\.-]+)\.([a-z\.]{2,6})$'), getToken),
        MessageHandler(~Filters.regex('^([a-z0-9_\.-]+)@([\da-z\.-]+)\.([a-z\.]{2,6})$'), incorrect_getEmail)],
      JOIN_GET_TOKEN:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.text, verifyToken_join, run_async = True)],
      JOIN_DEFAULT_VEH:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^\U0001F519'), start, run_async = True),
        MessageHandler(Filters.text, verifyVehicle_join, run_async = True)],

      # MENU.PY
      # STATUS
      STATUS:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^\U0001F3F7'), STAT_Help),
        MessageHandler(Filters.regex('^\U0001F519'), mainMenu)],

      # CONTROL(CONTROL.PY)
      CONT_MENU:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^\U0001F3F7'), control.help),                
        MessageHandler(Filters.regex('^\U0001F519'), mainMenu),
        MessageHandler(Filters.text, control.start, run_async = True)],
      CONT_BACK:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^\U0001F519'), control.menu)],
      CONT_TEMP_INPUT:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        CallbackQueryHandler(control.Temperatures.confirm)],
      CONT_TEMP_CONFIRM:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        CallbackQueryHandler(control.Temperatures.set)],
      
      # SCHEDULING
      SCHEDULING_MENU:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^감시모드 자동화$'), Sentry_.menu),
        MessageHandler(Filters.regex('^절전 방지 스케줄링$'), PreventSleep_.menu),
        MessageHandler(Filters.regex('^프리컨디셔닝 자동화$'), PreConditioning_.menu),
        MessageHandler(Filters.regex('^충전 종료 시간 설정$'), ChargeStop_.menu),
        MessageHandler(Filters.regex('^\U0001F519'), mainMenu)],

      # SCHE - SENTRY
      SENTRY_MENU:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^스케줄 추가$'), Sentry_.addDay),
        MessageHandler(Filters.regex('^스케줄 삭제$'), Sentry_.delSelect, run_async = True),
        MessageHandler(Filters.regex('^\U0001F3F7'), Sentry_.help),
        MessageHandler(Filters.regex('^\U0001F519'), SCHEDL_Menu)],
      SENTRY_ADD_DAY:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^[월화수목금토일]{1,7}$'), Sentry_.addTime),
        MessageHandler(Filters.text, Sentry_.addDay_invalid),
        CallbackQueryHandler(Sentry_.addCancel_1)],
      SENTRY_ADD_TIME:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^([01][0-9]|2[0-3])([0-5][0-9])$'), Sentry_.addOnOff),
        MessageHandler(Filters.text, Sentry_.addTime_invalid),
        CallbackQueryHandler(Sentry_.addCancel_1)],
      SENTRY_ADD_ONOFF:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^(감시모드 켜기 설정|감시모드 끄기 설정)$'), Sentry_.addDone),
        MessageHandler(Filters.regex('^\U0001F519'), Sentry_.addCancel_2),
        MessageHandler(Filters.text, Sentry_.addOnOff_invalid)],
      SENTRY_DELETE:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^#[1-5]'), Sentry_.delDone),
        MessageHandler(Filters.regex('^\U0001F519'), Sentry_.menu),
        MessageHandler(Filters.text, Sentry_.del_invalid)],
      SENTRY_BACK:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^\U0001F519'), Sentry_.menu)],
      
      # SCHE - PREVENT
      PREVENT_MENU:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^스케줄 추가$'), PreventSleep_.addDay),
        MessageHandler(Filters.regex('^스케줄 삭제$'), PreventSleep_.delSelect, run_async = True),
        MessageHandler(Filters.regex('^\U0001F3F7'), PreventSleep_.help),
        MessageHandler(Filters.regex('^\U0001F519'), SCHEDL_Menu)],
      PREVENT_ADD_DAY:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^[월화수목금토일]{1,7}$'), PreventSleep_.addTime),
        MessageHandler(Filters.text, PreventSleep_.addDay_invalid),
        CallbackQueryHandler(PreventSleep_.addCancel)],
      PREVENT_ADD_TIME:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^([01][0-9]|2[0-3])([0-5][0-9])$'), PreventSleep_.addRemain),
        MessageHandler(Filters.text, PreventSleep_.addTime_invalid),
        CallbackQueryHandler(PreventSleep_.addCancel)],
      PREVENT_ADD_REMAIN:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^([0-9]|[01][0-9]|2[0-4])$'), PreventSleep_.addDone),
        MessageHandler(Filters.text, PreventSleep_.addRemain_invalid),
        CallbackQueryHandler(PreventSleep_.addCancel)],
      PREVENT_DELETE:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^#[1-5]'), PreventSleep_.delDone),
        MessageHandler(Filters.regex('^\U0001F519'), PreventSleep_.menu),
        MessageHandler(Filters.text, PreventSleep_.del_invalid)],
      PREVENT_BACK:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^\U0001F519'), PreventSleep_.menu)],
      
      # SCHE - PRECONDITIONING
      PRECON_MENU:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^스케줄 추가$'), PreConditioning_.addDay),
        MessageHandler(Filters.regex('^스케줄 삭제$'), PreConditioning_.delSelect, run_async = True),
        MessageHandler(Filters.regex('^\U0001F3F7'), PreConditioning_.help),
        MessageHandler(Filters.regex('^\U0001F519'), SCHEDL_Menu)],
      PRECON_ADD_DAY:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^[월화수목금토일]{1,7}$'), PreConditioning_.addTime),
        MessageHandler(Filters.text, PreConditioning_.addDay_invalid),
        CallbackQueryHandler(PreConditioning_.addCancel)],
      PRECON_ADD_TIME:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^([01][0-9]|2[0-3])([0-5][0-9])$'), PreConditioning_.addRemain),
        MessageHandler(Filters.text, PreConditioning_.addTime_invalid),
        CallbackQueryHandler(PreConditioning_.addCancel)],
      PRECON_ADD_REMAIN:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^([1-5][0-9]|60)$'), PreConditioning_.addDone),
        MessageHandler(Filters.text, PreConditioning_.addRemain_invalid),
        CallbackQueryHandler(PreConditioning_.addCancel)],
      PRECON_DELETE:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^#[1-5]'), PreConditioning_.delDone),
        MessageHandler(Filters.regex('^\U0001F519'), PreConditioning_.menu),
        MessageHandler(Filters.text, PreConditioning_.del_invalid)],
      PRECON_BACK:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^\U0001F519'), PreConditioning_.menu)],

      # SCHE - CHARGE STOP
      CHRGSTOP_ADD_TIME:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^([01][0-9]|2[0-3])([0-5][0-9])$'), ChargeStop_.addDone),
        MessageHandler(Filters.text, ChargeStop_.addTime_invalid),
        CallbackQueryHandler(ChargeStop_.addCancel)],
      CHRGSTOP_DELETE:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^스케줄 삭제$'), ChargeStop_.delDone, run_async = True),
        MessageHandler(Filters.regex('^\U0001F519'), SCHEDL_Menu)],
      CHRGSTOP_BACK:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^\U0001F519'), SCHEDL_Menu)],
      
      # REMIND
      REMIND_MENU:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^충전 시작 알림 설정$'), REMIND_ChrgStart_SelectVeh, run_async = True),
        MessageHandler(Filters.regex('^충전 완료 알림 설정$'), REMIND_ChrgComplete_SelectVeh, run_async = True),
        MessageHandler(Filters.regex('^경부하 충전 알림 설정$'), REMIND_ChrgTime_SelectVeh, run_async = True),
        MessageHandler(Filters.regex('^도어/창문 열림 알림 설정$'), REMIND_Vent_SelectVeh, run_async = True),
        MessageHandler(Filters.regex('^\U0001F519'), mainMenu)],
      REMIND_CHRGSTART_SELECT:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(~Filters.regex('^(\U0001F3F7|\U0001F519)'), REMIND_ChrgStart_Set, run_async = True),
        MessageHandler(Filters.regex('^\U0001F3F7'), REMIND_ChrgStart_Help),
        MessageHandler(Filters.regex('^\U0001F519'), REMIND_Menu)],
      REMIND_CHRGSTART_BACK:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^\U0001F519'), REMIND_ChrgStart_SelectVeh, run_async = True)],
      REMIND_CHRGCOMP_SELECT:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(~Filters.regex('^(\U0001F3F7|\U0001F519)'), REMIND_ChrgComplete_Set, run_async = True),
        MessageHandler(Filters.regex('^\U0001F3F7'), REMIND_ChrgComplete_Help),
        MessageHandler(Filters.regex('^\U0001F519'), REMIND_Menu)],
      REMIND_CHRGCOMP_BACK:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^\U0001F519'), REMIND_ChrgComplete_SelectVeh, run_async = True)],
      REMIND_CHRGTIME_SELECT:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(~Filters.regex('^(\U0001F3F7|\U0001F519)'), REMIND_ChrgTime_Set, run_async = True),
        MessageHandler(Filters.regex('^\U0001F3F7'), REMIND_ChrgTime_Help),
        MessageHandler(Filters.regex('^\U0001F519'), REMIND_Menu)],
      REMIND_CHRGTIME_BACK:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^\U0001F519'), REMIND_ChrgTime_SelectVeh, run_async = True)],
      REMIND_VENT_SELECT:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(~Filters.regex('^(\U0001F3F7|\U0001F519)'), REMIND_Vent_Set, run_async = True),
        MessageHandler(Filters.regex('^\U0001F3F7'), REMIND_Vent_Help),
        MessageHandler(Filters.regex('^\U0001F519'), REMIND_Menu)],
      REMIND_VENT_BACK:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^\U0001F519'), REMIND_Vent_SelectVeh, run_async = True)],

      # SETTING
      SETTING_MENU:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^내 차 정보$'), SETT_VehicleInfo),
        MessageHandler(Filters.regex('^테슬라 토큰 갱신$'), SETT_GetToken),
        MessageHandler(Filters.regex('^계정 정보 변경$'), SETT_Account),
        MessageHandler(Filters.regex('^자주 사용하는 차량 변경$'), SETT_DefaultVehicle),
        MessageHandler(Filters.regex('^\U0001F519'), start, run_async = True)],
      SETTING_TOKEN:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^(취소|돌아가기)$'), SETT_Menu),
        MessageHandler(Filters.text, SETT_VerifyToken, run_async = True)],
      SETTING_ACCOUNT:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^닉네임 바꾸기$'), SETT_ModifyName),
        MessageHandler(Filters.regex('^전화번호 바꾸기$'), SETT_ModifyPhone),
        MessageHandler(Filters.regex('^이메일 바꾸기$'), SETT_ModifyEmail),
        MessageHandler(Filters.regex('^서비스 탈퇴$'), SETT_Withdrawal_Noti),
        MessageHandler(Filters.regex('^\U0001F519'), SETT_Menu)],
      SETTING_MOD_NAME:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^[가-힣]{2,8}$'), SETT_ModifyName_done),
        MessageHandler(~Filters.regex('^[가-힣]{2,8}$'), SETT_ModifyName_invalid)],
      SETTING_MOD_PHONE:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^01(?:0|1|[6-9])(\\d{3}|\\d{4})(\\d{4})$'), SETT_ModifyPhone_done),
        MessageHandler(~Filters.regex('^01(?:0|1|[6-9])(\\d{3}|\\d{4})(\\d{4})$'), SETT_ModifyPhone_invalid)],
      SETTING_MOD_EMAIL:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^([a-z0-9_\.-]+)@([\da-z\.-]+)\.([a-z\.]{2,6})$'), SETT_ModifyEmail_done),
        MessageHandler(~Filters.regex('^([a-z0-9_\.-]+)@([\da-z\.-]+)\.([a-z\.]{2,6})$'), SETT_ModifyEmail_invalid)],
      SETTING_WITHDRAWAL:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^네, 탈퇴하겠습니다.$'), SETT_Withdrawal_Done),
        MessageHandler(Filters.regex('^\U0001F519'), SETT_Menu)],
      SETTING_DEFAULT_VEH:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^\U0001F519'), SETT_Menu),
        MessageHandler(Filters.text, SETT_VerifyVehicle, run_async = True)],
      SETTING_BACK:
        [CommandHandler('cancel', cancel),
        MessageHandler(Filters.regex('^/종료$'), cancel),
        MessageHandler(Filters.regex('^\U0001F519'), SETT_Menu)],
    },
    fallbacks = [CommandHandler('cancel', cancel)]
  )

  updater.dispatcher.add_handler(convHandler, group = 0)
  updater.start_polling(timeout = 1, drop_pending_updates = True)
  updater.idle()

if __name__ == '__main__':
  main()