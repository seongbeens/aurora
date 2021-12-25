# This works separately from app.py in background.
import telegram
import schedule
import threading
from datetime import datetime
from api import *


# Enable logging
logger = logging.getLogger('schedules')
logger.addHandler(SchedLogHandler)

# Telegram
bot = telegram.Bot(token = telegram_token)

# Common - Get Vehicles Configuration & Write into VEHICLES.CSV
# Running Every Hour.
def COMMON_GetVehiclesConfig_Schedule():
  logger.debug('VEHCONF: Schedule has been executed.')

  _ThreadName = 'GetVehiclesConfigSchedule'
  logger.info('Thread ' + _ThreadName + ' started.')
  threading.Thread(name = _ThreadName, target = COMMON_GetVehiclesConfig).start()

def COMMON_GetVehiclesConfig():
  def _getApi(_chat_id, _veh_id):
    if getVehCurrent(_chat_id, _veh_id) == 'online':
      logger.debug('VEHCONF: getVehCurrent(' + str(_chat_id) + ', ' + str(_veh_id) + ') == online')

      def _isNull(columns):
        for i in sql.inquiryVehicle(_chat_id, _veh_id, columns):
          if i is None: return True
        
        return False

      _columns = ['car_type', 'trim_badging', 'efficiency_package', 'exterior_color', 'wheel_type']

      if _isNull(_columns): # Vehicle Configuration
        _data = getVehicleConfig(_chat_id, _veh_id)
        if not _data: return

        logger.debug('VEHCONF: getVehicleConfig(' + str(_chat_id) + ', ' + str(_veh_id) + ') Received.')
        
        _tuples = [_data['car_type'], _data['trim_badging'], _data['efficiency_package'], _data['exterior_color'], _data['wheel_type']]

        if sql.modifyVehicle(_chat_id, _veh_id, _columns, _tuples):
          logger.debug('VEHCONF: modifyVehicle(' + str(_chat_id) + ', ' + str(_veh_id) + ') Successfully.')
        
        else: logger.warning('VEHCONF: modifyVehicle(' + str(_chat_id) + ', ' + str(_veh_id) + ') Failed.')
      
    else: 
      logger.debug('VEHCONF: getVehCurrent(' + str(_chat_id) + ', ' + str(_veh_id) + ') != online')

  for tuples in sql.inquiryVehicles():
    _ThreadName, _ThreadExist = 'VEHCONF' + str(tuples[0]) + str(tuples[1]), False

    for i in threading.enumerate():
      if str(i).split('(')[1].split(',')[0] == _ThreadName: _ThreadExist = True

    if not _ThreadExist:
      logger.debug('Thread ' + _ThreadName + ' started.')
      threading.Thread(name = _ThreadName, target = _getApi, args = (tuples[0], tuples[1])).start()
      time.sleep(1)

# Common - Get Vehicle State
# & Reminder - Charging Complete
# Running Every 2Min.
def COMMON_GetVehiclesState_Schedule():
  logger.debug('VEHSTAT: Schedule has been executed.')

  _ThreadName = 'GetVehiclesStateSchedule'
  logger.debug('Thread ' + _ThreadName + ' started.')
  threading.Thread(name = _ThreadName, target = COMMON_GetVehiclesState_Target).start()

def COMMON_GetVehiclesState_Target():
  for tuples in sql.inquiryVehicles(['vehicle_name', 'reminder_charge_complete']):
    _ThreadName, _ThreadExist = 'VEHSTAT' + str(tuples[0]) + str(tuples[1]), False

    for i in threading.enumerate():
      if str(i).split('(')[1].split(',')[0] == _ThreadName: _ThreadExist = True

    if not _ThreadExist:
      logger.debug('Thread ' + _ThreadName + ' started.')
      threading.Thread(name = _ThreadName, target = COMMON_GetVehiclesState, args = (tuples[0], tuples[1], tuples[2], tuples[3])).start()
      time.sleep(1)

