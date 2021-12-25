from telegram.ext import ConversationHandler, CallbackQueryHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

from api import *

# Enable Logging
convLogger = logging.getLogger(__name__)
convLogger.addHandler(ConvLogHandler)

errorLogger = logging.getLogger(__name__)
errorLogger.addHandler(ErrorLogHandler)


def __getVehicle(update, context, editable_msg):
  veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]
  veh_state = getVehCurrent(update.message.chat_id, veh_id)

  # Return True
  if (not veh_id is None) & (not veh_state is None):
    if veh_state in ['asleep', 'offline']:
      message = '\U0001F4AB *차량을 깨우고 있습니다...*\n1분 이상의 시간이 소요될 수 있습니다.\n'\
              + '로딩이 완료되면 알림을 보내드릴거에요\U0001F60C'
      editable_msg.edit_text(message, parse_mode = 'Markdown')
    
      if wakeVehicle(update.message.chat_id, veh_id): return veh_id, editable_msg
      else:
        context.bot.deleteMessage(
          message_id = editable_msg.message_id, chat_id = update.message.chat_id)

        message = '\U000026A0 *차량을 깨울 수 없습니다.*\n일시적인 통신 불량일 수 있지만, '\
                + 'Deep Sleep 상태인 경우 직접 차량의 도어를 개폐하여 차량을 깨워야 할 수 있습니다.'
        keyboard = [['\U0001F519 돌아가기']]

        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
        update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

        return GOTO_MENU
    
    elif veh_state == 'online': return veh_id, editable_msg

    else:
      context.bot.deleteMessage(
        message_id = editable_msg.message_id, chat_id = update.message.chat_id)

      message = '\U000026A0 *알 수 없는 오류가 발생했어요.*\n'\
              + '오류를 제보해주시면 조속히 해결하도록 하겠습니다.\n아래 오류코드를 캡처하여 @TeslaAurora 로 문의해주세요.\n'\
              + '불편을 끼쳐 드려서 죄송합니다.\n\n'\
              + '\__getVehicle.veh_\__state.params.error: {}_\n'.format(veh_state)
      keyboard = [['\U0001F519 돌아가기']]

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')
      
      errorLogger.error(
        getUsername(update) + '({}) : '.format(update.message.chat_id) +
        '__getVehicle.veh_state.params.error: ' + veh_state)
      
      return GOTO_MENU #state 파라미터 확인 후 수정 필요
  
  # Return False
  else:
    # Message
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)
    
    message = '\U000026A0 *알 수 없는 오류가 발생했어요.*\n'\
            + '오류를 제보해주시면 조속히 해결하도록 하겠습니다.\n아래 오류코드를 캡처하여 @TeslaAurora 로 문의해주세요.\n'\
            + '\__getVehicle.veh_\__id.return.error_\n'\
            + '\__getVehicle.veh_\__state.return.error_\n'
    keyboard = [['\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    errorLogger.error(
      getUsername(update) + '({}) : '.format(update.message.chat_id) +
      '__getVehicle.veh_id.return.error: ' + str(veh_id))
    errorLogger.error(
      getUsername(update) + '({}) : '.format(update.message.chat_id) +
      '__getVehicle.veh_state.return.error: ' + veh_state)
    
    return GOTO_MENU




# Vehicle Control
def menu(update, context, rtn = False):
  if not rtn:
    # Logging Conversation
    convLog(update, convLogger)

  # Message
  message = '커맨드 앤 컨트롤 메뉴에요\U0001F636'
  keyboard = [['차량 잠그고 열기', '창문 환기 또는 닫기'],
              ['감시모드 켜고 끄기', '헤드라이트 점멸'],
              ['공조기 켜고 끄기', '공조기 온도 설정'],
              ['충전구 열고 닫기', '충전포트 잠금 해제'],
              ['\U0001F3F7 도움말', '\U0001F519 돌아가기']]

              # ['시트 열선 설정', '스티어링 휠 열선 설정'],
              # ['충전구 열고 닫기', '충전 목표량 설정'],

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.effective_message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return CONT_MENU

def start(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  if update.message.text in [
    '차량 잠그고 열기', '창문 환기 또는 닫기',
    '감시모드 켜고 끄기', '헤드라이트 점멸',
    '공조기 켜고 끄기', '공조기 온도 설정',
    '충전구 열고 닫기', '충전포트 잠금 해제']: return verify(update, context, update.message.text)
  else:
    message = '\U000026A0 *올바르지 않은 메뉴입니다.1*'
    keyboard = [['\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return CONT_BACK

def verify(update, context, command, editable_msg = None):
  if not editable_msg:
    # Message
    message = '\U0001F4AB *토큰을 확인하고 있습니다...*'
    editable_msg = update.message.reply_text(message, parse_mode = 'Markdown')
    
  else: # Retry Def: VS_verify
    message = '\U0001F44F *토큰 갱신이 완료되었습니다!*'
    editable_msg.edit_text(message, parse_mode = 'Markdown')

  # Verify Access Token
  if Token(update.message.chat_id).verify():
    message = '\U0001F4AB *차량을 확인하고 있습니다...*'
    editable_msg.edit_text(message, parse_mode = 'Markdown')

    veh_id, editable_msg = __getVehicle(update, context, editable_msg)
    if veh_id:
      if   command == '차량 잠그고 열기':
        return lock_unlock(update, context, veh_id, editable_msg)
      elif command == '창문 환기 또는 닫기':
        return window_vent_close(update, context, veh_id, editable_msg)
      elif command == '감시모드 켜고 끄기':
        return sentry_on_off(update, context, veh_id, editable_msg)
      elif command == '헤드라이트 점멸':
        return flash_headlight(update, context, veh_id, editable_msg)
      elif command == '공조기 켜고 끄기':
        return HVAC_on_off(update, context, veh_id, editable_msg)
      elif command == '공조기 온도 설정':
        return Temperatures.input(update, context, veh_id, editable_msg)
      elif command == '충전구 열고 닫기':
        return chargeport_door(update, context, veh_id, editable_msg)
      elif command == '충전포트 잠금 해제':
        return chargeport_unlock(update, context, veh_id, editable_msg)
      else:
        return unknown(update, context, veh_id, editable_msg)
      
  else: # Token Expired
    # Message
    message = '\U000026A0 *액세스 토큰이 만료되었습니다.*\n토큰을 자동으로 갱신하고 있어요\U0001F609\n잠시만 기다려주세요.'
    editable_msg.edit_text(message, parse_mode = 'Markdown')

    # Renewal Access Token
    if Token(update.message.chat_id).renewal() == 0:
      return verify(update, context, command, editable_msg)
      
    else:
      message = '\U000026A0 *토큰 갱신에 실패했습니다.*\n다시 한 번 시도해볼게요:(\n잠시만 기다려주세요.'
      editable_msg.edit_text(message, parse_mode = 'Markdown')

      # Renewal Access Token(1-More-Time)
      _a = Token(update.message.chat_id).renewal()
      if _a == 0: return verify(update, context, command, editable_msg)
      else:
        if _a == 1: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: VC\_TOKEN\_GEN\_1\n'
        elif _a == 2: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: VC\_TOKEN\_GEN\_2\n'
        elif _a == 3: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: VC\_TOKEN\_GEN\_3\n'
        elif _a == 4: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: VC\_TOKEN\_GEN\_4\n'
        elif _a == 5: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: VC\_TOKEN\_GEN\_5\n'
        elif _a == 6: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: VC\_TOKEN\_GEN\_6\n'
        elif _a == 7: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: VC\_TOKEN\_GEN\_7\n'
        elif _a == 8: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: VC\_TOKEN\_GEN\_8\n'
        else: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: VC\_TOKEN\_GEN\_9\n'
      message += '@TeslaAurora 로 문의해주세요.'
      keyboard = [['\U0001F519 돌아가기']]

      context.bot.deleteMessage(
        message_id = editable_msg.message_id, chat_id = update.message.chat_id)

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')
            
      return GOTO_MENU

# Commands
def lock_unlock(update, context, veh_id, editable_msg):
  _a = lockToggle(update.message.chat_id, veh_id)
  
  # Check State of Locked
  if _a == 1: # Unlock
    # Delete Loading Message
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)
    
    # Message
    message = '\U0001F31F *문이 열렸습니다.*'
    update.message.reply_text(message, parse_mode = 'Markdown')
    
    return menu(update, context, True)

  elif _a == 0: # Lock
    # Delete Loading Message
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)

    # Message
    message = '\U0001F31F *문이 잠겼습니다.*'
    update.message.reply_text(message, parse_mode = 'Markdown')

    return menu(update, context, True)

  else: return failed()

def window_vent_close(update, context, veh_id, editable_msg):
  _a = windowToggle(update.message.chat_id, veh_id)
  
  # Check State of Window
  if _a == 1: # Vent
    # Delete Loading Message
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)
    
    # Message
    message = '\U0001F31F *창문이 열렸습니다.*'
    update.message.reply_text(message, parse_mode = 'Markdown')
    
    return menu(update, context, True)

  elif _a == 0: # Close
    # Delete Loading Message
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)

    # Message
    message = '\U0001F31F *창문이 닫혔습니다.*'
    update.message.reply_text(message, parse_mode = 'Markdown')

    return menu(update, context, True)

  else: return failed()

