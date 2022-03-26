from telegram.ext import ConversationHandler, CallbackQueryHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

from api import *
from dicts import *

# Enable Logging
convLogger = logging.getLogger(__name__)
convLogger.addHandler(ConvLogHandler)

errorLogger = logging.getLogger(__name__)
errorLogger.addHandler(ErrorLogHandler)


# DEF
# Common
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
              + '오류를 제보해주시면 조속히 해결하도록 하겠습니다.\n아래 오류코드를 캡처하여 @TeslaAuroraCS 로 문의해주세요.\n'\
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
            + '오류를 제보해주시면 조속히 해결하도록 하겠습니다.\n아래 오류코드를 캡처하여 @TeslaAuroraCS 로 문의해주세요.\n'\
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

# Vehicle State
def STAT_Start(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  return STAT_Verify(update, context)

def STAT_Verify(update, context, editable_msg = None):
  if not editable_msg:
    # Purpose to ReplyKeyboardRemove()
    context.bot.deleteMessage(
      message_id = update.message.reply_text('*모듈을 로딩하고 있습니다...*',
      reply_markup = ReplyKeyboardRemove(), parse_mode = 'Markdown').message_id, chat_id = update.message.chat_id)
    
    # Message
    message = '\U0001F4AB *토큰을 확인하고 있습니다...*'
    editable_msg = update.message.reply_text(message, parse_mode = 'Markdown')
    
  else: # Retry Def: VS_tokenVerify
    # Message
    message = '\U0001F44F *토큰 갱신이 완료되었습니다!*'
    editable_msg.edit_text(message, parse_mode = 'Markdown')

  # Verify Access Token
  if Token(update.message.chat_id).verify():
    message = '\U0001F4AB *차량을 확인하고 있습니다...*'
    editable_msg.edit_text(message, parse_mode = 'Markdown')

    veh_id, editable_msg = __getVehicle(update, context, editable_msg)
    if veh_id: return STAT_Execution(update, context, veh_id, editable_msg)

  else: # Token Expired
    # Message
    message = '\U000026A0 *액세스 토큰이 만료되었습니다.*\n토큰을 자동으로 갱신하고 있어요\U0001F609\n잠시만 기다려주세요.'
    editable_msg.edit_text(message, parse_mode = 'Markdown')

    # Renewal Access Token
    if Token(update.message.chat_id).renewal() == 0:
      return STAT_Verify(update, context, editable_msg)

    else:
      message = '\U000026A0 *토큰 갱신에 실패했습니다.*\n다시 한 번 시도해볼게요:(\n잠시만 기다려주세요.'
      editable_msg.edit_text(message, parse_mode = 'Markdown')

      # Renewal Access Token(1-More-Time)
      _a = Token(update.message.chat_id).renewal()
      if _a == 0: return STAT_Verify(update, context, editable_msg)
      else:
        if _a == 1: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: VS\_TOKEN\_GEN\_1\n'
        elif _a == 2: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: VS\_TOKEN\_GEN\_2\n'
        elif _a == 3: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: VS\_TOKEN\_GEN\_3\n'
        elif _a == 4: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: VS\_TOKEN\_GEN\_4\n'
        elif _a == 5: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: VS\_TOKEN\_GEN\_5\n'
        elif _a == 6: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: VS\_TOKEN\_GEN\_6\n'
        elif _a == 7: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: VS\_TOKEN\_GEN\_7\n'
        elif _a == 8: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: VS\_TOKEN\_GEN\_8\n'
        else: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: VS\_TOKEN\_GEN\_9\n'
      message += '@TeslaAuroraCS 로 문의해주세요.'
      keyboard = [['\U0001F519 돌아가기']]

      context.bot.deleteMessage(
        message_id = editable_msg.message_id, chat_id = update.message.chat_id)

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')
            
      return GOTO_MENU

def STAT_Execution(update, context, veh_id, editable_msg):
  # Message
  message = '\U0001F4AB *데이터를 가져오고 있습니다...*\n로딩이 완료되면 알림을 보내드릴거에요\U0001F60C'
  editable_msg.edit_text(message, parse_mode = 'Markdown')
    
  vehData = getVehData(update.message.chat_id, veh_id)
  
  columns = ['sentry_switch_1', 'sentry_switch_2', 'sentry_switch_3', 'sentry_switch_4', 'sentry_switch_5']
  scheSentrys = sql.inquirySchedule(update.message.chat_id, veh_id, columns)

  columns = ['prevent_sleep_1', 'prevent_sleep_2']
  schePrevents = sql.inquirySchedule(update.message.chat_id, veh_id, columns)

  columns = ['preconditioning_1', 'preconditioning_2', 'preconditioning_3', 'preconditioning_4', 'preconditioning_5']
  schePrecons = sql.inquirySchedule(update.message.chat_id, veh_id, columns)

  # Delete Loading Message
  context.bot.deleteMessage(
    message_id = editable_msg.message_id, chat_id = update.message.chat_id)
    
  if not vehData:
    # Message
    message = '\U000026A0 *데이터를 가져올 수 없습니다.*\n일시적인 통신 불량일 수 있지만, '\
            + 'Deep Sleep 상태인 경우 직접 차량의 도어를 개폐하여 차량을 깨워야 할 수 있습니다.'
    keyboard = [['\U0001F3F7 도움말', '\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return STATUS

  # Messages
  # 공통
  message  = '*{}의 상태를 알려드릴게요\U0001F606*\n'.format(vehData['display_name'])
  if vehData['drive_state']['shift_state'] in ['D', 'N', 'R']:
    message += '\U0001F512 차량이 {}km/h로 주행하고 있어요.\n'.format(round(vehData['drive_state']['speed']*1.609344))
  else:
    message += locked[vehData['vehicle_state']['locked']]
    message += '{}.\n'.format(state[vehData['state']])
  message += '\U0001F50B 배터리는 {}%이고, '.format(vehData['charge_state']['battery_level'])
  message += '{}km 갈 수 있어요.\n'.format(round(vehData['charge_state']['battery_range']*1.609344))
  if not vehData['climate_state']['outside_temp'] is None:
    message += '\U00002600 외부 기온은 {}도, '.format(vehData['climate_state']['outside_temp'])
    message += '실내는 {}도에요.\n'.format(vehData['climate_state']['inside_temp'])
  message += '{}'.format(is_climate_on[vehData['climate_state']['is_climate_on']])
  if vehData['climate_state']['is_climate_on']:
    message += '{}단계에요.\n'.format(vehData['climate_state']['fan_status'])
    if vehData['climate_state']['climate_keeper_mode'] != 'off':
      message += '  \*  실내 온도 유지 모드도 켜져 있어요.\n'
  message += '{}\n'.format(sentry_mode[vehData['vehicle_state']['sentry_mode']])
  message += '\U0001F4A1 누적 주행거리는 {0:,}km에요.\n'.format(round(vehData['vehicle_state']['odometer']*1.609344))
  message += '\U0001F50E SW 버전은 {}입니다.\n'.format(vehData['vehicle_state']['car_version'].split()[0])
    
  '''
  #온도 관련(climate_state)
    + '온도유지 모드 : climate_keeper_mode'\
    + '시트 열선 켜짐 : seat_heater_left, seat_heater_right, seat_heater_rear_left, seat_heater_rear_center, seat_heater_rear_right'\
    + '스티어링 휠 열선 켜짐 : steering_wheel_heater'

  # 주행 관련(drive_state)
    + '위치 : heading, latitude, longitude '
  '''
  keyboard = [['\U0001F3F7 도움말', '\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  # 충전 관련(charging_state)
  if vehData['charge_state']['charging_state'] == 'Charging':
    left_time = [vehData['charge_state']['minutes_to_full_charge']//60, vehData['charge_state']['minutes_to_full_charge']%60]

    message = '\U0001F50C *차량을 충전 중이네요!*\n'\
            + '현재 충전 속도와 전류는 *' + str(vehData['charge_state']['charger_power'])\
            + 'kW, ' + str(vehData['charge_state']['charge_current_request'])\
            + 'A*입니다.\n충전 목표량은 *' + str(vehData['charge_state']['charge_limit_soc'])\
            + '%*로 설정되어 있어요.\n충전 완료까지 남은 시간은 *'
    if left_time[0] == 0: message += str(left_time[1]) + '분*이에요.'
    elif left_time[1] == 0: message += str(left_time[0]) + '시간*이에요.'
    else: message += str(left_time[0]) + '시간 ' + str(left_time[1]) + '분*이에요.'
    if vehData['charge_state']['charge_current_request_max'] > vehData['charge_state']['charge_current_request']:
      message += '\n충전 전류를 *' + str(vehData['charge_state']['charge_current_request_max'])\
              +  'A*까지 높일 수 있어요.\n'
    update.message.reply_text(message, parse_mode = 'Markdown')
  elif vehData['charge_state']['charging_state'] == 'NoPower':
    message = '\U0001F50C *충전기가 연결되어 있습니다!*\n'\
            + '충전 중이지 않지만, 충전기가 감지되었어요.\n'\
            + '충전 목표량은 *' + str(vehData['charge_state']['charge_limit_soc'])\
            + '%*로,\n충전 전류는 *' + str(vehData['charge_state']['charge_current_request'])\
            + 'A*로 설정되어 있어요.\n'\
            + '\U000023F0 경부하 충전 시간대를 기다리고 계신다면 오로라의 경부하 충전 시간 알리미를 이용해보세요:)\n'
    update.message.reply_text(message, parse_mode = 'Markdown')

  # 소프트웨어 관련(vehicle_state/software_update)
  if vehData['vehicle_state']['software_update']['status'] == 'downloading_wifi_wait':
    message = '\U0001F199 *새로운 소프트웨어 다운로드가 가능합니다!*\n'\
            + str(vehData['vehicle_state']['software_update']['version'])\
            + ' 버전 소프트웨어를 다운로드할 수 있어요:)\n'\
            + '와이파이를 연결하고 새로운 소프트웨어를 다운로드 받아보세요\U0001F929\n'\
            + '*\U000026A0 주행 중에는 절대 업데이트하지 마십시오.*'
    update.message.reply_text(message, parse_mode = 'Markdown')

  elif vehData['vehicle_state']['software_update']['status'] == 'downloading':
    message = '\U0001F199 *소프트웨어 업데이트 다운로드 중! ('\
            + str(vehData['vehicle_state']['software_update']['download_perc'])\
            + '%)*\n'\
            + str(vehData['vehicle_state']['software_update']['version'])\
            + ' 버전 소프트웨어를 다운로드하고 있어요:)\n'\
            + '다운로드가 완료되면 Tesla 앱에서 업데이트를 실행할 수 있답니다\U0001F929\n'\
            + '*\U000026A0 주행 중에는 절대 업데이트하지 마십시오.*'
    update.message.reply_text(message, parse_mode = 'Markdown')

  elif vehData['vehicle_state']['software_update']['status'] == 'available':
    message = '\U0001F199 *소프트웨어 업데이트가 가능해요!*\n'\
            + str(vehData['vehicle_state']['software_update']['version'])\
            + ' 버전 소프트웨어가 준비되었습니다:)\n'\
            + '멋있고 신비로운 기능을 기대하면서 Tesla 앱에서 업데이트를 진행해보세요\U0001F929\n'\
            + '*\U000026A0 주행 중에는 절대 업데이트하지 마십시오.*'
    update.message.reply_text(message, parse_mode = 'Markdown')

  elif vehData['vehicle_state']['software_update']['status'] == 'scheduled':
    message = '\U0001F199 *소프트웨어 업데이트가 곧 시작됩니다!*\n'\
            + str(vehData['vehicle_state']['software_update']['version'])\
            + ' 버전으로 곧 업데이트될 거에요:)\n이번 업데이트는 '\
            + str(vehData['vehicle_state']['software_update']['expected_duration_sec']//60)\
            + '분 정도 소요된답니다\U0001F929\n'\
            + '*\U000026A0 주행 중에는 절대 업데이트하지 마십시오.*'
    update.message.reply_text(message, parse_mode = 'Markdown')

  elif vehData['vehicle_state']['software_update']['status'] == 'installing':
    message = '\U0001F199 *소프트웨어 업데이트 진행 중! ('\
            + str(vehData['vehicle_state']['software_update']['install_perc'])\
            + '%)*\n'\
            + str(vehData['vehicle_state']['software_update']['version'])\
            + ' 버전으로 업데이트하고 있습니다:)\n'\
            + '업데이트 중에는 절대 주행하지 마세요\U0000203C\n'
    update.message.reply_text(message, parse_mode = 'Markdown')
  
  if scheSentrys:
    validCnts = 0
    message = '\U0001F422 *등록된 감시모드 스케줄이 있어요.*'

    for i, j in enumerate(scheSentrys):
      if j:
        if len(j) == 12:
          message += '\n*#' + str(i+1) + '* ' + DayOfWeek[j[:7]] + ' ' + j[7:9] + ':' + j[9:11]
          if j[11] == '0': message += '에 감시모드 끔'
          else: message += '에 감시모드 켬'
          validCnts += 1
    
    if validCnts > 0:
      update.message.reply_text(message, parse_mode = 'Markdown')

  if schePrevents:
    validCnts = 0
    message = '\U0001F995 *등록된 절전방지 스케줄이 있어요.*'

    for i, j in enumerate(schePrevents):
      if j:
        if len(j) == 13:
          message += '\n*#' + str(i+1) + '* ' + DayOfWeek[j[:7]] + ' ' + j[7:9] + ':' + j[9:11]
          message += '부터 ' + str(int(j[11:])) + '시간'
          validCnts += 1
    
    if validCnts > 0:
      update.message.reply_text(message, parse_mode = 'Markdown')


  if schePrecons:
    validCnts = 0
    message = '\U0001F996 *등록된 프리컨디셔닝 스케줄이 있어요.*'

    for i, j in enumerate(schePrecons):
      if j:
        if len(j) == 13:
          message += '\n*#' + str(i+1) + '* ' + DayOfWeek[j[:7]] + ' ' + j[7:9] + ':' + j[9:11]
          message += '부터 ' + str(int(j[11:])) + '분'
          validCnts += 1
    
    if validCnts > 0:
      update.message.reply_text(message, parse_mode = 'Markdown')

  
  return STATUS

def STAT_Help(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '\U0001F9D0 *실시간으로 보여지는 정보가 다르나요?*\n'\
          + '테슬라 오로라는 최적화된 정보를 제공하기 위해 차량의 실시간 상태에 따라 노출되는 정보가 변경되기도 해요.\n'\
          + '예를 들어 충전 중일 때는 평소에 보이지 않던 충전 전류와 남은 시간에 대한 정보가 추가로 보이기도 하죠.\n'\
          + '불편한 사항은 언제든 @TeslaAuroraCS 로 문의주시면 적극 개선하도록 노력할게요!'
  keyboard = [['\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  message = '\U0001F9D0 *로딩이 느린 이유가 무엇인가요?*\n'\
          + '테슬라는 배터리 소모를 줄이기 위해 주차 후 일정 시간이 경과하면 절전 모드로 진입해요.\n'\
          + '정확한 차량의 정보를 가져오려면 절전을 해제하여야 하고, 이 때 1분 내외의 시간이 소요됩니다.\n'\
          + '차량이 절전 모드로 진입하지 않게 하려면 감시모드를 활성화하거나 테슬라 오로라가 제공하는 절전 방지 스케줄링을 사용해주세요.'
  update.message.reply_text(message, parse_mode = 'Markdown')

  return STATUS


# Reminder - Common
def REMIND_KeyboardMarkup_vehicles(update, context, column):
  # Vehicles Vars
  keyboard, h = [], 0
  keyboard.append([])

  # Markup Keyboard
  try:
    for i in sql.inquiryVehicle(update.message.chat_id, None, ['vehicle_name', column]):
      if len(keyboard[h]) == 1:
        keyboard.append([])
        h += 1
      if i[1] == 1: keyboard[h].append(i[0] + ' \U000023F3 알림 끄기')
      else: keyboard[h].append(i[0] + ' \U0001F6CE 알림 켜기')
    return keyboard

  except:
    keyboard = [['\U0001F519 돌아가기']]
    return keyboard

def REMIND_Menu(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '오로라 알리미 메뉴에요\U0001F636'
  keyboard = [['충전 시작 알림 설정', '충전 완료 알림 설정'], ['경부하 충전 알림 설정', '도어/창문 열림 알림 설정'], ['\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return REMIND_MENU

# Reminder - Start Charging Alert
def REMIND_ChrgStart_SelectVeh(update, context, rtn = None):
  if not rtn:
    # Logging Conversation
    convLog(update, convLogger)

  # Message
  message = '*알림을 받을 차량을 설정하세요.*\n'\
          + '알림을 설정하면 충전이 시작될 때 메시지로 알려줍니다.'
  keyboard = REMIND_KeyboardMarkup_vehicles(update, context, 'noti_chrgstart')
  keyboard += [['\U0001F3F7 도움말', '\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return REMIND_CHRGSTART_SELECT

def REMIND_ChrgStart_Set(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  veh_id, veh_name, variable = None, None, 0

  # Get Vehicle Name in Text
  if '\U0001F6CE' in str(update.message.text):
    veh_name, variable = str(update.message.text).split(' \U0001F6CE ')[0], 1
  elif '\U000023F3' in str(update.message.text):
    veh_name, variable = str(update.message.text).split(' \U000023F3 ')[0], 0

  if veh_name:
    for i in sql.inquiryVehicle(update.message.chat_id, None, ['vehicle_id', 'vehicle_name']):
      if i[1] == veh_name: veh_id = i[0]
    
    if veh_id:
      if sql.modifyVehicle(update.message.chat_id, veh_id, ['noti_chrgstart'], [variable]):
        message = '\U0001F31F *설정이 완료되었습니다.*'
        update.message.reply_text(message, parse_mode = 'Markdown')

        return REMIND_ChrgStart_SelectVeh(update, context, True)
      
      else: message = '\U000026A0 *설정에 실패했습니다.*\n잠시 후 다시 시도해주세요.'
    
    else: message = '\U000026A0 *차량을 찾을 수 없습니다.*\n임의의 텍스트를 입력할 수 없어요:(\n'\
                  + '차량 이름을 변경하셨다면 계정 및 연동 설정에서 토큰을 갱신하고 다시 시도해주세요.'
    
  else: message = '\U000026A0 *차량을 찾을 수 없습니다.*\n임의의 텍스트를 입력할 수 없어요:(\n'\
                + '차량 이름을 변경하셨다면 계정 및 연동 설정에서 토큰을 갱신하고 다시 시도해주세요.'

  keyboard = [['\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return REMIND_CHRGSTART_BACK

def REMIND_ChrgStart_Help(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '\U0001F9D0 *충전 시작 알림이란?*\n충전기를 언제 연결했든 상관 없이 '\
          + '*실제로 충전이 시작되면 알림을 보내드리는 기능입니다.*\n'\
          + '데스티네이션 차저나 전용 완속 충전기가 있는 환경에서 유용하게 사용할 수 있습니다.'
  keyboard = [['\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return REMIND_CHRGSTART_BACK

# Reminder - Charging Complete Alert
def REMIND_ChrgComplete_SelectVeh(update, context, rtn = None):
  if not rtn:
    # Logging Conversation
    convLog(update, convLogger)

  # Message
  message = '*알림을 받을 차량을 설정하세요.*\n'\
          + '알림을 설정하면 충전 완료 10분 전, 5분 전 및 충전이 완료되었을 때 알려줍니다.'
  keyboard = REMIND_KeyboardMarkup_vehicles(update, context, 'noti_chrgcomplete')
  keyboard += [['\U0001F3F7 도움말', '\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return REMIND_CHRGCOMP_SELECT

def REMIND_ChrgComplete_Set(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  veh_id, veh_name, variable = None, None, 0

  # Get Vehicle Name in Text
  if '\U0001F6CE' in str(update.message.text):
    veh_name, variable = str(update.message.text).split(' \U0001F6CE ')[0], 1
  elif '\U000023F3' in str(update.message.text):
    veh_name, variable = str(update.message.text).split(' \U000023F3 ')[0], 0

  if veh_name:
    for i in sql.inquiryVehicle(update.message.chat_id, None, ['vehicle_id', 'vehicle_name']):
      if i[1] == veh_name: veh_id = i[0]
    
    if veh_id:
      if sql.modifyVehicle(update.message.chat_id, veh_id, ['noti_chrgcomplete'], [variable]):
        message = '\U0001F31F *설정이 완료되었습니다.*'
        update.message.reply_text(message, parse_mode = 'Markdown')

        return REMIND_ChrgComplete_SelectVeh(update, context, True)
      
      else: message = '\U000026A0 *설정에 실패했습니다.*\n잠시 후 다시 시도해주세요.'
    
    else: message = '\U000026A0 *차량을 찾을 수 없습니다.*\n임의의 텍스트를 입력할 수 없어요:(\n'\
                  + '차량 이름을 변경하셨다면 계정 및 연동 설정에서 토큰을 갱신하고 다시 시도해주세요.'
    
  else: message = '\U000026A0 *차량을 찾을 수 없습니다.*\n임의의 텍스트를 입력할 수 없어요:(\n'\
                + '차량 이름을 변경하셨다면 계정 및 연동 설정에서 토큰을 갱신하고 다시 시도해주세요.'

  keyboard = [['\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return REMIND_CHRGCOMP_BACK

def REMIND_ChrgComplete_Help(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '\U0001F9D0 *충전 완료 알림이란?*\n충전이 완료되기까지 남은 시간을 계산하여 '\
          + '*충전 완료 10분 전, 5분 전 및 충전이 완료되었을 때 알림을 보내드리는 기능입니다.*\n'\
          + '슈퍼차징이나 급속 충전 중에 잠깐 자리를 비웠을 때 유용하게 사용할 수 있습니다.\n'\
          + '또한, 충전 완료 알림 기능을 켜고 충전 목표량을 100%로 설정 후 충전 완료 상태가 되면 '\
          + '현재 가용 가능한 주행 거리가 저장되며, 이는 계정 및 연동 설정에서 확인할 수 있습니다.'
  keyboard = [['\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return REMIND_CHRGCOMP_BACK

# Reminder - Charge Light-load Alert
def REMIND_ChrgTime_SelectVeh(update, context, rtn = None):
  if not rtn:
    # Logging Conversation
    convLog(update, convLogger)

  # Message
  message = '*알림을 받을 차량을 설정하세요.*\n'\
          + '알림을 설정하면 월~토요일 오후 11시에 충전 대기 상태인 경우 메시지로 알려줍니다.\n'
  keyboard = REMIND_KeyboardMarkup_vehicles(update, context, 'noti_chrgtime')
  keyboard += [['\U0001F3F7 도움말', '\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')
  
  message = '\U000026A0 공용 충전기의 경우, 반드시 충전기가 여유로운 환경에서만 사용하여 주시고 충전 에티켓을 준수하여 주시기 바랍니다.'
  update.message.reply_text(message, parse_mode = 'Markdown')

  return REMIND_CHRGTIME_SELECT

def REMIND_ChrgTime_Set(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  veh_id, veh_name, variable = None, None, 0

  # Get Vehicle Name in Text
  if '\U0001F6CE' in str(update.message.text):
    veh_name, variable = str(update.message.text).split(' \U0001F6CE ')[0], 1
  elif '\U000023F3' in str(update.message.text):
    veh_name, variable = str(update.message.text).split(' \U000023F3 ')[0], 0

  if veh_name:
    for i in sql.inquiryVehicle(update.message.chat_id, None, ['vehicle_id', 'vehicle_name']):
      if i[1] == veh_name: veh_id = i[0]
    
    if veh_id:
      if sql.modifyVehicle(update.message.chat_id, veh_id, ['noti_chrgtime'], [variable]):
        message = '\U0001F31F *설정이 완료되었습니다.*'
        update.message.reply_text(message, parse_mode = 'Markdown')
        
        return REMIND_ChrgTime_SelectVeh(update, context, True)
      
      else: message = '\U000026A0 *설정에 실패했습니다.*\n잠시 후 다시 시도해주세요.'
    
    else: message = '\U000026A0 *차량을 찾을 수 없습니다.*\n임의의 텍스트를 입력할 수 없어요:(\n'\
                  + '차량 이름을 변경하셨다면 계정 및 연동 설정에서 토큰을 갱신하고 다시 시도해주세요.'
    
  else: message = '\U000026A0 *차량을 찾을 수 없습니다.*\n임의의 텍스트를 입력할 수 없어요:(\n'\
                + '차량 이름을 변경하셨다면 계정 및 연동 설정에서 토큰을 갱신하고 다시 시도해주세요.'

  keyboard = [['\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return REMIND_CHRGTIME_BACK

def REMIND_ChrgTime_Help(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '\U0001F9D0 *경부하 충전 알림이란?*\n전용 충전기(월 커넥터 등)는 차량에서 충전 시간 예약을 설정할 수 있지만, '\
          + '공용 충전기는 일정 시간동안 충전되는 전력이 없으면 자동으로 결제가 취소되고 '\
          + '사용자가 원하는 충전 시간에 다시 결제해서 충전을 시작해야 하는 문제점이 있습니다.\n'\
          + '미리 충전기를 연결해두고 충전 시작을 잊어버리는 사용자를 위해 충전 중이지 않은 충전기에 연결되어 있다면 '\
          + '*우리나라 경부하 전력요금의 시작 시각(월-토 오후 11시)에 알림을 보내드리는 기능입니다.*\n'\
          + '기능을 활성화하면, 충전 상태 수집을 위해 알림 시각 3분 전에 차량을 깨웁니다.\n'\
          + '공용 충전기의 경우, 반드시 충전기가 여유로운 주거지에서만 사용하여 주시고, 충전 에티켓을 준수하여 주시기 바랍니다.'
  keyboard = [['\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return REMIND_CHRGTIME_BACK

# Reminder - Vent
def REMIND_Vent_SelectVeh(update, context, rtn = None):
  if not rtn:
    # Logging Conversation
    convLog(update, convLogger)

  # Message
  message = '*알림을 받을 차량을 설정하세요.*\n'\
          + '알림을 설정하면 주차 중 도어나 창문이 열린 채 5분이 지속되면 메시지로 알려줍니다.\n'
  keyboard = REMIND_KeyboardMarkup_vehicles(update, context, 'noti_vent')
  keyboard += [['\U0001F3F7 도움말', '\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return REMIND_VENT_SELECT

def REMIND_Vent_Set(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  veh_id, veh_name, variable = None, None, 0

  # Get Vehicle Name in Text
  if '\U0001F6CE' in str(update.message.text):
    veh_name, variable = str(update.message.text).split(' \U0001F6CE ')[0], 1
  elif '\U000023F3' in str(update.message.text):
    veh_name, variable = str(update.message.text).split(' \U000023F3 ')[0], 0

  if veh_name:
    for i in sql.inquiryVehicle(update.message.chat_id, None, ['vehicle_id', 'vehicle_name']):
      if i[1] == veh_name: veh_id = i[0]
    
    if veh_id:
      if sql.modifyVehicle(update.message.chat_id, veh_id, ['noti_vent'], [variable]):
        message = '\U0001F31F *설정이 완료되었습니다.*'
        update.message.reply_text(message, parse_mode = 'Markdown')
        
        return REMIND_Vent_SelectVeh(update, context, True)
      
      else: message = '\U000026A0 *설정에 실패했습니다.*\n잠시 후 다시 시도해주세요.'
    
    else: message = '\U000026A0 *차량을 찾을 수 없습니다.*\n임의의 텍스트를 입력할 수 없어요:(\n'\
                  + '차량 이름을 변경하셨다면 계정 및 연동 설정에서 토큰을 갱신하고 다시 시도해주세요.'
    
  else: message = '\U000026A0 *차량을 찾을 수 없습니다.*\n임의의 텍스트를 입력할 수 없어요:(\n'\
                + '차량 이름을 변경하셨다면 계정 및 연동 설정에서 토큰을 갱신하고 다시 시도해주세요.'

  keyboard = [['\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return REMIND_VENT_BACK

def REMIND_Vent_Help(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '\U0001F9D0 *도어/창문 열림 알림이란?*\n운전자가 없을 때 5분 이상 도어나 창문이 열려 있는 경우 '\
          + '알림과 함께 열려 있는 도어들을 알려줍니다.'
  keyboard = [['\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return REMIND_VENT_BACK

# Scheduling Menu
def SCHEDL_Menu(update, context, rtn = False):
  if not rtn:
    # Logging Conversation
    convLog(update, convLogger)

  # Message
  message = '스케줄링 메뉴에요\U0001F636'
  keyboard = [['감시모드 자동화', '절전 방지 스케줄링'], ['프리컨디셔닝 자동화', '충전 종료 시간 설정']]
  keyboard += [['\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.effective_message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return SCHEDULING_MENU

# Sentry Mode Automation - Common
class Sentry:
  def __init__(self) -> None:
    self.editable_msg = []
  
  def menu(self, update, context, rtn = False):
    if not rtn:
      # Logging Conversation
      convLog(update, convLogger)

    # Message
    message = '감시모드 자동화 메뉴에요\U0001F636'
    keyboard = [['스케줄 추가', '스케줄 삭제']]
    keyboard += [['\U0001F3F7 도움말', '\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.effective_message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return SENTRY_MENU

  def help(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    # Message
    message = '\U0001F9D0 *감시모드 자동화란?*\n'\
            + '감시모드를 매번 수동으로 Tesla 앱에서 작동시킬 필요 없이 '\
            + '특정 요일, 시각에 자동으로 켜고 끌 수 있는 스케줄링 기능입니다.\n'\
            + '스케줄은 최대 5개까지 등록할 수 있으며, 차량이 2대 이상인 경우 현재 선택된 차량에 대해 스케줄이 설정됩니다.\n'\
            + '한 번 등록한 스케줄을 변경하려면 직접 삭제하고 다시 등록하여야 합니다.'
    keyboard = [['\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return SENTRY_BACK

  # SENTRY - Add Schedule
  def findValue(self, chat_id, veh_id, type):
    columns = ['sentry_switch_1', 'sentry_switch_2', 'sentry_switch_3', 'sentry_switch_4', 'sentry_switch_5']
    lists = sql.inquirySchedule(chat_id, veh_id, columns)

    if not lists:
      sql.modifySchedule(chat_id, veh_id, ['sentry_switch_1'], [None])

    if type == 'DAY':
      for i, j in enumerate(lists):
        if j:
          if not len(j) == 12:
            return columns[i]
      
      for i, j in enumerate(lists):
        if not j:
          return columns[i]
      
      return 'FULL'
    
    for i, j in enumerate(lists):
      if type == 'TIME':
        if j:
          if len(j) == 7: return columns[i], j

      if type == 'ONOFF':
        if j:
          if len(j) == 11: return columns[i], j
    
    return 'NOT_FOUND', '0'

  def addDay(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    # Message
    message = '*스케줄을 설정할 요일을 입력하세요.*\n입력 형식 : 일~토 중에 1~7글자\n입력 예시 : 일, 월수금, 일월화수목금토 등'
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('설정 취소', callback_data = 'CANCEL')]])

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        self.editable_msg.remove(i)
        break

    self.editable_msg.append([
      update.message.chat_id, message,
      update.message.reply_text(message, reply_markup = markup, parse_mode = 'Markdown')
    ])
    
    return SENTRY_ADD_DAY

  def addDay_invalid(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        i[2].edit_text(text = i[1], reply_markup = InlineKeyboardMarkup([[]]), parse_mode = 'Markdown')
        break
    
    # Message
    message = '\U000026A0 *입력 형식에 맞지 않습니다.*\n입력 형식 : 일~토 중에 1~7글자\n입력 예시 : 일, 월수금, 일월화수목금토 등'
    update.message.reply_text(message, parse_mode = 'Markdown')

    message = '*스케줄을 설정할 요일을 입력하세요.*'
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('설정 취소', callback_data = 'CANCEL')]])
    
    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        self.editable_msg.remove(i)
        break

    self.editable_msg.append([
      update.message.chat_id, message,
      update.message.reply_text(message, reply_markup = markup, parse_mode = 'Markdown')
    ])

    return SENTRY_ADD_DAY

  def addTime(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    def _createTimestamp():
      _timestamp_list, _timestamp = [0 for _ in range(7)], ''

      if '월' in update.message.text: _timestamp_list[0] = 1
      if '화' in update.message.text: _timestamp_list[1] = 1
      if '수' in update.message.text: _timestamp_list[2] = 1
      if '목' in update.message.text: _timestamp_list[3] = 1
      if '금' in update.message.text: _timestamp_list[4] = 1
      if '토' in update.message.text: _timestamp_list[5] = 1
      if '일' in update.message.text: _timestamp_list[6] = 1
      for i in _timestamp_list: _timestamp += str(i)
      
      return _timestamp

    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]
    _column = Sentry_.findValue(update.message.chat_id, _veh_id, 'DAY')
    _timestamp = _createTimestamp()
    
    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        i[2].edit_text(text = i[1], reply_markup = InlineKeyboardMarkup([[]]), parse_mode = 'Markdown')
        break
    
    if _column == 'FULL':
      # Message
      message = '\U000026A0 *더 이상 스케줄을 추가할 수 없습니다.*\n'\
              + '감시모드 자동화 스케줄은 5개까지 저장할 수 있으며, 스케줄을 변경하시려면 기존 스케줄을 삭제한 후 새로 추가하여야 합니다.'
      keyboard = [['\U0001F519 돌아가기']]

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

      return SENTRY_BACK

    if sql.modifySchedule(update.message.chat_id, _veh_id, [_column], [_timestamp]):
      # Message
      message = '*스케줄을 설정할 시간을 입력하세요.*\n입력 형식 : 4자리 시간 형식(HHMM)\n입력 예시 : 0600, 1530, 2300 등'
      markup = InlineKeyboardMarkup([[InlineKeyboardButton('설정 취소', callback_data = 'CANCEL')]])
      
      for i in self.editable_msg:
        if i[0] == update.message.chat_id:
          self.editable_msg.remove(i)
          break

      self.editable_msg.append([
        update.message.chat_id, message,
        update.message.reply_text(message, reply_markup = markup, parse_mode = 'Markdown')
      ])

      return SENTRY_ADD_TIME

    else: return Sentry_.addTime(update, context)

  def addTime_invalid(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        i[2].edit_text(text = i[1], reply_markup = InlineKeyboardMarkup([[]]), parse_mode = 'Markdown')
        break
    
    # Message
    message = '\U000026A0 *입력 형식에 맞지 않습니다.*\n입력 형식 : 4자리 시간 형식(HHMM)\n입력 예시 : 0600, 1530, 2300 등'
    update.message.reply_text(message, reply_markup = ReplyKeyboardRemove(), parse_mode = 'Markdown')

    message = '*스케줄을 설정할 시간을 입력하세요.*'
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('설정 취소', callback_data = 'CANCEL')]])
    
    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        self.editable_msg.remove(i)
        break

    self.editable_msg.append([
      update.message.chat_id, message,
      update.message.reply_text(message, reply_markup = markup, parse_mode = 'Markdown')
    ])

    return SENTRY_ADD_TIME

  def addOnOff(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)
    
    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]
    _column, _timestamp = Sentry_.findValue(update.message.chat_id, _veh_id, 'TIME')
    _timestamp += str(update.message.text)

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        i[2].edit_text(text = i[1], reply_markup = InlineKeyboardMarkup([[]]), parse_mode = 'Markdown')
        break
    
    if _column == 'NOT_FOUND':
      # Message
      message = '\U000026A0 *추가하던 스케줄을 찾을 수 없습니다.*\n'\
              + '일시적 오류일 수 있으니 처음부터 다시 진행해주세요.\n'\
              + '오류가 지속되는 경우 @TeslaAuroraCS 로 문의해주세요.'
      keyboard = [['\U0001F519 돌아가기']]

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

      return SENTRY_BACK

    if sql.modifySchedule(update.message.chat_id, _veh_id, [_column], [_timestamp]):
      # Message
      message = '*스케줄이 동작할 유형을 선택하세요.*\n설정한 요일과 시간에 감시모드를 켜거나 끕니다.'
      keyboard = [['감시모드 켜기 설정', '감시모드 끄기 설정'], ['\U0001F519 등록 취소']]

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

      return SENTRY_ADD_ONOFF

    else: return Sentry_.addOnOff(update, context)

  def addOnOff_invalid(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    # Message
    message = '\U000026A0 *입력 형식에 맞지 않습니다.*\n아래 버튼을 눌러서 설정해주세요.'
    update.message.reply_text(message, parse_mode = 'Markdown')

    message = '*스케줄이 동작할 유형을 선택하세요.*'
    keyboard = [['감시모드 켜기 설정', '감시모드 끄기 설정'], ['\U0001F519 등록 취소']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return SENTRY_ADD_ONOFF

  def addDone(self, update, context):
    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]
    _column, _timestamp = Sentry_.findValue(update.message.chat_id, _veh_id, 'ONOFF')
    if update.message.text == '감시모드 켜기 설정': _timestamp += '1'
    elif update.message.text == '감시모드 끄기 설정': _timestamp += '0'

    if _column == 'NOT_FOUND':
      # Logging Conversation
      convLog(update, convLogger)

      # Message
      message = '\U000026A0 *추가하던 스케줄을 찾을 수 없습니다.*\n'\
              + '서버의 누락이 있었을 수도 있습니다.\n처음부터 다시 진행해주세요.'
      keyboard = [['\U0001F519 돌아가기']]

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

      return SENTRY_BACK

    if sql.modifySchedule(update.message.chat_id, _veh_id, [_column], [_timestamp]):
      # Message
      message = '\U0001F31F *스케줄 등록이 완료되었습니다.*'
      update.message.reply_text(message, reply_markup = ReplyKeyboardRemove(), parse_mode = 'Markdown')

      return Sentry_.menu(update, context)
    
    else: return Sentry_.addDone(update, context)

  def addCancel_1(self, update, context):
    # Message
    message = '*스케줄 등록이 취소되었습니다.*'
    update.callback_query.message.edit_text(message, parse_mode = 'Markdown')

    return Sentry_.menu(update, context, True)

  def addCancel_2(self, update, context):
    # Message
    message = '*스케줄 등록이 취소되었습니다.*'
    update.message.reply_text(message, parse_mode = 'Markdown')

    return Sentry_.menu(update, context, True)

  # SENTRY: Delete Schedule
  def delKeyboardMarkup(self, chat_id, veh_id):
    columns = ['sentry_switch_1',
              'sentry_switch_2',
              'sentry_switch_3',
              'sentry_switch_4',
              'sentry_switch_5']
    keyboard, k = [], 0
    keyboard.append([])
    
    # Markup Keyboard
    try:
      lists = sql.inquirySchedule(chat_id, veh_id, columns)

      for i, j in enumerate(lists):
        if j:
          if len(j) == 12:
            if len(keyboard[k]) == 2:
              keyboard.append([])
              k += 1
            j = '#' + str(i+1) + ' ' + DayOfWeek[j[:7]] + ' ' + j[7:9] + ':' + j[9:11]
            keyboard[k].append(j)

      keyboard += [['\U0001F519 돌아가기']]
      return keyboard

    except:
      keyboard = [['\U0001F519 돌아가기']]
      return keyboard

  def delSelect(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]

    # Message
    message = '*삭제할 스케줄을 선택하세요.*\n삭제된 스케줄은 복구할 수 없습니다.'
    keyboard = Sentry_.delKeyboardMarkup(update.message.chat_id, _veh_id)

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return SENTRY_DELETE

  def delDone(self, update, context):
    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]
    _column = 'sentry_switch_' + update.message.text[1:2]
    
    if sql.modifySchedule(update.message.chat_id, _veh_id, [_column], [None]):
      # Message
      message = '\U0001F31F *스케줄이 삭제되었습니다.*'
      update.message.reply_text(message, reply_markup = ReplyKeyboardRemove(), parse_mode = 'Markdown')

      return Sentry_.menu(update, context)
    
    else:
      # Logging Conversation
      convLog(update, convLogger)

      # Message
      message = '\U000026A0 *삭제하던 스케줄을 찾을 수 없습니다.*\n'\
              + '처음부터 다시 진행해주세요.'
      keyboard = [['\U0001F519 돌아가기']]

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

      return SENTRY_BACK

  def del_invalid(self, update, context):
    # Message
    message = '\U000026A0 *입력된 스케줄을 찾을 수 없습니다.*\n'\
            + '임의의 텍스트를 입력할 수 없어요:(\n'\
            + '아래 버튼에 표시되는 등록된 스케줄을 선택하여 해당 스케줄을 삭제할 수 있습니다.'
    update.message.reply_text(message, parse_mode = 'Markdown')

    return Sentry_.delSelect(update, context)


# Prevent Goto Sleep
class PreventSleep:
  def __init__(self) -> None:
    self.editable_msg = []

  def menu(self, update, context, rtn = False):
    if not rtn:
      # Logging Conversation
      convLog(update, convLogger)

    # Message
    message = '절전 방지 스케줄링 메뉴에요\U0001F636'
    keyboard = [['스케줄 추가', '스케줄 삭제']]
    keyboard += [['\U0001F3F7 도움말', '\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.effective_message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return PREVENT_MENU

  def help(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    # Message
    message = '\U0001F9D0 *절전 방지 스케줄링이란?*\n'\
            + '12V 배터리 방전 방지 및 딥 슬립 방지 등을 위해 '\
            + '매일 자동으로 차량을 온라인 상태로 유지시켜 주는 스케줄링 기능입니다. '\
            + '(예시 : 매일 06시에 1시간동안 온라인 상태 유지)\n'\
            + '유지 시간을 0시간으로 설정하면 차량을 한 번만 깨우고, 24시간으로 설정하면 매일 항시 온라인 상태를 유지하게끔 합니다.\n'\
            + '스케줄은 차량별로 최대 2개까지 등록할 수 있으며, 스케줄 실행 시간이 중복되는 경우 나중에 실행되는 스케줄은 실행되지 않습니다.\n'\
            + '차량이 2대 이상인 경우 현재 설정된 차량에 대해 스케줄이 설정됩니다.\n'\
            + '한 번 등록한 스케줄을 변경하려면 직접 삭제하고 다시 등록하여야 합니다.'
    keyboard = [['\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return PREVENT_BACK

  # Prevent - ADD
  def findValue(self, chat_id, veh_id, type):
    columns = ['prevent_sleep_1', 'prevent_sleep_2']
    lists = sql.inquirySchedule(chat_id, veh_id, columns)

    if not lists:
      sql.modifySchedule(chat_id, veh_id, ['prevent_sleep_1'], [None])

    if type == 'DAY':
      for i, j in enumerate(lists):
        if j:
          if not len(j) == 13:
            return columns[i]
      
      for i, j in enumerate(lists):
        if not j:
          return columns[i]
      
      return 'FULL'
    
    for i, j in enumerate(lists):
      if type == 'TIME':
        if j:
          if len(j) == 7: return columns[i], j

      if type == 'REMAIN':
        if j:
          if len(j) == 11: return columns[i], j
    
    return 'NOT_FOUND', '0'

  def addDay(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    # Message
    message = '*스케줄을 설정할 요일을 입력하세요.*\n입력 형식 : 일~토 중에 1~7글자\n입력 예시 : 일, 월수금, 일월화수목금토 등'
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('설정 취소', callback_data = 'CANCEL')]])

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        self.editable_msg.remove(i)
        break

    self.editable_msg.append([
      update.message.chat_id, message,
      update.message.reply_text(message, reply_markup = markup, parse_mode = 'Markdown')
    ])
    
    return PREVENT_ADD_DAY

  def addDay_invalid(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        i[2].edit_text(text = i[1], reply_markup = InlineKeyboardMarkup([[]]), parse_mode = 'Markdown')
        break
    
    # Message
    message = '\U000026A0 *입력 형식에 맞지 않습니다.*\n입력 형식 : 일~토 중에 1~7글자\n입력 예시 : 일, 월수금, 일월화수목금토 등'
    update.message.reply_text(message, parse_mode = 'Markdown')

    message = '*스케줄을 설정할 요일을 입력하세요.*'
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('설정 취소', callback_data = 'CANCEL')]])
    
    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        self.editable_msg.remove(i)
        break

    self.editable_msg.append([
      update.message.chat_id, message,
      update.message.reply_text(message, reply_markup = markup, parse_mode = 'Markdown')
    ])

    return PREVENT_ADD_DAY

  def addTime(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    def _createTimestamp():
      _timestamp_list, _timestamp = [0 for _ in range(7)], ''

      if '월' in update.message.text: _timestamp_list[0] = 1
      if '화' in update.message.text: _timestamp_list[1] = 1
      if '수' in update.message.text: _timestamp_list[2] = 1
      if '목' in update.message.text: _timestamp_list[3] = 1
      if '금' in update.message.text: _timestamp_list[4] = 1
      if '토' in update.message.text: _timestamp_list[5] = 1
      if '일' in update.message.text: _timestamp_list[6] = 1
      for i in _timestamp_list: _timestamp += str(i)
      
      return _timestamp

    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]
    _column = PreventSleep_.findValue(update.message.chat_id, _veh_id, 'DAY')
    _timestamp = _createTimestamp()

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        i[2].edit_text(text = i[1], reply_markup = InlineKeyboardMarkup([[]]), parse_mode = 'Markdown')
        break
    
    if _column == 'FULL':
      # Message
      message = '\U000026A0 *더 이상 스케줄을 추가할 수 없습니다.*\n'\
              + '절전 방지 스케줄은 2개까지 저장할 수 있으며, 스케줄을 변경하시려면 기존 스케줄을 삭제한 후 새로 추가하여야 합니다.'
      keyboard = [['\U0001F519 돌아가기']]

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

      return PREVENT_BACK

    if sql.modifySchedule(update.message.chat_id, _veh_id, [_column], [_timestamp]):
      # Message
      message = '*스케줄이 시작될 시간을 입력하세요.*\n입력 형식 : 4자리 시간 형식(HHMM)\n입력 예시 : 0600, 1530, 2300 등'
      markup = InlineKeyboardMarkup([[InlineKeyboardButton('설정 취소', callback_data = 'CANCEL')]])
      
      for i in self.editable_msg:
        if i[0] == update.message.chat_id:
          self.editable_msg.remove(i)
          break

      self.editable_msg.append([
        update.message.chat_id, message,
        update.message.reply_text(message, reply_markup = markup, parse_mode = 'Markdown')
      ])

      return PREVENT_ADD_TIME

    else: return PreventSleep_.addTime(update, context)

  def addTime_invalid(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        i[2].edit_text(text = i[1], reply_markup = InlineKeyboardMarkup([[]]), parse_mode = 'Markdown')
        break
    
    # Message
    message = '\U000026A0 *입력 형식에 맞지 않습니다.*\n입력 형식 : 4자리 시간 형식(HHMM)\n입력 예시 : 0600, 1530, 2300 등'
    update.message.reply_text(message, reply_markup = ReplyKeyboardRemove(), parse_mode = 'Markdown')

    message = '*스케줄이 시작될 시간을 입력하세요.*'
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('설정 취소', callback_data = 'CANCEL')]])
    
    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        self.editable_msg.remove(i)
        break

    self.editable_msg.append([
      update.message.chat_id, message,
      update.message.reply_text(message, reply_markup = markup, parse_mode = 'Markdown')
    ])

    return PREVENT_ADD_TIME

  def addRemain(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)
    
    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]
    _column, _timestamp = PreventSleep_.findValue(update.message.chat_id, _veh_id, 'TIME')
    _timestamp += str(update.message.text)

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        i[2].edit_text(text = i[1], reply_markup = InlineKeyboardMarkup([[]]), parse_mode = 'Markdown')
        break
    
    if _column == 'NOT_FOUND':
      # Message
      message = '\U000026A0 *추가하던 스케줄을 찾을 수 없습니다.*\n'\
              + '서버의 누락이 있었을 수도 있습니다.\n처음부터 다시 진행해주세요.'
      keyboard = [['\U0001F519 돌아가기']]

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

      return PREVENT_BACK

    if sql.modifySchedule(update.message.chat_id, _veh_id, [_column], [_timestamp]):
      # Message
      message = '*스케줄이 유지될 시간을 입력하세요.*\n입력 형식 : 0 ~ 24(시간)\n입력 예시 : 0, 1, 6, 12, 24 등'
      markup = InlineKeyboardMarkup([[InlineKeyboardButton('설정 취소', callback_data = 'CANCEL')]])

      for i in self.editable_msg:
        if i[0] == update.message.chat_id:
          self.editable_msg.remove(i)
          break

      self.editable_msg.append([
        update.message.chat_id, message,
        update.message.reply_text(message, reply_markup = markup, parse_mode = 'Markdown')
      ])

      return PREVENT_ADD_REMAIN

    else: return PreventSleep_.addRemain(update, context)

  def addRemain_invalid(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        i[2].edit_text(text = i[1], reply_markup = InlineKeyboardMarkup([[]]), parse_mode = 'Markdown')
        break
    
    # Message
    message = '\U000026A0 *입력 형식에 맞지 않습니다.*\n입력 형식 : 0 ~ 24(시간)\n입력 예시 : 0, 1, 6, 12, 24 등'
    update.message.reply_text(message, parse_mode = 'Markdown')

    message = '*스케줄이 유지될 시간을 입력하세요.*'
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('설정 취소', callback_data = 'CANCEL')]])

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        self.editable_msg.remove(i)
        break

    self.editable_msg.append([
      update.message.chat_id, message,
      update.message.reply_text(message, reply_markup = markup, parse_mode = 'Markdown')
    ])

    return PREVENT_ADD_REMAIN

  def addDone(self, update, context):
    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]
    _column, _timestamp = PreventSleep_.findValue(update.message.chat_id, _veh_id, 'REMAIN')
    if int(update.message.text) in range(0, 10): _timestamp += '0' + str(int(update.message.text))
    else: _timestamp += str(update.message.text)

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        i[2].edit_text(text = i[1], reply_markup = InlineKeyboardMarkup([[]]), parse_mode = 'Markdown')
        break
    
    if _column == 'NOT_FOUND':
      # Logging Conversation
      convLog(update, convLogger)

      # Message
      message = '\U000026A0 *추가하던 스케줄을 찾을 수 없습니다.*\n'\
              + '서버의 누락이 있었을 수도 있습니다.\n처음부터 다시 진행해주세요.'
      keyboard = [['\U0001F519 돌아가기']]

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

      return PREVENT_BACK

    if sql.modifySchedule(update.message.chat_id, _veh_id, [_column], [_timestamp]):
      # Message
      message = '\U0001F31F *스케줄 등록이 완료되었습니다.*'
      update.message.reply_text(message, parse_mode = 'Markdown')

      return PreventSleep_.menu(update, context)
    
    else: return PreventSleep_.addDone(update, context)

  def addCancel(self, update, context):
    # Message
    message = '*스케줄 등록이 취소되었습니다.*'
    update.callback_query.message.edit_text(message, parse_mode = 'Markdown')
        
    return PreventSleep_.menu(update, context, True)

  # PREVENT: Delete Schedule
  def delKeyboardMarkup(self, chat_id, veh_id):
    columns = ['prevent_sleep_1', 'prevent_sleep_2']
    keyboard, k = [], 0
    keyboard.append([])
    
    # Markup Keyboard
    try:
      lists = sql.inquirySchedule(chat_id, veh_id, columns)

      for i, j in enumerate(lists):
        if j:
          if len(j) == 13:
            if len(keyboard[k]) == 1:
              keyboard.append([])
              k += 1
            if int(j[11:]) == 0: j = '#' + str(i+1) + ' ' + DayOfWeek[j[:7]] + ' ' + j[7:9] + ':' + j[9:11]
            else: j = '#' + str(i+1) + ' ' + DayOfWeek[j[:7]] + ' ' + j[7:9] + ':' + j[9:11] + '부터 ' + str(int(j[11:])) + '시간'
            keyboard[k].append(j)

      keyboard += [['\U0001F519 돌아가기']]
      return keyboard

    except:
      keyboard = [['\U0001F519 돌아가기']]
      return keyboard

  def delSelect(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]

    # Message
    message = '*삭제할 스케줄을 선택하세요.*\n삭제된 스케줄은 복구할 수 없습니다.'
    keyboard = PreventSleep_.delKeyboardMarkup(update.message.chat_id, _veh_id)

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return PREVENT_DELETE

  def delDone(self, update, context):
    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]
    _column = 'prevent_sleep_' + update.message.text[1:2]
    
    if sql.modifySchedule(update.message.chat_id, _veh_id, [_column], [None]):
      # Message
      message = '\U0001F31F *스케줄이 삭제되었습니다.*'
      update.message.reply_text(message, reply_markup = ReplyKeyboardRemove(), parse_mode = 'Markdown')

      return PreventSleep_.menu(update, context)
    
    else:
      # Logging Conversation
      convLog(update, convLogger)

      # Message
      message = '\U000026A0 *삭제하던 스케줄을 찾을 수 없습니다.*\n'\
              + '처음부터 다시 진행해주세요.'
      keyboard = [['\U0001F519 돌아가기']]

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

      return PREVENT_BACK

  def del_invalid(self, update, context):
    # Message
    message = '\U000026A0 *입력된 스케줄을 찾을 수 없습니다.*\n'\
            + '임의의 텍스트를 입력할 수 없어요:(\n'\
            + '아래 버튼에 표시되는 등록된 스케줄을 선택하여 해당 스케줄을 삭제할 수 있습니다.'
    update.message.reply_text(message, parse_mode = 'Markdown')

    return PreventSleep_.delSelect(update, context)


# PreConditioning
class PreConditioning:
  def __init__(self) -> None:
    self.editable_msg = []

  def menu(self, update, context, rtn = False):
    if not rtn:
      # Logging Conversation
      convLog(update, convLogger)

    # Message
    message = '프리컨디셔닝 자동화 메뉴에요\U0001F636'
    keyboard = [['스케줄 추가', '스케줄 삭제']]
    keyboard += [['\U0001F3F7 도움말', '\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.effective_message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return PRECON_MENU

  def help(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    # Message
    message = '\U0001F9D0 *프리컨디셔닝 자동화란?*\n'\
            + '설정한 시간에 미리 배터리와 차량의 실내를 예열시켜 주어 겨울철 빠른 출발을 돕습니다.\n'\
            + '설정한 유지 시간의 절반은 HI 온도로 빠르게 차량 내부를 데우고, 이후의 절반은 기존 설정한 공조기 온도로 복귀하여 프리컨디셔닝을 지속합니다.\n'\
            + '유지 시간이 경과할 때까지 차량에 탑승하지 않으면 시간이 완전히 경과한 이후 공조기가 꺼집니다.\n'\
            + '스케줄은 차량별로 최대 5개까지 등록할 수 있으며, 스케줄 실행 시간이 중복되는 경우 나중에 실행되는 스케줄은 실행되지 않습니다.\n'\
            + '차량이 2대 이상인 경우 현재 설정된 차량에 대해 스케줄이 설정됩니다.\n'\
            + '한 번 등록한 스케줄을 변경하려면 직접 삭제하고 다시 등록하여야 합니다.'
    keyboard = [['\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return PRECON_BACK

  # Preconditioning - ADD
  def findValue(self, chat_id, veh_id, type):
    columns = ['preconditioning_1', 'preconditioning_2', 'preconditioning_3', 'preconditioning_4', 'preconditioning_5']
    lists = sql.inquirySchedule(chat_id, veh_id, columns)

    if not lists:
      sql.modifySchedule(chat_id, veh_id, ['preconditioning_1'], [None])
      
    if type == 'DAY':
      for i, j in enumerate(lists):
        if j:
          if not len(j) == 13:
            return columns[i]
      
      for i, j in enumerate(lists):
        if not j:
          return columns[i]
      
      return 'FULL'
    
    for i, j in enumerate(lists):
      if type == 'TIME':
        if j:
          if len(j) == 7: return columns[i], j

      if type == 'REMAIN':
        if j:
          if len(j) == 11: return columns[i], j
    
    return 'NOT_FOUND', '0'

  def addDay(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    # Message
    message = '*스케줄을 설정할 요일을 입력하세요.*\n입력 형식 : 일~토 중에 1~7글자\n입력 예시 : 일, 월수금, 일월화수목금토 등'
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('설정 취소', callback_data = 'CANCEL')]])

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        self.editable_msg.remove(i)
        break

    self.editable_msg.append([
      update.message.chat_id, message,
      update.message.reply_text(message, reply_markup = markup, parse_mode = 'Markdown')
    ])
    
    return PRECON_ADD_DAY

  def addDay_invalid(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        i[2].edit_text(text = i[1], reply_markup = InlineKeyboardMarkup([[]]), parse_mode = 'Markdown')
        break
    
    # Message
    message = '\U000026A0 *입력 형식에 맞지 않습니다.*\n입력 형식 : 일~토 중에 1~7글자\n입력 예시 : 일, 월수금, 일월화수목금토 등'
    update.message.reply_text(message, parse_mode = 'Markdown')

    message = '*스케줄을 설정할 요일을 입력하세요.*'
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('설정 취소', callback_data = 'CANCEL')]])
    
    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        self.editable_msg.remove(i)
        break

    self.editable_msg.append([
      update.message.chat_id, message,
      update.message.reply_text(message, reply_markup = markup, parse_mode = 'Markdown')
    ])

    return PRECON_ADD_DAY

  def addTime(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    def _createTimestamp():
      _timestamp_list, _timestamp = [0 for _ in range(7)], ''

      if '월' in update.message.text: _timestamp_list[0] = 1
      if '화' in update.message.text: _timestamp_list[1] = 1
      if '수' in update.message.text: _timestamp_list[2] = 1
      if '목' in update.message.text: _timestamp_list[3] = 1
      if '금' in update.message.text: _timestamp_list[4] = 1
      if '토' in update.message.text: _timestamp_list[5] = 1
      if '일' in update.message.text: _timestamp_list[6] = 1
      for i in _timestamp_list: _timestamp += str(i)
      
      return _timestamp

    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]
    _column = PreConditioning_.findValue(update.message.chat_id, _veh_id, 'DAY')
    _timestamp = _createTimestamp()

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        i[2].edit_text(text = i[1], reply_markup = InlineKeyboardMarkup([[]]), parse_mode = 'Markdown')
        break
    
    if _column == 'FULL':
      # Message
      message = '\U000026A0 *더 이상 스케줄을 추가할 수 없습니다.*\n'\
              + '프리컨디셔닝 스케줄은 5개까지 저장할 수 있으며, 스케줄을 변경하시려면 기존 스케줄을 삭제한 후 새로 추가하여야 합니다.'
      keyboard = [['\U0001F519 돌아가기']]

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

      return PRECON_BACK

    if sql.modifySchedule(update.message.chat_id, _veh_id, [_column], [_timestamp]):
      # Message
      message = '*스케줄이 시작될 시간을 입력하세요.*\n입력 형식 : 4자리 시간 형식(HHMM)\n입력 예시 : 0600, 1530, 2300 등'
      markup = InlineKeyboardMarkup([[InlineKeyboardButton('설정 취소', callback_data = 'CANCEL')]])
      
      for i in self.editable_msg:
        if i[0] == update.message.chat_id:
          self.editable_msg.remove(i)
          break

      self.editable_msg.append([
        update.message.chat_id, message,
        update.message.reply_text(message, reply_markup = markup, parse_mode = 'Markdown')
      ])

      return PRECON_ADD_TIME

    else: return PreConditioning_.addTime(update, context)

  def addTime_invalid(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        i[2].edit_text(text = i[1], reply_markup = InlineKeyboardMarkup([[]]), parse_mode = 'Markdown')
        break
    
    # Message
    message = '\U000026A0 *입력 형식에 맞지 않습니다.*\n입력 형식 : 4자리 시간 형식(HHMM)\n입력 예시 : 0600, 1530, 2300 등'
    update.message.reply_text(message, reply_markup = ReplyKeyboardRemove(), parse_mode = 'Markdown')

    message = '*스케줄이 시작될 시간을 입력하세요.*'
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('설정 취소', callback_data = 'CANCEL')]])
    
    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        self.editable_msg.remove(i)
        break

    self.editable_msg.append([
      update.message.chat_id, message,
      update.message.reply_text(message, reply_markup = markup, parse_mode = 'Markdown')
    ])

    return PRECON_ADD_TIME

  def addRemain(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)
    
    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]
    _column, _timestamp = PreConditioning_.findValue(update.message.chat_id, _veh_id, 'TIME')
    _timestamp += str(update.message.text)

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        i[2].edit_text(text = i[1], reply_markup = InlineKeyboardMarkup([[]]), parse_mode = 'Markdown')
        break
    
    if _column == 'NOT_FOUND':
      # Message
      message = '\U000026A0 *추가하던 스케줄을 찾을 수 없습니다.*\n'\
              + '서버의 누락이 있었을 수도 있습니다.\n처음부터 다시 진행해주세요.'
      keyboard = [['\U0001F519 돌아가기']]

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

      return PRECON_BACK

    if sql.modifySchedule(update.message.chat_id, _veh_id, [_column], [_timestamp]):
      # Message
      message = '*스케줄이 유지될 시간을 입력하세요.*\n입력 형식 : 10~60(분)\n입력 예시 : 10, 15, 30, 60 등'
      markup = InlineKeyboardMarkup([[InlineKeyboardButton('설정 취소', callback_data = 'CANCEL')]])

      for i in self.editable_msg:
        if i[0] == update.message.chat_id:
          self.editable_msg.remove(i)
          break

      self.editable_msg.append([
        update.message.chat_id, message,
        update.message.reply_text(message, reply_markup = markup, parse_mode = 'Markdown')
      ])

      return PRECON_ADD_REMAIN

    else: return PreConditioning_.addRemain(update, context)

  def addRemain_invalid(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        i[2].edit_text(text = i[1], reply_markup = InlineKeyboardMarkup([[]]), parse_mode = 'Markdown')
        break
    
    # Message
    message = '\U000026A0 *입력 형식에 맞지 않습니다.*\n입력 형식 : 10~60(분)\n입력 예시 : 10, 15, 30, 60 등'
    update.message.reply_text(message, parse_mode = 'Markdown')

    message = '*스케줄이 유지될 시간을 입력하세요.*'
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('설정 취소', callback_data = 'CANCEL')]])

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        self.editable_msg.remove(i)
        break

    self.editable_msg.append([
      update.message.chat_id, message,
      update.message.reply_text(message, reply_markup = markup, parse_mode = 'Markdown')
    ])

    return PRECON_ADD_REMAIN

  def addDone(self, update, context):
    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]
    _column, _timestamp = PreConditioning_.findValue(update.message.chat_id, _veh_id, 'REMAIN')
    if int(update.message.text) in range(0, 10): _timestamp += '0' + str(int(update.message.text))
    else: _timestamp += str(update.message.text)

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        i[2].edit_text(text = i[1], reply_markup = InlineKeyboardMarkup([[]]), parse_mode = 'Markdown')
        break
    
    if _column == 'NOT_FOUND':
      # Logging Conversation
      convLog(update, convLogger)

      # Message
      message = '\U000026A0 *추가하던 스케줄을 찾을 수 없습니다.*\n'\
              + '서버의 누락이 있었을 수도 있습니다.\n처음부터 다시 진행해주세요.'
      keyboard = [['\U0001F519 돌아가기']]

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

      return PRECON_BACK

    if sql.modifySchedule(update.message.chat_id, _veh_id, [_column], [_timestamp]):
      # Message
      message = '\U0001F31F *스케줄 등록이 완료되었습니다.*'
      update.message.reply_text(message, parse_mode = 'Markdown')

      return PreConditioning_.menu(update, context)
    
    else: return PreConditioning_.addDone(update, context)

  def addCancel(self, update, context):
    # Message
    message = '*스케줄 등록이 취소되었습니다.*'
    update.callback_query.message.edit_text(message, parse_mode = 'Markdown')
        
    return PreConditioning_.menu(update, context, True)

  # PREVENT: Delete Schedule
  def delKeyboardMarkup(self, chat_id, veh_id):
    columns = ['preconditioning_1', 'preconditioning_2', 'preconditioning_3', 'preconditioning_4', 'preconditioning_5']
    keyboard, k = [], 0
    keyboard.append([])
    
    # Markup Keyboard
    try:
      lists = sql.inquirySchedule(chat_id, veh_id, columns)

      for i, j in enumerate(lists):
        if j:
          if len(j) == 13:
            if len(keyboard[k]) == 1:
              keyboard.append([])
              k += 1
            j = '#' + str(i+1) + ' ' + DayOfWeek[j[:7]] + ' ' + j[7:9] + ':' + j[9:11] + '부터 ' + str(int(j[11:])) + '분'
            keyboard[k].append(j)

      keyboard += [['\U0001F519 돌아가기']]
      return keyboard

    except:
      keyboard = [['\U0001F519 돌아가기']]
      return keyboard

  def delSelect(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]

    # Message
    message = '*삭제할 스케줄을 선택하세요.*\n삭제된 스케줄은 복구할 수 없습니다.'
    keyboard = PreConditioning_.delKeyboardMarkup(update.message.chat_id, _veh_id)

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return PRECON_DELETE

  def delDone(self, update, context):
    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]
    _column = 'preconditioning_' + update.message.text[1:2]
    
    if sql.modifySchedule(update.message.chat_id, _veh_id, [_column], [None]):
      # Message
      message = '\U0001F31F *스케줄이 삭제되었습니다.*'
      update.message.reply_text(message, reply_markup = ReplyKeyboardRemove(), parse_mode = 'Markdown')

      return PreConditioning_.menu(update, context)
    
    else:
      # Logging Conversation
      convLog(update, convLogger)

      # Message
      message = '\U000026A0 *삭제하던 스케줄을 찾을 수 없습니다.*\n'\
              + '처음부터 다시 진행해주세요.'
      keyboard = [['\U0001F519 돌아가기']]

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

      return PRECON_BACK

  def del_invalid(self, update, context):
    # Message
    message = '\U000026A0 *입력된 스케줄을 찾을 수 없습니다.*\n'\
            + '임의의 텍스트를 입력할 수 없어요:(\n'\
            + '아래 버튼에 표시되는 등록된 스케줄을 선택하여 해당 스케줄을 삭제할 수 있습니다.'
    update.message.reply_text(message, parse_mode = 'Markdown')

    return PreConditioning_.delSelect(update, context)

# Charge Stop
class ChargeStop:
  def __init__(self) -> None:
    self.editable_msg = []

  def menu(slef, update, context):
    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]
    try:
      _value = sql.inquirySchedule(update.message.chat_id, _veh_id, ['chrg_stop_1'])[0]
    except TypeError:
      sql.modifySchedule(update.message.chat_id, _veh_id, ['chrg_stop_1'], [None])
      return ChargeStop_.menu(update, context)

    if _value: return ChargeStop_.delConfirm(update, context, _value)
    else: return ChargeStop_.addTime(update, context)

  # CHRGSTOP: Add Schedule
  def addTime(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    # Message
    message = '\U0001F9D0 *충전 종료 시간 설정이란?*\n'\
            + '목표 충전량과 관계 없이 설정한 시간에 자동으로 충전을 중지해주어 불필요한 과충전을 방지할 수 있습니다.\n'\
            + '매일 설정한 시간에 충전이 중지되고 사용자에게 알림을 보내줍니다.\n'
    update.message.reply_text(message, parse_mode = 'Markdown')
    
    message = '*충전이 종료될 시간을 입력하세요.*\n입력 형식 : 4자리 시간 형식(HHMM)\n입력 예시 : 0600, 1530, 2300 등'
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('설정 취소', callback_data = 'CANCEL')]])

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        self.editable_msg.remove(i)
        break

    self.editable_msg.append([
      update.message.chat_id, message,
      update.message.reply_text(message, reply_markup = markup, parse_mode = 'Markdown')
    ])
    
    return CHRGSTOP_ADD_TIME

  def addTime_invalid(self, update, context):
    # Logging Conversation
    convLog(update, convLogger)

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        i[2].edit_text(text = i[1], reply_markup = InlineKeyboardMarkup([[]]), parse_mode = 'Markdown')
        break
    
    # Message
    message = '\U000026A0 *입력 형식에 맞지 않습니다.*\n입력 형식 : 4자리 시간 형식(HHMM)\n입력 예시 : 0600, 1530, 2300 등'
    update.message.reply_text(message, reply_markup = ReplyKeyboardRemove(), parse_mode = 'Markdown')

    message = '*충전이 종료될 시간을 입력하세요.*'
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('설정 취소', callback_data = 'CANCEL')]])
    
    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        self.editable_msg.remove(i)
        break

    self.editable_msg.append([
      update.message.chat_id, message,
      update.message.reply_text(message, reply_markup = markup, parse_mode = 'Markdown')
    ])

    return CHRGSTOP_ADD_TIME

  def addDone(self, update, context):
    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]

    for i in self.editable_msg:
      if i[0] == update.message.chat_id:
        i[2].edit_text(text = i[1], reply_markup = InlineKeyboardMarkup([[]]), parse_mode = 'Markdown')
        break
    
    if sql.modifySchedule(update.message.chat_id, _veh_id, ['chrg_stop_1'], [update.message.text]):
      # Message
      message = '\U0001F31F *스케줄 등록이 완료되었습니다.*'
      update.message.reply_text(message, parse_mode = 'Markdown')

      return SCHEDL_Menu(update, context)
    
    else: return ChargeStop_.addDone(update, context)

  def addCancel(self, update, context):
    # Message
    message = '*스케줄 등록이 취소되었습니다.*'
    update.callback_query.message.edit_text(message, parse_mode = 'Markdown')
        
    return SCHEDL_Menu(update, context, True)

  # CHRGSTOP: Delete Schedule
  def delConfirm(self, update, context, value):
    # Logging Conversation
    convLog(update, convLogger)

    value = str(value[:2]) + ':' + str(value[2:])

    # Message
    message = '*{}에 등록된 스케줄을 삭제할까요?*\n충전 종료 시간 설정은 1건만 가능합니다.\n삭제된 스케줄은 복구할 수 없습니다.'.format(value)
    keyboard = [['스케줄 삭제'], ['\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return CHRGSTOP_DELETE

  def delDone(self, update, context):
    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]
    
    if sql.modifySchedule(update.message.chat_id, _veh_id, ['chrg_stop_1'], [None]):
      # Message
      message = '\U0001F31F *스케줄이 삭제되었습니다.*'
      update.message.reply_text(message, reply_markup = ReplyKeyboardRemove(), parse_mode = 'Markdown')

      return SCHEDL_Menu(update, context)
    
    else: return ChargeStop_.delDone(update, context)


# Nearby Charging Station
def NEAR_Start(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  return NEAR_Execution(update, context)

def NEAR_Execution(update, context):
  # Purpose to ReplyKeyboardRemove() & __getVehicle
  editable_msg = update.message.reply_text('*모듈을 로딩하고 있습니다...*', parse_mode = 'Markdown')
  
  # Vars
  _veh_id, editable_msg = __getVehicle(update, context, editable_msg)

  message = '\U0001F4AB *차량과 통신하고 있습니다...*'
  editable_msg.edit_text(message, parse_mode = 'Markdown')

  if _veh_id: _chargers = getNearbyChrgSites(update.message.chat_id, _veh_id)
  else:
    context.bot.deleteMessage(
      message_id = editable_msg.message_id, chat_id = update.message.chat_id)

    message = '\U000026A0 *차량에 연결할 수 없습니다.*\n잠시 후 다시 시도해보세요.'
    keyboard = [['\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return GOTO_MENU

  # Delete Loading Message
  context.bot.deleteMessage(
    message_id = editable_msg.message_id, chat_id = update.message.chat_id)
  
  if _chargers == 429:
    message = '\U000026A0 *정보를 가져올 수 없습니다.*\n너무 잦은 시도로 인해 서버 요청이 거부되었습니다. 잠시 후 다시 시도해보세요.'
    keyboard = [['\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return GOTO_MENU

  elif _chargers:
    superchargers = _chargers['superchargers']
    destinchargers = _chargers['destination_charging']

  else:
    message = '\U000026A0 *정보를 가져올 수 없습니다.*\n잠시 후 다시 시도해보세요.'
    keyboard = [['\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return GOTO_MENU

  try:
    # Message
    reply_markup = InlineKeyboardMarkup([])

    for i in superchargers:
      i['name'] = i['name'].replace(' - ', ' ')
      i['name'] = i['name'].replace('-', ' ')
      i['url_name'] = i['name'].replace(' ', '')

      if not i['site_closed']:
        reply_markup['inline_keyboard'].append([InlineKeyboardButton(
          text = i['name'] + '(' + str(i['available_stalls']) + '/' + str(i['total_stalls']) + ') ' + str(round(i['distance_miles']*1.609344, 1)) + 'km',
          url = 'https://apis.openapi.sk.com/tmap/app/routes?appKey=l7xx179f8d32ceeb4b608ce4e5f863684f1f&name='
              + i['url_name'] + '슈퍼차저&lon=' + str(i['location']['long']) + '&lat=' + str(i['location']['lat']))])
      
      else:
        reply_markup['inline_keyboard'].append([InlineKeyboardButton(
          text = i['name'] + '  \U000026A0 이용 불가',
          url = 'https://apis.openapi.sk.com/tmap/app/routes?appKey=l7xx179f8d32ceeb4b608ce4e5f863684f1f&name='
              + i['url_name'] + '슈퍼차저&lon=' + str(i['location']['long']) + '&lat=' + str(i['location']['lat']))])

    update.message.reply_text('*슈퍼차저 정보를 알려드려요!*\n버튼을 클릭하면 TMAP으로 연결해요.', reply_markup = reply_markup, parse_mode = 'Markdown')

    if len(destinchargers) > 0:
      message = '\n<b>데스티네이션차저 정보도 알려드릴게요:)</b>\n'
      for i in destinchargers:
        i['url_name'] = i['name'].replace(' ', '')

        message += '\U0001F38D<a href="https://apis.openapi.sk.com/tmap/app/routes?appKey=l7xx179f8d32ceeb4b608ce4e5f863684f1f&name='
        message += i['url_name'] + '&lon=' + str(i['location']['long']) + '&lat=' + str(i['location']['lat']) + '">' + i['name'] + '</a> '
        message += str(round(i['distance_miles']*1.609344, 1)) + 'km\n'
    
    else:
      message = '\n<b>데스티네이션차저는 근처에 없어요:(</b>\n'

    keyboard = [['\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'HTML')

    return GOTO_MENU

  except:
    # Message
    message = '\U000026A0 *정보를 가져올 수 없습니다.*\n잠시 후 다시 시도해보세요.'
    keyboard = [['\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return GOTO_MENU

# Find Location of Vehicle
def FIND_Location(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  message = '\U0001F4AB *데이터를 가져오고 있습니다...*'
  editable_msg = update.message.reply_text(message, parse_mode = 'Markdown')

  try:
    _veh_id = sql.inquiryAccount(update.message.chat_id, ['default_vehicle'])[0]
    _coord = sql.inquiryVehicle(update.message.chat_id, _veh_id, ['longitude', 'latitude'])

    url = 'https://apis.openapi.sk.com/tmap/staticMap?version=1&'\
        + 'appKey=l7xx179f8d32ceeb4b608ce4e5f863684f1f&coordType=WGS84GEO&width=512&height=512&zoom=17&format=PNG&'\
        + 'longitude={}&latitude={}&markers={}'.format(str(_coord[0]), str(_coord[1]), str(_coord[0]) + ',' + str(_coord[1]))
    keyboard = [['\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_photo(url, reply_markup = reply_markup)

    message = '*내 차의 최근 위치입니다.*\n위치 정보는 차량이 온라인일 때 갱신되므로 정확하지 않을 수 있습니다.'
    editable_msg.edit_text(message, parse_mode = 'Markdown')

    return GOTO_MENU

  except Exception as e:
    errorLogger.error(e, exc_info = False)

    context.bot.deleteMessage(
    message_id = editable_msg.message_id, chat_id = update.message.chat_id)

    message = '\U000026A0 *위치 정보를 가져올 수 없습니다.*\n새로 가입한 시점에는 서버에 차량 정보를 가져오는 데 시간이 소요됩니다. 잠시 후 다시 시도해보세요.'
    keyboard = [['\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return GOTO_MENU


# Account & Vehicle Setting
def SETT_KeyboardMarkup_vehicles(update, context):
  # Vehicles Vars
  keyboard, h = [], 0
  keyboard.append([])

  # Markup Keyboard
  try:
    for i in sql.inquiryVehicle(update.message.chat_id, None, ['vehicle_name']):
      if len(keyboard[h]) == 2:
        keyboard.append([])
        h += 1
      keyboard[h].append(i[0])
    return keyboard

  except:
    keyboard = [['\U0001F519 돌아가기']]
    return keyboard

def SETT_Menu(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '이용하실 메뉴를 선택해주세요\U0001F636'
  keyboard = [['내 차 정보', '테슬라 토큰 갱신'], ['계정 정보 변경', '자주 사용하는 차량 변경'], ['\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return SETTING_MENU


def SETT_VehicleInfo(update, context):
  # Logging Conversation
  convLog(update, convLogger)
  
  tuples = sql.inquiryVehicle(update.message.chat_id, None, ['vehicle_name', 'car_type', 'trim_badging', 'exterior_color', 'wheel_type', 'car_version', 'odometer', 'battery_range'])
  
  for i in tuples:
    if None in i[:7]:
      # Message
      message = '\U000026A0 *아직 차량 정보가 서버에 없습니다.*\n서비스 가입 직후인 경우 데이터 수집에 어느 정도 시간이 소요됩니다.\n잠시 후 다시 시도해보세요.'
      keyboard = [['\U0001F519 돌아가기']]

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')
    
      return SETTING_BACK

    # Message
    message = '*{}의 차량 정보입니다\U0001F619*\n\U0001F9E4 *차종* : {} {}\n'.format(i[0], car_type[i[1]], trim_badging[i[2]])\
            + '\U0001F9E4 *컬러* : {}\n\U0001F9E4 *휠* : {}\n'.format(exterior_color[i[3]], wheel_type[i[4]])\
            + '\U0001F9E4 *소프트웨어* : {}\n\U0001F9E4 *누적 주행거리* : {}km\n'.format(i[5], str(i[6]))
    if i[7]: message += '\U0001F9E4 *주행 가능거리* : {}km\n  \* 최근 배터리 완전 충전 시 계산된 수치입니다.'.format(str(i[7]))
    keyboard = [['\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return SETTING_BACK


def SETT_GetToken(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '*Tesla 계정과 연결하는 토큰을 갱신합니다.*\n'\
          + '토큰 갱신과 동시에 연동된 차량을 새로 불러올거에요! Tesla 계정에서 삭제된 차량은 오로라에서도 삭제되고, Tesla 계정에 추가된 차량은 오로라에서도 추가되어요.\n'\
          + '토큰은 종단 간 암호화되어 있으므로 개발자를 비롯한 중간의 *그 누구도 회원님의 계정 정보를 알 수 없습니다.*'
  update.message.reply_text(message, parse_mode = 'Markdown', reply_markup = ReplyKeyboardRemove())

  message = '*토큰을 갱신하는 방법을 알려드릴게요!*\n'\
          + '\U00002714 토큰 발급 앱을 실행합니다. '\
          + '설치 바로가기: [iOS](https://apps.apple.com/kr/app/auth-app-for-tesla/id1552058613) 또는 '\
          + '[Android](https://play.google.com/store/apps/details?id=net.leveugle.teslatokens)\n'\
          + '\U00002714 앱에서 Tesla 계정으로 로그인하고, Refresh Token의 값을 복사하세요.\n'\
          + '\U00002714 복사한 값을 정확히 아래에 붙혀 넣으면 됩니다.'
  update.message.reply_text(message, parse_mode = 'Markdown', disable_web_page_preview = True)

  message = '*Refresh Token을 입력해주세요.*\n갱신을 취소하려면 \'취소\'를 입력하세요.'
  update.message.reply_text(message, parse_mode = 'Markdown')

  return SETTING_TOKEN

def SETT_VerifyToken(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Delete User Message
  #update.message.delete()

  # Message
  message = '\U0001F4AB *토큰을 검증하고 있습니다...*\n'
  #message += '입력하신 메시지는 보안을 위해 저희가 삭제했습니다:)'
  editable_msg = update.message.reply_text(message, parse_mode = 'Markdown')

  # Verify Refresh Token & Get Access Token
  access_t = Token(update.message.chat_id).generate(update.message.text)

  # Succeeded Verify Token
  if access_t:
    if Token(update.message.chat_id).verify(access_t):
      # Message
      message = '\U0001F44F *토큰 검증을 성공했습니다!*\n'
      editable_msg.edit_text(message, parse_mode = 'Markdown')

      message = '\U0001F4AB *등록된 차량 목록을 가져오는 중입니다...*'
      editable_msg = update.message.reply_text(message, parse_mode = 'Markdown')
            
      '''
      if vehicle_cnts > 2:
        # Message
        message = '\U000026A0 *이런, 차량을 3대 이상 보유하고 계시군요.*\n'\
                + '3대 이상의 차량이 있는 Tesla 계정으로는 가입이 제한돼요:(\n'\
                + '서버 안정화를 위한 조치로, 더 많은 이용자가 쾌적하게 사용할 수 있게 하기 위함임을 양해해주셨으면 좋겠습니다\U0001F622\n'\
                + '새로운 Tesla 계정을 만들어 \'다른 운전자 추가\' 기능을 이용하신다면 서비스를 이용하실 수 있습니다.\n'\
                + '다음 기회에 다시 찾아뵙기를 희망합니다\U0001F3C3\n'\
                + '[테슬라 계정 생성 바로가기 링크](https://auth.tesla.com/oauth2/v1/register?redirect_uri=https%3A%2F%2Fwww.tesla.com%2Fteslaaccount%2Fowner-xp%2Fauth%2Fcallback&response_type=code&client_id=ownership&scope=offline_access+openid+ou_code+email&audience=https%3A%2F%2Fownership.tesla.com%2F&locale=ko-KR)'
                        
        editable_msg.edit_text(message, parse_mode = 'Markdown')
                
        return ConversationHandler.END
      '''

      vehicle_cnts = getVehCounts(update.message.chat_id, access_t)
      if sql.modifyAccount(update.message.chat_id, ['vehicle_counts'], [vehicle_cnts]):
        newerVeh = generateVehicles(update.message.chat_id, access_t)
        if newerVeh:
          existVeh = []
          try:
            for i in sql.inquiryVehicle(update.message.chat_id, None, ['vehicle_id']):
              existVeh.append(i[0])
          
          except:
            # Message
            message = '\U000026A0 *차량 목록을 가져오는 데에 실패했습니다.*\nERRCODE: MENU\_2267\n@TeslaAuroraCS 로 문의해주세요. '
            editable_msg.edit_text(message, parse_mode = 'Markdown')

            return ConversationHandler.END
          
          for i in existVeh:
            factor = 0
            for j in newerVeh:
              if i == j: factor = 1
            if factor == 0:
              try:
                sql.deleteVehicle(update.message.chat_id, i)

              except:
                # Message
                message = '\U000026A0 *차량 목록을 가져오는 데에 실패했습니다.*\nERRCODE: MENU\_2282\n@TeslaAuroraCS 로 문의해주세요.'
                editable_msg.edit_text(message, parse_mode = 'Markdown')

                return ConversationHandler.END

          message = '\U0001F44F *차량 목록을 가져왔습니다!*\n'
          editable_msg.edit_text(message, parse_mode = 'Markdown')

          # Write Privacy info.
          # Succeeded Write Token
          if sql.modifyAccount(update.message.chat_id, ['token_refresh', 'token_access'], [update.message.text, access_t]):
            if vehicle_cnts > 1:
              # Message
              message = '\U0001F607 *차량을 두 대 이상 보유하고 계시군요!*\n'\
                      + '보유한 차량 중에서 자주 사용하는 차량을 지정해야 합니다.\n'\
                      + '서비스 사용 시 차량 선택에 대한 절차를 간소화하기 위해 모든 기능은 설정된 자주 사용하는 차량에 대해 동작합니다.\n'\
                      + '자주 사용하는 차량은 한 대만 설정할 수 있으며, 계정 설정에서 언제든 변경할 수 있습니다:)\n'
              editable_msg.edit_text(message, parse_mode = 'Markdown')
              
              message = '*자주 사용하는 차량을 선택해주세요.*'
              keyboard = SETT_KeyboardMarkup_vehicles(update, context)
              
              reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
              update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

              return SETTING_DEFAULT_VEH
            
            else:
              message = '\U0001F4AB *데이터를 저장하고 있습니다...*'
              editable_msg = update.message.reply_text(message, parse_mode = 'Markdown')

              for _ in getVehCurrent(update.message.chat_id): vID = _['id']
              if sql.modifyAccount(update.message.chat_id, ['default_vehicle'], [vID]):
                # Message
                context.bot.deleteMessage(
                message_id = editable_msg.message_id, chat_id = update.message.chat_id)

                message = '\U0001F31F *정보 수정이 완료되었습니다.*'
                update.message.reply_text(message, parse_mode = 'Markdown')

                return SETT_Menu(update, context)

              # Failed modifyAccount()
              else:
                # Message
                message = '\U000026A0 *데이터 저장에 실패했습니다.*\nERRCODE: MENU\_2327\n@TeslaAuroraCS 로 문의해주세요.'
                update.message.reply_text(message, parse_mode = 'Markdown')
                            
                return ConversationHandler.END

          # Failed Write Token
          else:
            # Message
            message = '\U000026A0 *데이터 저장에 실패했습니다.*\nERRCODE: MENU\_2335\n@TeslaAuroraCS 로 문의해주세요.'
            update.message.reply_text(message, parse_mode = 'Markdown')
                        
            return ConversationHandler.END

        # Failed createVehID
        else:
          # Message
          message = '\U000026A0 *차량 목록을 가져오는 데에 실패했습니다.*\nERRCODE: MENU\_2343\n@TeslaAuroraCS 로 문의해주세요.'
          editable_msg.edit_text(message, parse_mode = 'Markdown')
                    
          return ConversationHandler.END

      # Failed modifyAccount | countVeh
      else:
        # Message
        message = '\U000026A0 *차량 목록을 가져오는 데에 실패했습니다.*\nERRCODE: MENU\_2351\n@TeslaAuroraCS 로 문의해주세요.'
        editable_msg.edit_text(message, parse_mode = 'Markdown')
                
        return ConversationHandler.END
        
    # Failed Verify Token
    else:
      # Message
      message = '\U000026A0 *Token이 정확하지 않거나 유효하지 않습니다.*\n'
      editable_msg.edit_text(message, parse_mode = 'Markdown')

      message = '보내드린 메시지의 링크에 있는 앱에서 토큰을 발급하길 권장드리며, Access Token이 아닌 Refresh Token을 입력하셔야 합니다\U0001F62C\n'\
              + '지속적으로 오류가 발생한다면 @TeslaAuroraCS 로 문의해주세요.'
      update.message.reply_text(message, parse_mode = 'Markdown')
                    
      message = '*Refresh Token을 입력해주세요.*\n갱신을 취소하려면 \'취소\'를 입력하세요.'
      update.message.reply_text(message, parse_mode = 'Markdown')
    
  # Failed Verify Token
  else:
    # Message
    message = '\U000026A0 *Token이 정확하지 않거나 유효하지 않습니다.*\n'
    editable_msg.edit_text(message, parse_mode = 'Markdown')

    message = '보내드린 메시지의 링크에 있는 앱에서 토큰을 발급하길 권장드리며, Access Token이 아닌 Refresh Token을 입력하셔야 합니다\U0001F62C\n'\
            + '지속적으로 오류가 발생한다면 @TeslaAuroraCS 로 문의해주세요.'
    update.message.reply_text(message, parse_mode = 'Markdown')
                
    message = '*Refresh Token을 입력해주세요.*\n갱신을 취소하려면 \'취소\'를 입력하세요.'
    update.message.reply_text(message, parse_mode = 'Markdown')

def SETT_VerifyVehicle(update, context):
  # Message
  message = '\U0001F4AB *차량을 확인하고 있습니다...*'
  editable_msg = update.message.reply_text(message, parse_mode = 'Markdown')
    
  # Verify Access Token
  if Token(update.message.chat_id).verify():
    # Vehicles Vars
    vID, vName = [], []

    # Logging Conversation
    convLog(update, convLogger)

    # Matching Vehicle(ID - DP_NAME)
    for i in getVehCurrent(update.message.chat_id):
      vID.insert(0, i['id'])
      vName.insert(0, i['display_name'])
      # [0]에 insert하면서 기존 데이터는 [1]로 옮겨짐
      
    # Verify Reply
    if update.message.text in vName:
      message = '\U0001F4AB *데이터를 저장하고 있습니다...*'
      editable_msg.edit_text(message, parse_mode = 'Markdown')

      _a = vID[vName.index(update.message.text)]
      if sql.modifyAccount(update.message.chat_id, ['default_vehicle'], [_a]):
        # Message
        context.bot.deleteMessage(
        message_id = editable_msg.message_id, chat_id = update.message.chat_id)

        message = '\U0001F31F *정보 수정이 완료되었습니다.*'
        update.message.reply_text(message, parse_mode = 'Markdown')

        return SETT_Menu(update, context)

      # Failed modifyAccount()
      else:
        # Message
        message = '\U000026A0 *데이터 저장에 실패했습니다.*\nERRCODE: MENU\_2420\n@TeslaAuroraCS 로 문의해주세요.'
        editable_msg.edit_text(message, parse_mode = 'Markdown')
        
        return ConversationHandler.END

    else: # Not Matched Vehicle(ID - DP_NAME)
      # Message
      #context.bot.deleteMessage(message_id = editable_msg.message_id, chat_id = update.message.chat_id)
      message = '\U000026A0 *차량을 찾을 수 없습니다.*\n임의의 텍스트를 입력할 수 없어요:(\n'\
              + '아래 버튼에 표시되는 차량 이름이 올바르지 않다면 @TeslaAuroraCS 로 문의해주세요.'
      editable_msg.edit_text(message, parse_mode = 'Markdown')

      message = '*차량을 선택해주세요.*'
      keyboard = SETT_KeyboardMarkup_vehicles(update, context)

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

      return SETTING_DEFAULT_VEH
      
  else: # Token Expired
    # Message
    message = '\U000026A0 *액세스 토큰이 만료되었습니다.*\n토큰을 자동으로 갱신하고 있어요\U0001F609\n잠시만 기다려주세요.'
    editable_msg.edit_text(message, parse_mode = 'Markdown')

    # Renewal Access Token
    if Token(update.message.chat_id).renewal() == 0:
      context.bot.deleteMessage(
        message_id = editable_msg.message_id, chat_id = update.message.chat_id)
      return SETT_VerifyVehicle(update, context)
    else:
      message = '\U000026A0 *토큰 갱신에 실패했습니다.*\n다시 한 번 시도해볼게요:(\n잠시만 기다려주세요.'
      editable_msg.edit_text(message, parse_mode = 'Markdown')

      # Renewal Access Token(1-More-Time)
      _a = Token(update.message.chat_id).renewal()
      if _a == 0:
        context.bot.deleteMessage(
          message_id = editable_msg.message_id, chat_id = update.message.chat_id)
        return SETT_VerifyVehicle(update, context)

      else:
        if _a == 1: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: MENU\_2462\n'
        elif _a == 2: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: MENU\_2463\n'
        elif _a == 3: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: MENU\_2464\n'
        elif _a == 4: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: MENU\_2465\n'
        elif _a == 5: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: MENU\_2466\n'
        elif _a == 6: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: MENU\_2467\n'
        elif _a == 7: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: MENU\_2468\n'
        elif _a == 8: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: MENU\_2469\n'
        else: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: MENU\_2470\n'

      message += '@TeslaAuroraCS 로 문의해주세요.'
      keyboard = [['\U0001F519 돌아가기']]

      context.bot.deleteMessage(
        message_id = editable_msg.message_id, chat_id = update.message.chat_id)

      # Logging Conversation
      convLog(update, convLogger)

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')
            
      return GOTO_MENU


def SETT_Account(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '이용하실 메뉴를 선택해주세요\U0001F636'
  keyboard = [['닉네임 바꾸기', '전화번호 바꾸기'], ['이메일 바꾸기', '서비스 탈퇴'], ['\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return SETTING_ACCOUNT

def SETT_ModifyName(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '*새로운 닉네임을 입력해주세요.*\n닉네임은 한글로 2~8자만 입력할 수 있습니다.'
  update.message.reply_text(message, parse_mode = 'Markdown', reply_markup = ReplyKeyboardRemove())

  return SETTING_MOD_NAME

def SETT_ModifyName_done(update, context):
  # Logging Conversation
  convLog(update, convLogger)
  
  return SETT_ProcessModify(update, context, 'nickname')

def SETT_ModifyName_invalid(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '\U000026A0 닉네임은 한글로 2~8자만 입력할 수 있어요\U0001F635\n*새로운 닉네임을 입력해주세요.*'
  update.message.reply_text(message, parse_mode = 'Markdown')

  return SETTING_MOD_NAME

def SETT_ModifyPhone(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '*새로운 전화번호를 입력해주세요.*\n전화번호는 대시(-)를 제외하고 입력해주세요.'
  update.message.reply_text(message, parse_mode = 'Markdown', reply_markup = ReplyKeyboardRemove())

  return SETTING_MOD_PHONE

def SETT_ModifyPhone_done(update, context):
  # Logging Conversation
  convLog(update, convLogger)
  
  return SETT_ProcessModify(update, context, 'phone')

def SETT_ModifyPhone_invalid(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '\U000026A0 전화번호는 숫자로만 입력할 수 있어요\U0001F622\n대시(-)를 제외하고 입력해주시길 부탁드려요:)\n*전화번호를 입력해주세요.*'
  update.message.reply_text(message, parse_mode = 'Markdown')

  return SETTING_MOD_PHONE

def SETT_ModifyEmail(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '*새로운 이메일 주소를 입력해주세요.*\nex. teslaaurora@naver.com'
  update.message.reply_text(message, parse_mode = 'Markdown', reply_markup = ReplyKeyboardRemove())

  return SETTING_MOD_EMAIL

def SETT_ModifyEmail_done(update, context):
  # Logging Conversation
  convLog(update, convLogger)
  
  return SETT_ProcessModify(update, context, 'email')

def SETT_ModifyEmail_invalid(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '\U000026A0 정확한 이메일 형식이 아니에요\U0001F627\n골뱅이와 도메인까지 입력해주셔야 해요:)\n*새로운 이메일 주소를 입력해주세요.*\nex. teslaaurora@naver.com'
  update.message.reply_text(message, parse_mode = 'Markdown')

  return SETTING_MOD_EMAIL

def SETT_ProcessModify(update, context, column):
  if sql.modifyAccount(update.message.chat_id, [column], [update.message.text]):
    # Message
    message = '\U0001F31F *정보 수정이 완료되었습니다.*'
    update.message.reply_text(message, parse_mode = 'Markdown')

    return SETT_Menu(update, context)
  
  else:
    # Message
    message = '\U000026A0 *정보 수정에 실패하였습니다.*\nERRCODE: MENU\_2588\n잠시 후 다시 시도하세요.'
    keyboard = [['\U0001F519 돌아가기']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
    update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

    return SETTING_BACK

def SETT_Withdrawal_Noti(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '*정말로 서비스를 탈퇴하시나요?*\n테슬라 오로라는 개인정보를 안전하게 보관하고 있으며, 서비스 제공 이외의 목적으로 절대 활용되지 않습니다.\n'\
          + '앞으로 다양한 기능들이 추가될 예정이며, 불편한 점이 있으셨다면 @TeslaAuroraCS 로 문의하실 수 있고, 개발자는 불편한 점의 빠른 개선을 위해 항상 적극적으로 노력하고 있습니다.\n'\
          + '그래도 서비스 탈퇴를 원하신다면, 아래 버튼을 눌러서 진행할 수 있으며 탈퇴 즉시 모든 개인정보와 차량 정보가 삭제됩니다.'
  keyboard = [['네, 탈퇴하겠습니다.'], ['\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return SETTING_WITHDRAWAL

def SETT_Withdrawal_Done(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  try:
    if sql.deleteAccount(update.message.chat_id):
      # Message
      message = '*서비스 탈퇴가 완료되었습니다.*\n그 동안 함께해주셔서 감사드립니다.'
      update.message.reply_text(message, reply_markup = ReplyKeyboardRemove(), parse_mode = 'Markdown')

      return ConversationHandler.END
  
  except:
    # Message
    message = '\U000026A0 *탈퇴 처리 중 오류가 발생했습니다.*\nERRCODE: MENU\_2625\n오류가 지속되는 경우 @TeslaAuroraCS 로 문의해주세요.'
    update.message.reply_text(message, reply_markup = ReplyKeyboardRemove(), parse_mode = 'Markdown')

    return ConversationHandler.END


def SETT_DefaultVehicle(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '*자주 사용하는 차량을 선택해주세요.*'
  keyboard = SETT_KeyboardMarkup_vehicles(update, context)
  keyboard += [['\U0001F519 돌아가기']]

  if len(keyboard[0]) == 1:
    # Message
    message = '\U000026A0 *한 대의 차량만 보유하고 있습니다.*\n'\
            + '자주 사용하는 차량은 2대 이상의 차량 중 한 대만을 선택하여 주 기능을 사용할 수 있는 차량을 설정하는 기능입니다.\n'\
            + '차량 목록을 갱신하려는 경우, \'테슬라 토큰 갱신\'을 통해 새로운 차량 정보를 가져올 수 있습니다.'
    keyboard = [['\U0001F519 돌아가기']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return SETTING_DEFAULT_VEH

# Enable Classes
Sentry_ = Sentry()
PreventSleep_ = PreventSleep()
PreConditioning_ = PreConditioning()
ChargeStop_ = ChargeStop()