def COMMON_GetVehiclesState(chat_id, veh_id, veh_name, _a):
  if getVehCurrent(chat_id, veh_id) == 'online':
    logger.debug('VEHSTAT: getVehCurrent(' + str(chat_id) + ', ' + str(veh_id) + ') == online')

    data = {'vehicle_state': '', 'drive_state': ''}
    data['vehicle_state'] = getVehicleState(chat_id, veh_id)
    data['charge_state'] = getChargeState(chat_id, veh_id)
    data['drive_state'] = getDriveState(chat_id, veh_id)

    # Collect Vehicle State
    __collect(chat_id, veh_id, data)

    # Reminder Charging Complete
    if _a == 1: __chrgCheck(chat_id, veh_id, veh_name, data['charge_state'])

    # Idle Mode
    if (not data['vehicle_state']['is_user_present']) & \
       (not data['vehicle_state']['sentry_mode']) & \
       (not data['charge_state']['charging_state'] == 'Charging'):
      logger.info(
        'VEHSTAT: Enter Idle mode. ({}, {})'
        .format(str(chat_id), str(veh_id)))
      time.sleep(900) # 15 min
      logger.debug(
        'VEHSTAT: Exit Idle mode. ({}, {})'
        .format(str(chat_id), str(veh_id)))

  else: 
    logger.debug(
      'VEHSTAT: getVehCurrent({}, {}) != online'
      .format(str(chat_id), str(veh_id)))

def __collect(chat_id, veh_id, data):
    columns = ['odometer', 'car_version', 'latitude', 'longitude']
    tuples = [round(data['vehicle_state']['odometer']*1.609344), data['vehicle_state']['car_version'].split()[0],
                data['drive_state']['latitude'], data['drive_state']['longitude']]

    # Update Vehicle Information
    if sql.modifyVehicle(chat_id, veh_id, columns, tuples):
      logger.debug('VEHSTAT: modifyVehicle(' + str(chat_id) + ', ' + str(veh_id) + ') Successfully.')
    
    else: logger.warning('VEHSTAT: modifyVehicle(' + str(chat_id) + ', ' + str(veh_id) + ') Failed.')

def __chrgCheck(chat_id, veh_id, veh_name, prev_data):
  # Variables
  data = prev_data
  msg_10min, msg_5min = False, False

  if data:
    if data['charging_state'] in ['Disconnected', 'NoPower', 'Stopped', 'Complete']: return
    existing_charge_limit_soc = data['charge_limit_soc']
  else: return

  # Notification of Start Charging
  if sql.inquiryVehicle(chat_id, veh_id, ['reminder_charge_start'])[0] == 1:
    if data['charging_state'] == 'Charging':
      bot.send_message(chat_id = chat_id,
        text = '\U0001F389 *' + str(veh_name) + '의 알림이에요!*\n' + str(data['battery_level']) + '%에서 충전이 시작되었습니다.\n'\
             + '충전 목표량은 *' + str(data['charge_limit_soc']) + '%*로 설정되어 있어요.', parse_mode = 'Markdown')
      logger.info('__chrgCheck: Start Charging. (' + str(chat_id) + ', ' + str(veh_id) + ')')

  # Notification of Charging Completion
  while True:
    if existing_charge_limit_soc != data['charge_limit_soc']:
      existing_charge_limit_soc, msg_10min, msg_5min = data['charge_limit_soc'], False, False

    if data['charging_state'] == 'Charging':
      if data['minutes_to_full_charge'] == 10:
        if msg_10min == False:
          bot.send_message(chat_id = chat_id,
            text = '\U0001F389 *' + str(veh_name) + '의 알림이에요!*\n' + str(data['charge_limit_soc']) + '% 충전 완료까지 10분 남았습니다.', parse_mode = 'Markdown')
          logger.info('__chrgCheck: 10 min left. (' + str(chat_id) + ', ' + str(veh_id) + ')')
          msg_10min = True

      elif data['minutes_to_full_charge'] == 5:
        if msg_5min == False:
          bot.send_message(chat_id = chat_id,
            text = '\U0001F389 *' + str(veh_name) + '의 알림이에요!*\n' + str(data['charge_limit_soc']) + '% 충전 완료까지 5분 남았습니다.', parse_mode = 'Markdown')
          logger.info('__chrgCheck: 5 min left. (' + str(chat_id) + ', ' + str(veh_id) + ')')
          msg_5min = True

    elif data['charging_state'] == 'Stopped':
      bot.send_message(chat_id = chat_id,
        text = '\U0001F389 *' + str(veh_name) + '의 알림이에요!*\n' + str(data['battery_level']) + '%에 충전이 중지되었습니다.', parse_mode = 'Markdown')
      logger.info('__chrgCheck: Charging stopped. (' + str(chat_id) + ', ' + str(veh_id) + ')')
      break

    elif data['charging_state'] == 'Complete':
      bot.send_message(chat_id = chat_id,
        text = '\U0001F389 *' + str(veh_name) + '의 알림이에요!*\n' + str(data['battery_level']) + '%에 충전이 완료되었습니다.', parse_mode = 'Markdown')
      logger.info('__chrgCheck: Charging Completed. (' + str(chat_id) + ', ' + str(veh_id) + ')')
      if data['charge_limit_soc'] == data['battery_level'] == 100: # 100% Battery Range ModifyVehicle
        sql.modifyVehicle(chat_id, veh_id, ['battery_range'], [round(data['battery_range']*1.609344, 1)])
        logger.info('__chrgCheck: modifyVehicle(' + str(chat_id) + ', ' + str(veh_id) + ') 100-percent battery_range updated.')
      break

    elif data['charging_state'] in ['Disconnected', 'NoPower']: break

    else: logger.error('__chrgCheck: Unknown charging_state: {} ({}, {})'.format(data['charging_state']), str(chat_id), str(veh_id))

    time.sleep(30)
    data = getChargeState(chat_id, veh_id)