def sentry_on_off(update, context, veh_id, editable_msg):
  _a = sentryToggle(update.message.chat_id, veh_id)
  
  # Check State of Locked
  if _a == 1: # Turn ON
    # Delete Loading Message
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)
    
    # Message
    message = '\U0001F31F *감시모드가 켜졌습니다.*'
    update.message.reply_text(message, parse_mode = 'Markdown')
    
    return menu(update, context, True)

  elif _a == 0: # Turn OFF
    # Delete Loading Message
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)

    # Message
    message = '\U0001F31F *감시모드가 꺼졌습니다.*'
    update.message.reply_text(message, parse_mode = 'Markdown')

    return menu(update, context, True)

  else: return failed()

def flash_headlight(update, context, veh_id, editable_msg):
  if flashlights(update.message.chat_id, veh_id):
    # Delete Loading Message
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)
    
    # Message
    message = '\U0001F31F *헤드라이트가 점멸했습니다.*'
    update.message.reply_text(message, parse_mode = 'Markdown')
    
    return menu(update, context, True)

  else: return failed()  

def HVAC_on_off(update, context, veh_id, editable_msg):
  _a = HVACToggle(update.message.chat_id, veh_id)
  
  # Check State of Locked
  if not _a == 0: # Turn ON
    # Delete Loading Message
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)
    
    # Message
    message = '\U0001F31F *공조기가 {}도로 켜졌습니다.*'.format(_a)
    update.message.reply_text(message, parse_mode = 'Markdown')
    
    return menu(update, context, True)

  elif _a == 0: # Turn OFF
    # Delete Loading Message
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)

    # Message
    message = '\U0001F31F *공조기가 꺼졌습니다.*'
    update.message.reply_text(message, parse_mode = 'Markdown')

    return menu(update, context, True)

  else: return failed()

class Temperature:
  def callbackMarkup(self, chat_id, types, data):
    self.reply_markup_1 = InlineKeyboardMarkup([
      [InlineKeyboardButton('LO', callback_data = data + ' 15.0'),
       InlineKeyboardButton('16도', callback_data = data + ' 16.0'),
       InlineKeyboardButton('17도', callback_data = data + ' 17.0'),
       InlineKeyboardButton('18도', callback_data = data + ' 18.0'),
       InlineKeyboardButton('19도', callback_data = data + ' 19.0'),
       InlineKeyboardButton('>>', callback_data = data + ' GOTO2')],
      [InlineKeyboardButton('설정 취소', callback_data = data + ' CANCEL')]
    ])

    self.reply_markup_2 = InlineKeyboardMarkup([
      [InlineKeyboardButton('<<', callback_data = data + ' GOTO1'),
       InlineKeyboardButton('20도', callback_data = data + ' 20.0'),
       InlineKeyboardButton('21도', callback_data = data + ' 21.0'),
       InlineKeyboardButton('22도', callback_data = data + ' 22.0'),
       InlineKeyboardButton('23도', callback_data = data + ' 23.0'),
       InlineKeyboardButton('>>', callback_data = data + ' GOTO3')],
      [InlineKeyboardButton('설정 취소', callback_data = data + ' CANCEL')]
    ])

    self.reply_markup_3 = InlineKeyboardMarkup([
      [InlineKeyboardButton('<<', callback_data = data + ' GOTO2'),
       InlineKeyboardButton('24도', callback_data = data + ' 24.0'),
       InlineKeyboardButton('25도', callback_data = data + ' 25.0'),
       InlineKeyboardButton('26도', callback_data = data + ' 26.0'),
       InlineKeyboardButton('27도', callback_data = data + ' 27.0'),
       InlineKeyboardButton('HI', callback_data = data + ' 28.0')],
      [InlineKeyboardButton('설정 취소', callback_data = data + ' CANCEL')]
    ])
    
    self.confirm_markup = InlineKeyboardMarkup([
      [InlineKeyboardButton('네', callback_data = data + ' YES'),
       InlineKeyboardButton('아니오', callback_data = data + ' NO')],
      [InlineKeyboardButton('설정 취소', callback_data = data + ' CANCEL')]
    ])

    self.default_markup = self.reply_markup_2

    if types == 'DEFAULT': return self.default_markup
    if types == 'GOTO1': return self.reply_markup_1
    if types == 'GOTO2': return self.reply_markup_2
    if types == 'GOTO3': return self.reply_markup_3
    if types == 'TEMP': return self.confirm_markup

  def input(self, update, context, veh_id, editable_msg):
    # Delete Loading Message
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)

    text = '*설정할 온도를 선택해주세요.*\n화살표를 눌러 좌우로 이동할 수 있습니다.'
    markup = self.callbackMarkup(update.message.chat_id, 'DEFAULT', str(veh_id))
    update.message.reply_text(text, reply_markup = markup, parse_mode = 'Markdown')

    return CONT_TEMP_INPUT

  def confirm(self, update, context):
    __veh_id, __factor = str(update.callback_query.data).split()
    convLogger.info(getUsername(update) + '({}) : '
    .format(update.callback_query.message.chat_id) + __factor)

    if __factor == 'CANCEL':
      text = '*공조기 온도 설정이 취소되었습니다.*'
      update.callback_query.message.edit_text(text, parse_mode = 'Markdown')
      
      return menu(update, context, True)

    elif __factor == 'GOTO1':
      text = '*설정할 온도를 선택해주세요.*'
      markup = self.callbackMarkup(update.callback_query.message.chat_id, 'GOTO1', __veh_id)
      update.callback_query.message.edit_text(text, reply_markup = markup, parse_mode = 'Markdown')

      return CONT_TEMP_INPUT

    elif __factor == 'GOTO2':
      text = '*설정할 온도를 선택해주세요.*'
      markup = self.callbackMarkup(update.callback_query.message.chat_id, 'GOTO2', __veh_id)
      update.callback_query.message.edit_text(text, reply_markup = markup, parse_mode = 'Markdown')

      return CONT_TEMP_INPUT

    elif __factor == 'GOTO3':
      text = '*설정할 온도를 선택해주세요.*'
      markup = self.callbackMarkup(update.callback_query.message.chat_id, 'GOTO3', __veh_id)
      update.callback_query.message.edit_text(text, reply_markup = markup, parse_mode = 'Markdown')

      return CONT_TEMP_INPUT

    elif __factor == '15.0':
      text = '*온도를 LO로 설정할까요?*'
      markup = self.callbackMarkup(update.callback_query.message.chat_id, 'TEMP', update.callback_query.data)
      update.callback_query.message.edit_text(text, reply_markup = markup, parse_mode = 'Markdown')

      return CONT_TEMP_CONFIRM

    elif __factor == '28.0':
      text = '*온도를 HI로 설정할까요?*'
      markup = self.callbackMarkup(update.callback_query.message.chat_id, 'TEMP', update.callback_query.data)
      update.callback_query.message.edit_text(text, reply_markup = markup, parse_mode = 'Markdown')

      return CONT_TEMP_CONFIRM

    else:
      text = '*온도를 {}도로 설정할까요?*'.format(str(__factor).replace('.0', ''))
      markup = self.callbackMarkup(update.callback_query.message.chat_id, 'TEMP', update.callback_query.data)
      update.callback_query.message.edit_text(text, reply_markup = markup, parse_mode = 'Markdown')
      
      return CONT_TEMP_CONFIRM

  def set(self, update, context):
    __veh_id, __temp, __factor = str(update.callback_query.data).split()
    convLogger.info(getUsername(update) + '({}) : '
    .format(update.callback_query.message.chat_id) + __factor)

    if __factor == 'YES':
      text = '\U0001F4AB *차량과 통신하고 있습니다...*'
      update.callback_query.message.edit_text(text, parse_mode = 'Markdown')

      if setHVACTemp(update.callback_query.message.chat_id, __veh_id, float(__temp)):
        if float(__temp) == 15.0: dp_temp = str(__temp).replace('15.0', 'LO')
        if float(__temp) == 28.0: dp_temp = str(__temp).replace('28.0', 'HI')
        else: dp_temp = str(__temp).replace('.0', '도')

        text = '\U0001F31F *공조기 온도가 {}로 설정되었습니다.*'.format(dp_temp)
        update.callback_query.message.edit_text(text, parse_mode = 'Markdown')
        
        return menu(update, context, True)
    
    elif __factor == 'NO':
      text = '*설정할 온도를 선택해주세요.*\n화살표를 눌러 좌우로 이동할 수 있습니다.'
      markup = self.callbackMarkup(update.callback_query.message.chat_id, 'DEFAULT', __veh_id)
      update.callback_query.message.edit_text(text, reply_markup = markup, parse_mode = 'Markdown')
      
      return CONT_TEMP_INPUT

    else:
      text = '*공조기 온도 설정이 취소되었습니다.*'
      update.callback_query.message.edit_text(text, parse_mode = 'Markdown')
      
      return menu(update, context, True)