# Reminder - Charge Time Pre-wake Vehicle
# Running @22:57 MON-SAT
def REMIND_ChrgTime_WakeVeh_Schedule():
  logger.info('REMIND_ChrgTime_WakeVeh: Schedule has been executed.')

  _ThreadName = 'ReminderChrgTimeWakeVehSchedule'
  logger.debug('Thread ' + _ThreadName + ' started.')
  threading.Thread(name = _ThreadName, target = REMIND_ChrgTime_WakeVeh).start()

def REMIND_ChrgTime_WakeVeh():
  for tuples in sql.inquiryVehicles(['reminder_charge_time']):
    if tuples[2] == 1:
      _ThreadName = 'CTWAKE' + str(tuples[0]) + str(tuples[1])
      logger.info('Thread ' + _ThreadName + ' started.')
      threading.Thread(name = _ThreadName, target = wakeVehicle, args = (tuples[0], tuples[1])).start()
      time.sleep(0.1)


# Reminder - Charge Time Alert
# Running @23:00 MON-SAT
def REMIND_ChrgTime_Schedule():
  logger.info('REMIND_ChrgTime: Schedule has been executed.')

  _ThreadName = 'ReminderChargeTimeSchedule'
  logger.debug('Thread ' + _ThreadName + ' started.')
  threading.Thread(name = _ThreadName, target = REMIND_ChrgTime_Target).start()

def REMIND_ChrgTime_Target():
  for tuples in sql.inquiryVehicles(['vehicle_name', 'reminder_charge_time']):
    if tuples[3] == 1:
      _ThreadName = 'CHRGTIME' + str(tuples[0]) + str(tuples[1])
      logger.info('Thread ' + _ThreadName + ' started.')
      threading.Thread(name = _ThreadName, target = REMIND_ChrgTime_Alert, args = (tuples[0], tuples[1], tuples[2])).start()