def chargeport_door(update, context, veh_id, editable_msg):
  _a = portToggle(update.message.chat_id, veh_id)
  
  if _a == 1: # Turn Open
    # Delete Loading Message
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)
    
    # Message
    message = '\U0001F31F *충전구가 열렸습니다.*'
    update.message.reply_text(message, parse_mode = 'Markdown')
    
    return menu(update, context, True)

  elif _a == 0: # Turn Close
    # Delete Loading Message
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)

    # Message
    message = '\U0001F31F *충전구가 닫혔습니다.*'
    update.message.reply_text(message, parse_mode = 'Markdown')

    return menu(update, context, True)

  elif _a == -1: # Driving
    # Delete Loading Message
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)

    # Message
    message = '\U000026A0 *주행 중에는 충전구를 열 수 없습니다.*\n충전구를 열려면 기어가 P단이어야 합니다.'
    update.message.reply_text(message, parse_mode = 'Markdown')

    return menu(update, context, True)

  elif _a == -2: # Latched
    # Delete Loading Message
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)

    # Message
    message = '\U000026A0 *충전기가 연결되어 있습니다.*\n충전구를 닫으려면 충전기를 분리해주세요.'
    update.message.reply_text(message, parse_mode = 'Markdown')

    return menu(update, context, True)

  else: return failed()