def REMIND_ChrgTime_Alert(chat_id, veh_id, veh_name):
  try:
    if getVehCurrent(chat_id, veh_id) == 'online':
      logger.debug('REMIND_ChrgTime_Alert: getVehCurrent(' + str(chat_id) + ', ' + str(veh_id) + ') == online')
      #_name = getVehName(chat_id, veh_id)
      _data = getChargeState(chat_id, veh_id)
      
      if not _data:
        pass
        # bot.send_message(chat_id = chat_id,
        #   text = '\U0001F389 *' + str(_name) + '의 알림이에요!*\n충전기 상태를 가져올 수 없습니다.')
      
      elif _data['charging_state'] == 'NoPower':
        logger.debug('REMIND_ChrgTime_Alert: charging_state(' + str(chat_id) + ', ' + str(veh_id) + ') == NoPower')
        text = '\U0001F389 *' + str(veh_name) + '의 알림이에요!*\n오후 11시부터 경부하 전력 시간대입니다.\n충전 대기 중인 차량의 충전을 시작해주세요:)\n'
        text += '충전 목표량은 *' + str(_data['charge_limit_soc']) + '%*이고, 충전 전류는 *' + str(_data['charge_current_request']) + 'A*로 설정되어 있어요.'
        bot.send_message(chat_id = chat_id, text = text, parse_mode = 'Markdown')
        logger.info('REMIND_ChrgTime_Alert: bot.send_message(' + str(chat_id) + ') sent successfully.')
      
      else:
        logger.debug('REMIND_ChrgTime_Alert: charging_state(' + str(chat_id) + ', ' + str(veh_id) + ') != NoPower')
        #bot.send_message(chat_id = chat_id, text = str(charging_state))
    else:
      logger.warning('REMIND_ChrgTime_Alert: getVehCurrent(' + str(chat_id) + ', ' + str(veh_id) + ') != online')
      #bot.send_message(chat_id = chat_id,
      #  text = '\U0001F389 *' + str(_name) + '의 알림이에요!*\n차량과의 연결에 실패했습니다.\n로그를 확인하시기 바랍니다.')
  
  except:
    logger.error('REMIND_ChrgTime_Alert: Exception error that occurred in the TRY syntax.')


# Sleep Preventer
# Running every min.
def PREVENT_Sleep_Schedule():
  logger.info('PREVENT_Sleep: Schedule has been executed.')

  _ThreadName = 'PreventSleepSchedule'
  logger.debug('Thread ' + _ThreadName + ' started.')
  threading.Thread(name = _ThreadName, target = PREVENT_Sleep_Target).start()

def PREVENT_Sleep_Target():
  for tuples in sql.inquiryVehicles(['prevent_sleep_1', 'prevent_sleep_2']):
    for i in tuples[2:]:
      if i:
        if len(i) == 13: 
          if i[datetime.today().weekday()] == '1': # 요일 체크
            if datetime.now().strftime('%H%M') == i[7:11]: # 시간 체크
              _ThreadName, _ThreadExist = 'PSWAKE' + str(tuples[0]) + str(tuples[1]), False

              for j in threading.enumerate():
                if str(j).split('(')[1].split(',')[0] == _ThreadName: _ThreadExist = True

              if not _ThreadExist:
                logger.info('Thread ' + _ThreadName + ' started.')
                threading.Thread(name = _ThreadName, target = PREVENT_Sleep, args = (tuples[0], tuples[1], int(i[11:]))).start()
                time.sleep(0.1)
                break

def PREVENT_Sleep(chat_id, veh_id, remain_time):
  logger.info('PREVENT_Sleep: just running. ({}, {}, range: 0)'.format(str(chat_id), str(veh_id)))
  threading.Thread(target = wakeVehicle, args = (chat_id, veh_id)).start()
  for i in range(remain_time * 60 - 2):
    time.sleep(59.99)
    logger.info('PREVENT_Sleep: just running. ({}, {}, range: {})'.format(str(chat_id), str(veh_id), i + 1))
    threading.Thread(target = wakeVehicle, args = (chat_id, veh_id)).start()


# Sentry Mode Switch Automation
# Running Every Min.
def SENTRY_Switch_Schedule():
    logger.debug('SENTRY_Switch: Schedule has been executed.')

    _ThreadName = 'SentrySwitchSchedule'
    logger.debug('Thread ' + _ThreadName + ' started.')
    threading.Thread(name = _ThreadName, target = SENTRY_Switch_Target).start()