def chargeport_unlock(update, context, veh_id, editable_msg):
  _a = portUnlock(update.message.chat_id, veh_id)
  
  if _a == 1: # Unlock
    # Delete Loading Message
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)
    
    # Message
    message = '\U0001F31F *충전포트 잠금이 풀렸습니다.*'
    update.message.reply_text(message, parse_mode = 'Markdown')
    
    return menu(update, context, True)

  elif _a == 0: # Invalid Condition
    # Delete Loading Message
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)
    
    # Message
    message = '\U000026A0 *충전기가 연결되어 있지 않습니다.*\n충전기가 연결된 충전포트를 잠금 해제할 수 있습니다.'
    update.message.reply_text(message, parse_mode = 'Markdown')
    
    return menu(update, context, True)

  else: return failed()

def failed(update, context, veh_id, editable_msg = None):
  if editable_msg:
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)

  # Message
  message = '\U000026A0 *명령을 완료할 수 없습니다.*\n일시적인 통신 불량일 수 있습니다.\n'\
          + '오류가 지속되는 경우 @TeslaAurora 로 문의해주세요.'
  keyboard = [['\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return GOTO_MENU

def unknown(update, context, veh_id, editable_msg):
  message = '\U000026A0 *올바르지 않은 메뉴입니다.*'
  update.message.reply_text(message, parse_mode = 'Markdown')

  return menu(update, context, True)


def help(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '\U0001F9D0 *토글 메뉴가 무엇인가요?*\n'\
        + '끄고 켜는 전원 스위치처럼 동작하는 형태를 토글이라고 합니다.\n'\
        + '예를 들어, \'차량 잠그고 열기\'는 차량 도어를 잠그거나 잠금을 해제하는 것 이외의 옵션이 없어요.\n'\
        + '반면, 공조기의 온도를 설정할 때는 18도, 21도, 24도 등 우리가 원하는 온도 값으로 맞추어야 해요.\n'\
        + '이러한 토글 기능을 실행할 때는 사용자가 버튼을 누를 때 곧 바로 실행돼요.'
  keyboard = [['\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  message = '\U0001F9D0 *더 많은 커맨드가 필요하시나요?*\n'\
          + '테슬라 오로라 유저들이 제일 많이 사용하는 커맨드를 구현시켜 놓았어요:)\n'\
          + '커맨드는 사용자의 선호도에 따라 언제든 추가 또는 삭제가 이루어질 수 있어요.\n'\
          + '많은 사람들에게 꼭 필요한 커맨드가 있다고 생각드실 때 언제든 @TeslaAurora 로 문의해주세요!'
  update.message.reply_text(message, parse_mode = 'Markdown')

  return CONT_BACK


# Enable Classes
Temperatures = Temperature()