def SENTRY_Switch_Target():
  for tuples in sql.inquiryVehicles(
  ['sentry_schedule_1', 'sentry_schedule_2', 'sentry_schedule_3', 'sentry_schedule_4', 'sentry_schedule_5']):
    _schedules = []

    for i in tuples[2:]:
      if i:
        if len(i) == 12: _schedules.append(i)

    if _schedules:
      _ThreadName, _ThreadExist = 'SENTRY' + str(tuples[0]) + str(tuples[1]), False

      for i in threading.enumerate():
        if str(i).split('(')[1].split(',')[0] == _ThreadName: _ThreadExist = True

      if not _ThreadExist:
        logger.info('Thread ' + _ThreadName + ' started.')
        threading.Thread(name = _ThreadName, target = SENTRY_Switch, args = (tuples[0], tuples[1], _schedules)).start()

def SENTRY_Switch(chat_id, veh_id, timestamps):
  for i in timestamps:
    if i[datetime.today().weekday()] == '1': # 요일 체크
      if datetime.now().strftime('%H%M') == i[7:11]: # 시간 체크
        for _ in range(10):
          if SentrySchedule(chat_id, veh_id, i[11]):
            _name = getVehName(chat_id, veh_id)
            text = '\U0001F389 *' + str(_name) + '의 알림이에요!*\n감시모드 자동화가 잘 동작했어요:)\n'
            bot.send_message(chat_id = chat_id, text = text, parse_mode = 'Markdown')
            logger.info('SENTRY_Switch: Command successfully executed. ({}, {})'.format(str(chat_id), str(veh_id)))
            return

          logger.warning('SENTRY_Switch: Command Retrying. ({}, {}, range: {})'.format(str(chat_id), str(veh_id), _))

        text = '\U000026A0 *감시모드 자동화를 실패했습니다.*\n차량이 주행 중이거나 일시적인 통신 불량일 수 있습니다.\n'\
             + '오류가 지속되는 경우 @TeslaAurora 로 문의해주세요.'
        bot.send_message(chat_id = chat_id, text = text, parse_mode = 'Markdown')
        return

  logger.debug('SENTRY_Switch: No schedule to execute. ({}, {})'.format(str(chat_id), str(veh_id)))


# Execution
def __schedules():
  COMMON_GetVehiclesConfig_Schedule()
  # COMMON_GetVehiclesState_Schedule()
  # SENTRY_Switch_Schedule()
  # schedule.every().day.at('16:27').do(REMIND_ChrgComplete_Schedule)

  schedule.every().hours.do(COMMON_GetVehiclesConfig_Schedule)
  schedule.every(2).minutes.do(COMMON_GetVehiclesState_Schedule)
  schedule.every().minutes.do(PREVENT_Sleep_Schedule)
  schedule.every().minutes.do(SENTRY_Switch_Schedule)

  schedule.every().monday.at('22:57').do(REMIND_ChrgTime_WakeVeh_Schedule)
  schedule.every().monday.at('23:00').do(REMIND_ChrgTime_Schedule)
  schedule.every().tuesday.at('22:57').do(REMIND_ChrgTime_WakeVeh_Schedule)
  schedule.every().tuesday.at('23:00').do(REMIND_ChrgTime_Schedule)
  schedule.every().wednesday.at('22:57').do(REMIND_ChrgTime_WakeVeh_Schedule)
  schedule.every().wednesday.at('23:00').do(REMIND_ChrgTime_Schedule)
  schedule.every().thursday.at('22:57').do(REMIND_ChrgTime_WakeVeh_Schedule)
  schedule.every().thursday.at('23:00').do(REMIND_ChrgTime_Schedule)
  schedule.every().friday.at('22:57').do(REMIND_ChrgTime_WakeVeh_Schedule)
  schedule.every().friday.at('23:00').do(REMIND_ChrgTime_Schedule)
  schedule.every().saturday.at('22:57').do(REMIND_ChrgTime_WakeVeh_Schedule)
  schedule.every().saturday.at('23:00').do(REMIND_ChrgTime_Schedule)
  
  while True:
    schedule.run_pending()
    time.sleep(0.5)

if __name__ == '__main__':
  logger.info('Scheduler started.')
  __schedules()

# 모든 스케줄 테스트 필요