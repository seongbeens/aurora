# This works separately from app.py in background.
import telegram
import schedule
import threading
import datetime as dt

from api import *
from dicts import *


# Enable logging
logger = logging.getLogger('schedules')
logger.addHandler(SchedLogHandler)

# Telegram
bot = telegram.Bot(token = telegram_token)

# Common - Get Vehicles Configuration & Write into VEHICLES.CSV
# Running Every 30min.
def COMMON_GetVehiclesConfig_Schedule():
  logger.debug('VEHCONF: Schedule has been executed.')

  _ThreadName = 'GetVehiclesConfigSchedule'
  logger.info('Thread ' + _ThreadName + ' started.')
  threading.Thread(name = _ThreadName, target = COMMON_GetVehiclesConfig).start()

def COMMON_GetVehiclesConfig():
  def _getApi(_chat_id, _veh_id):
    if getVehCurrent(_chat_id, _veh_id) == 'online':
      logger.debug('VEHCONF: getVehCurrent({}, {}) == online'.format(_chat_id, _veh_id))

      def _isNull(columns):
        for i in sql.inquiryVehicle(_chat_id, _veh_id, columns):
          if i is None: return True
        
        return False

      _columns = ['car_type', 'trim_badging', 'efficiency_package', 'exterior_color', 'wheel_type']

      if _isNull(_columns): # Vehicle Configuration
        _data = getVehicleConfig(_chat_id, _veh_id)
        if not _data: return

        logger.debug('VEHCONF: getVehicleConfig({}, {}) Received.'.format(_chat_id, _veh_id))
        
        _tuples = [_data['car_type'], _data['trim_badging'], _data['efficiency_package'], _data['exterior_color'], _data['wheel_type']]

        if sql.modifyVehicle(_chat_id, _veh_id, _columns, _tuples):
          logger.debug('VEHCONF: modifyVehicle({}, {}) Successfully.'.format(_chat_id, _veh_id))
        
        else: logger.warning('VEHCONF: modifyVehicle({}, {}) Failed.'.format(_chat_id, _veh_id))
      
    else: 
      logger.debug('VEHCONF: getVehCurrent({}, {}) != online'.format(_chat_id, _veh_id))

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
# Running Every Min.
def COMMON_GetVehiclesState_Schedule():
  logger.debug('VEHSTAT: Schedule has been executed.')

  _ThreadName = 'GetVehiclesStateSchedule'
  logger.info('Thread ' + _ThreadName + ' started.')
  threading.Thread(name = _ThreadName, target = COMMON_GetVehiclesState_Target).start()

def COMMON_GetVehiclesState_Target():
  for tuples in sql.inquiryVehicles(['vehicle_name', 'noti_vent', 'noti_chrgstart', 'noti_chrgcomplete']):
    _ThreadName, _ThreadExist = 'VEHSTAT' + str(tuples[0]) + str(tuples[1]), False

    for i in threading.enumerate():
      if str(i).split('(')[1].split(',')[0] == _ThreadName: _ThreadExist = True

    if not _ThreadExist:
      logger.debug('Thread ' + _ThreadName + ' started.')
      threading.Thread(name = _ThreadName, target = COMMON_GetVehiclesState, args = (tuples[0], tuples[1], tuples[2], tuples[3], tuples[4], tuples[5])).start()
      time.sleep(0.1)

def COMMON_GetVehiclesState(chat_id, veh_id, veh_name, _a, _b, _c):
  if getVehCurrent(chat_id, veh_id) == 'online':
    logger.debug('VEHSTAT: getVehCurrent({}, {}) == online'.format(chat_id, veh_id))

    data = {'vehicle_state': '', 'charge_state': '', 'drive_state': ''}
    data['vehicle_state'] = getVehicleState(chat_id, veh_id)
    data['charge_state'] = getChargeState(chat_id, veh_id)
    data['drive_state'] = getDriveState(chat_id, veh_id)

    # Collect Vehicle State
    __collect(chat_id, veh_id, data)

    # Checking if Door/Window is Open
    if _a == 1:
      _ThreadName, _ThreadExist = 'VENTCHK' + str(chat_id) + str(veh_id), False

      for i in threading.enumerate():
        if str(i).split('(')[1].split(',')[0] == _ThreadName: _ThreadExist = True
      
      if not _ThreadExist:
        logger.debug('Thread ' + _ThreadName + ' started.')
        t1 = threading.Thread(name = _ThreadName, target = __ventCheck, args = (chat_id, veh_id, veh_name, data['vehicle_state']))
        t1.start()

    # Reminder Charging Complete
    if _b == 1 or _c == 1:
      _ThreadName, _ThreadExist = 'CHRGCHK' + str(chat_id) + str(veh_id), False

      for i in threading.enumerate():
        if str(i).split('(')[1].split(',')[0] == _ThreadName: _ThreadExist = True
      
      if not _ThreadExist:
        logger.debug('Thread ' + _ThreadName + ' started.')
        t2 = threading.Thread(name = _ThreadName, target = __chrgCheck, args = (chat_id, veh_id, veh_name, data['charge_state'], _b, _c))
        t2.start()
    
    # Idle Mode
    if  (data['vehicle_state']['locked']) & \
    (not data['vehicle_state']['is_user_present']) & \
    (not data['vehicle_state']['sentry_mode']) & \
    (not data['charge_state']['charging_state'] in ['Starting', 'Charging']):
      logger.debug(
        'VEHSTAT: Enter Idle mode. ({}, {})'
        .format(chat_id, veh_id))
      time.sleep(900) # 15 min
      logger.debug(
        'VEHSTAT: Exit Idle mode. ({}, {})'
        .format(chat_id, veh_id))

  else: 
    logger.debug(
      'VEHSTAT: getVehCurrent({}, {}) != online'
      .format(chat_id, veh_id))

def __collect(chat_id, veh_id, data):
    columns = ['odometer', 'car_version', 'latitude', 'longitude']
    tuples = [round(data['vehicle_state']['odometer']*1.609344), data['vehicle_state']['car_version'].split()[0],
              data['drive_state']['latitude'], data['drive_state']['longitude']]

    # Update Vehicle Information
    if sql.modifyVehicle(chat_id, veh_id, columns, tuples):
      logger.debug('VEHSTAT: modifyVehicle({}, {}) Successfully.'.format(chat_id, veh_id))
    
    else: logger.warning('VEHSTAT: modifyVehicle({}, {}) Failed.'.format(chat_id, veh_id))

def __ventCheck(chat_id, veh_id, veh_name, data):
  def fors(variety):
    def execution():
      data = getVehicleState(chat_id, veh_id)
      for i in variety:
        if data[i] == 0: variety.remove(i)

    execution()
    for i in range(4):
      time.sleep(60)
      execution()
    
    if len(variety) == 0: return

    if getDriveState(chat_id, veh_id)['shift_state'] in ['R', 'N', 'D']: return
    
    if len(variety) == 1:
      bot.send_message(chat_id = chat_id,
        text = '\U0001F6A8 *' + str(veh_name) + '의 알림이에요!*\n' + dowor[variety[0]] + ' 열려 있습니다.', parse_mode = 'Markdown')
      logger.info('__ventCheck: The Door/window is Open. ({}, {})'.format(chat_id, veh_id))

    elif len(variety) > 1:
      text = '\U0001F6A8 *' + str(veh_name) + '의 알림이에요!*\n아래의 도어 또는 윈도우가 열려 있어요.\n'
      for i in variety: text += '\U00002796 {}\n'.format(dowor[i][:-1])
      bot.send_message(chat_id = chat_id, text = text, parse_mode = 'Markdown')
      logger.info('__ventCheck: The Doors/windows are Open. ({}, {})'.format(chat_id, veh_id))
    
    return

  if data:
    if ((data['df'] == 0) & (data['dr'] == 0) & (data['pf'] == 0) & (data['pr'] == 0)
      & (data['fd_window'] == 0) & (data['rd_window'] == 0) & (data['fp_window'] == 0) & (data['rp_window'] == 0)
      & (data['ft'] == 0) & (data['rt'] == 0)): return

  else: return

  variety = []

  if not data['df'] == 0: variety.append('df')
  if not data['dr'] == 0: variety.append('dr')
  if not data['pf'] == 0: variety.append('pf')
  if not data['pr'] == 0: variety.append('pr')

  if not data['fd_window'] == 0: variety.append('fd_window')
  if not data['rd_window'] == 0: variety.append('rd_window')
  if not data['fp_window'] == 0: variety.append('fp_window')
  if not data['rp_window'] == 0: variety.append('rp_window')

  if not data['ft'] == 0: variety.append('ft')
  if not data['rt'] == 0: variety.append('rt')

  fors(variety)

def __chrgCheck(chat_id, veh_id, veh_name, data, _start, _complete):
  # Variables
  msg_10min = msg_5min = False

  if data:
    if data['charging_state'] in ['Disconnected', 'NoPower', 'Stopped', 'Complete']: return
    existing_charge_limit_soc = data['charge_limit_soc']
  else: return

  # Notification of Start Charging
  if _start == 1:
    if (data['charging_state'] == 'Starting') or (data['charging_state'] == 'Charging' and data['charge_energy_added'] <= 0.1):
      bot.send_message(chat_id = chat_id,
        text = '\U0001F389 *' + str(veh_name) + '의 알림이에요!*\n' + str(data['battery_level']) + '%에서 충전이 시작되었습니다.\n'\
             + '충전 목표량은 *' + str(data['charge_limit_soc']) + '%*로 설정되어 있어요.', parse_mode = 'Markdown')
      logger.info('__chrgCheck: Start Charging. ({}, {})'.format(chat_id, veh_id))
      time.sleep(180)
      if _complete == 1: data = getChargeState(chat_id, veh_id)

  # Notification of Charging Completion
  if _complete == 1:
    while True:
      if existing_charge_limit_soc != data['charge_limit_soc']:
        existing_charge_limit_soc, msg_10min, msg_5min = data['charge_limit_soc'], False, False

      if data['charging_state'] == 'Charging':
        if data['minutes_to_full_charge'] == 10:
          if msg_10min == False:
            if data['trip_charging'] == True:
              bot.send_message(chat_id = chat_id,
                text = '\U0001F389 *' + str(veh_name) + '의 알림이에요!*\n주행 재개까지 10분 남았습니다.', parse_mode = 'Markdown')
            else: bot.send_message(chat_id = chat_id,
                text = '\U0001F389 *' + str(veh_name) + '의 알림이에요!*\n' + str(data['charge_limit_soc']) + '% 충전 완료까지 10분 남았습니다.', parse_mode = 'Markdown')
            logger.info('__chrgCheck: 10 min Left. ({}, {})'.format(chat_id, veh_id))
            msg_10min = True

        elif data['minutes_to_full_charge'] == 5:
          if msg_5min == False:
            if data['trip_charging'] == True:
              bot.send_message(chat_id = chat_id,
                text = '\U0001F389 *' + str(veh_name) + '의 알림이에요!*\n주행 재개까지 5분 남았습니다.', parse_mode = 'Markdown')
            else: bot.send_message(chat_id = chat_id,
                text = '\U0001F389 *' + str(veh_name) + '의 알림이에요!*\n' + str(data['charge_limit_soc']) + '% 충전 완료까지 5분 남았습니다.', parse_mode = 'Markdown')
            logger.info('__chrgCheck: 5 min Left. ({}, {})'.format(chat_id, veh_id))
            msg_5min = True

      elif data['charging_state'] == 'Stopped':
        bot.send_message(chat_id = chat_id,
          text = '\U0001F389 *' + str(veh_name) + '의 알림이에요!*\n' + str(data['battery_level']) + '%에서 충전이 중지되었습니다.', parse_mode = 'Markdown')
        logger.info('__chrgCheck: Charging Stopped. ({}, {})'.format(chat_id, veh_id))
        break

      elif data['charging_state'] == 'Complete':
        bot.send_message(chat_id = chat_id,
          text = '\U0001F389 *' + str(veh_name) + '의 알림이에요!*\n' + str(data['battery_level']) + '%에서 충전이 완료되었습니다.', parse_mode = 'Markdown')
        logger.info('__chrgCheck: Charging Completed. (' + str(chat_id) + ', ' + str(veh_id) + ')')
        if data['charge_limit_soc'] == data['battery_level'] == 100: # 100% Battery Range ModifyVehicle
          sql.modifyVehicle(chat_id, veh_id, ['battery_range'], [round(data['battery_range']*1.609344, 1)])
          logger.info('__chrgCheck: battery_range Updated. ({}, {})'.format(chat_id, veh_id))
        break

      elif data['charging_state'] in ['Disconnected', 'NoPower']: break

      else: logger.error('__chrgCheck: Unknown charging_state: {} ({}, {})'.format(data['charging_state'], chat_id, veh_id))

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
  for tuples in sql.inquiryVehicles(['noti_chrgtime']):
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
  for tuples in sql.inquiryVehicles(['vehicle_name', 'noti_chrgtime']):
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
        logger.info('REMIND_ChrgTime_Alert: Sending Message. ({}, {})'.format(chat_id, veh_id))
      
      else:
        logger.debug('REMIND_ChrgTime_Alert: charging_state({}, {}) != NoPower'.format(chat_id, veh_id))
        #bot.send_message(chat_id = chat_id, text = str(charging_state))
    else:
      logger.warning('REMIND_ChrgTime_Alert: getVehCurrent({}, {}) != online'.format(chat_id, veh_id))
      #bot.send_message(chat_id = chat_id,
      #  text = '\U0001F389 *' + str(_name) + '의 알림이에요!*\n차량과의 연결에 실패했습니다.\n로그를 확인하시기 바랍니다.')
  
  except:
    logger.error('REMIND_ChrgTime_Alert: Exception error that occurred in the TRY syntax.')


# Sleep Preventer
# Running every min.
def PREVENT_Sleep_Schedule():
  logger.debug('PREVENT_Sleep: Schedule has been executed.')

  _ThreadName = 'PreventSleepSchedule'
  logger.debug('Thread ' + _ThreadName + ' started.')
  threading.Thread(name = _ThreadName, target = PREVENT_Sleep_Target).start()

def PREVENT_Sleep_Target():
  for tuples in sql.inquirySchedules(['prevent_sleep_1', 'prevent_sleep_2']):
    for i in tuples[2:]:
      if i:
        if len(i) == 13: 
          if i[dt.datetime.today().weekday()] == '1': # 요일 체크
            nowTime = dt.datetime.now()
            startTime = nowTime.replace(hour = int(i[7:9]), minute = int(i[9:11]))
            endTime = startTime + dt.timedelta(minutes = int(i[11:]) * 60 - 1)
            if startTime <= nowTime <= endTime:
              _ThreadName, _ThreadExist = 'PSWAKE' + str(tuples[0]) + str(tuples[1]), False

              for j in threading.enumerate():
                if str(j).split('(')[1].split(',')[0] == _ThreadName: _ThreadExist = True

              if not _ThreadExist:
                logger.info('Thread ' + _ThreadName + ' started.')
                threading.Thread(name = _ThreadName, target = PREVENT_Sleep, args = (tuples[0], tuples[1], startTime, endTime)).start()
                time.sleep(0.1)
                break

def PREVENT_Sleep(chat_id, veh_id, startTime, endTime):
  logger.info('PREVENT_Sleep: Just running. ({}, {})'.format(chat_id, veh_id))

  _name = getVehName(chat_id, veh_id)
  threading.Thread(target = wakeVehicle, args = (chat_id, veh_id)).start()

  if dt.datetime.now() - dt.timedelta(seconds = 30) <= startTime <= dt.datetime.now() + dt.timedelta(seconds = 30):
    text = '\U0001F389 *' + str(_name) + '의 알림이에요!*\n설정한 절전 방지 스케줄이 시작되고 있습니다:)\n'
    bot.send_message(chat_id = chat_id, text = text, parse_mode = 'Markdown')
    logger.info('PREVENT_Sleep: Start Message Sent. ({}, {})'.format(startTime.strftime('%H%M'), endTime.strftime('%H%M')))
  
  while endTime >= dt.datetime.now() + dt.timedelta(minutes = 3):
    time.sleep(180)
    logger.debug('PREVENT_Sleep: Running. ({}, {}, endTime: {})'.format(chat_id, veh_id, endTime.strftime('%H%M')))
    threading.Thread(target = wakeVehicle, args = (chat_id, veh_id)).start()

  if dt.datetime.now() - dt.timedelta(seconds = 30) <= endTime <= dt.datetime.now() + dt.timedelta(seconds = 30):
    text = '\U0001F389 *' + str(_name) + '의 알림이에요!*\n설정한 절전 방지 스케줄이 완료되었습니다:)\n'
    bot.send_message(chat_id = chat_id, text = text, parse_mode = 'Markdown')
    logger.info('PREVENT_Sleep: End Message Sent. ({}, {})'.format(startTime.strftime('%H%M'), endTime.strftime('%H%M')))


# PreConditioning
# Running Every Min.
def PreConditioning_Schedule():
    logger.debug('PreConditioning: Schedule has been executed.')

    _ThreadName = 'PreConditioningSchedule'
    logger.debug('Thread ' + _ThreadName + ' started.')
    threading.Thread(name = _ThreadName, target = PreConditioning_Target).start()

def PreConditioning_Target():
  for tuples in sql.inquirySchedules(
  ['preconditioning_1', 'preconditioning_2', 'preconditioning_3', 'preconditioning_4', 'preconditioning_5']):
    _schedules = []

    for i in tuples[2:]:
      if i:
        if len(i) == 13: _schedules.append(i)

    if _schedules:
      for i in _schedules:
        if i[dt.datetime.today().weekday()] == '1': # 요일 체크
          nowTime = dt.datetime.now()
          startTime = nowTime.replace(hour = int(i[7:9]), minute = int(i[9:11]))
          switchTime = startTime + dt.timedelta(seconds = int(i[11:]) * 60 // 2)
          endTime = startTime + dt.timedelta(minutes = int(i[11:]) - 1)
          if startTime <= nowTime <= endTime:
            _ThreadName, _ThreadExist = 'PRECON' + str(tuples[0]) + str(tuples[1]), False

            for j in threading.enumerate():
              if str(j).split('(')[1].split(',')[0] == _ThreadName: _ThreadExist = True

            if not _ThreadExist:
              logger.info('Thread ' + _ThreadName + ' started.')
              threading.Thread(name = _ThreadName, target = PreConditioning_exec, args = (tuples[0], tuples[1], startTime, switchTime, endTime)).start()

    else: logger.debug('PreConditioning_Target: No schedule to execute. ({}, {})'.format(tuples[0], tuples[1]))

def PreConditioning_exec(chat_id, veh_id, startTime, switchTime, endTime):
  for i in range(10):
    if wakeVehicle(chat_id, veh_id):
      if preConditioning(chat_id, veh_id, True):
        logger.info('PreConditioning_exec: Preconditioning Started. ({}, {})'.format(chat_id, veh_id))
        _name = getVehName(chat_id, veh_id)

        if dt.datetime.now() - dt.timedelta(seconds = 30) <= startTime <= dt.datetime.now() + dt.timedelta(seconds = 30):
          text = '\U0001F389 *' + str(_name) + '의 알림이에요!*\n설정한 프리컨디셔닝이 시작되고 있습니다:)\n'
          bot.send_message(chat_id = chat_id, text = text, parse_mode = 'Markdown')
          logger.info('PreConditioning_exec: Start Message Sent. ({}, {})'.format(startTime.strftime('%H%M'), endTime.strftime('%H%M')))

        while True:
          if dt.datetime.now() <= switchTime <= dt.datetime.now() + dt.timedelta(seconds = 30): break
          time.sleep(20)

        if getVehCurrent(chat_id, veh_id) != 'online':
          logger.info('PreConditioning_exec: Preconditioning Aborted. ({}, {}, Not Online)'.format(chat_id, veh_id))
          return

        for _ in range(10):
          if preConditioning(chat_id, veh_id, False):
            logger.info('PreConditioning_exec: Preconditioning Switched. ({}, {})'.format(chat_id, veh_id))
            break
        
        while True:
          if dt.datetime.now() <= endTime <= dt.datetime.now() + dt.timedelta(seconds = 30): break
          time.sleep(20)

        if getVehCurrent(chat_id, veh_id) != 'online':
          logger.info('PreConditioning_exec: Preconditioning Aborted. ({}, {}, Not Online)'.format(chat_id, veh_id))
          return

        if getDriveState(chat_id, veh_id)['shift_state'] in ['R', 'N', 'D']:
          logger.info('PreConditioning_exec: Preconditioning Aborted. ({}, {}, Driving)'.format(chat_id, veh_id))
          return

        for _ in range(10):
          if HVACToggle(chat_id, veh_id) == 0: break
        
        if dt.datetime.now() - dt.timedelta(seconds = 30) <= endTime <= dt.datetime.now() + dt.timedelta(seconds = 30):
          text = '\U0001F389 *' + str(_name) + '의 알림이에요!*\n프리컨디셔닝 설정 시간이 초과하여 공조기가 꺼집니다.\n'
          bot.send_message(chat_id = chat_id, text = text, parse_mode = 'Markdown')
          logger.info('PreConditioning_exec: End Message Sent. ({}, {})'.format(startTime.strftime('%H%M'), endTime.strftime('%H%M')))
        
        logger.info('PreConditioning_exec: Preconditioning Completed. ({}, {})'.format(chat_id, veh_id))
        return

      logger.warning('PreConditioning_exec: Command Retrying. ({}, {}, range: {})'.format(chat_id, veh_id, i+1))

  text = '\U000026A0 *프리컨디셔닝을 실패했습니다.*\n일시적인 통신 불량일 수 있습니다.\n'\
        + '오류가 지속되는 경우 @TeslaAuroraCS 로 문의해주세요.'
  bot.send_message(chat_id = chat_id, text = text, parse_mode = 'Markdown')

  logger.warning('PreConditioning_exec: Aborted. ({}, {}, Too Many Retries)'.format(chat_id, veh_id))
  return


# Charge Stop
# Running Every Min.
def CHRG_Stop_Schedule():
  logger.debug('CHRG_Stop: Schedule has been executed.')

  _ThreadName = 'ChargeStopSchedule'
  logger.debug('Thread ' + _ThreadName + ' started.')
  threading.Thread(name = _ThreadName, target = CHRG_Stop_Target).start()

def CHRG_Stop_Target():
  for tuples in sql.inquirySchedules(['chrg_stop_1']):
    if tuples[2]:
      nowTime = dt.datetime.now()
      startTime = nowTime.replace(hour = int(tuples[2][:2]), minute = int(tuples[2][2:]))
      endTime = startTime + dt.timedelta(seconds = 30)
      if startTime <= nowTime <= endTime:
      # if dt.datetime.now().strftime('%H%M') == tuples[2]: # 시간 체크
        _ThreadName, _ThreadExist = 'CHRGSTOP' + str(tuples[0]) + str(tuples[1]), False

        for i in threading.enumerate():
          if str(i).split('(')[1].split(',')[0] == _ThreadName: _ThreadExist = True

        if not _ThreadExist:
          logger.info('Thread ' + _ThreadName + ' started.')
          threading.Thread(name = _ThreadName, target = chargeStop, args = (tuples[0], tuples[1])).start()


# Sentry Mode Switch Automation
# Running Every Min.
def SENTRY_Switch_Schedule():
    logger.debug('SENTRY_Switch: Schedule has been executed.')

    _ThreadName = 'SentrySwitchSchedule'
    logger.debug('Thread ' + _ThreadName + ' started.')
    threading.Thread(name = _ThreadName, target = SENTRY_Switch_Target).start()

def SENTRY_Switch_Target():
  for tuples in sql.inquirySchedules(
  ['sentry_switch_1', 'sentry_switch_2', 'sentry_switch_3', 'sentry_switch_4', 'sentry_switch_5']):
    _schedules = []

    for i in tuples[2:]:
      if i:
        if len(i) == 12: _schedules.append(i)

    if _schedules:
      for i in _schedules:
        if i[dt.datetime.today().weekday()] == '1': # 요일 체크
          nowTime = dt.datetime.now()
          startTime = nowTime.replace(hour = int(i[7:9]), minute = int(i[9:11]))
          endTime = startTime + dt.timedelta(seconds = 30)
          if startTime <= nowTime <= endTime:
            _ThreadName, _ThreadExist = 'SENTRY' + str(tuples[0]) + str(tuples[1]), False

            for j in threading.enumerate():
              if str(j).split('(')[1].split(',')[0] == _ThreadName: _ThreadExist = True

            if not _ThreadExist:
              logger.info('Thread ' + _ThreadName + ' started.')
              threading.Thread(name = _ThreadName, target = SENTRY_Switch, args = (tuples[0], tuples[1], int(i[11]))).start()

    else: logger.debug('SENTRY_Switch_Target: No schedule to execute. ({}, {})'.format(tuples[0], tuples[1]))

def SENTRY_Switch(chat_id, veh_id, switch):
  for i in range(10):
    if sentrySchedule(chat_id, veh_id, switch) == 0:
      _name = getVehName(chat_id, veh_id)

      text = '\U0001F389 *' + str(_name) + '의 알림이에요!*\n설정하신 자동화 스케줄로 감시모드가 꺼졌습니다:)\n'
      bot.send_message(chat_id = chat_id, text = text, parse_mode = 'Markdown')

      logger.info('SENTRY_Switch: Sentry Mode Turned Off. ({}, {})'.format(chat_id, veh_id))

      time.sleep(30)
      return
    
    elif sentrySchedule(chat_id, veh_id, switch) == 1:
      _name = getVehName(chat_id, veh_id)

      text = '\U0001F389 *' + str(_name) + '의 알림이에요!*\n설정하신 자동화 스케줄로 감시모드가 켜졌습니다:)\n'
      bot.send_message(chat_id = chat_id, text = text, parse_mode = 'Markdown')

      logger.info('SENTRY_Switch: Sentry Mode Turned On. ({}, {})'.format(chat_id, veh_id))

      time.sleep(30)
      return

    logger.warning('SENTRY_Switch: Command Retrying. ({}, {}, range: {})'.format(chat_id, veh_id, i+1))

  text = '\U000026A0 *감시모드 자동화를 실패했습니다.*\n차량이 주행 중이거나 일시적인 통신 불량일 수 있습니다.\n'\
        + '오류가 지속되는 경우 @TeslaAuroraCS 로 문의해주세요.'
  bot.send_message(chat_id = chat_id, text = text, parse_mode = 'Markdown')
  return


# Execution
def __schedules():
  # COMMON_GetVehiclesConfig_Schedule()
  # COMMON_GetVehiclesState_Schedule()
  # SENTRY_Switch_Schedule()
  # schedule.every().day.at('16:27').do(REMIND_ChrgComplete_Schedule)

  schedule.every().hours.at('00:20').do(COMMON_GetVehiclesConfig_Schedule)
  schedule.every().hours.at('30:20').do(COMMON_GetVehiclesConfig_Schedule)

  schedule.every().minutes.at(':30').do(COMMON_GetVehiclesState_Schedule)

  schedule.every().minutes.at(':00').do(PREVENT_Sleep_Schedule)
  schedule.every().minutes.at(':05').do(PreConditioning_Schedule)
  schedule.every().minutes.at(':10').do(CHRG_Stop_Schedule)
  schedule.every().minutes.at(':15').do(SENTRY_Switch_Schedule)

  schedule.every().monday.at('22:57').do(REMIND_ChrgTime_WakeVeh_Schedule)
  schedule.every().tuesday.at('22:57').do(REMIND_ChrgTime_WakeVeh_Schedule)
  schedule.every().wednesday.at('22:57').do(REMIND_ChrgTime_WakeVeh_Schedule)
  schedule.every().thursday.at('22:57').do(REMIND_ChrgTime_WakeVeh_Schedule)
  schedule.every().friday.at('22:57').do(REMIND_ChrgTime_WakeVeh_Schedule)
  schedule.every().saturday.at('22:57').do(REMIND_ChrgTime_WakeVeh_Schedule)

  schedule.every().monday.at('23:00').do(REMIND_ChrgTime_Schedule)
  schedule.every().tuesday.at('23:00').do(REMIND_ChrgTime_Schedule)
  schedule.every().wednesday.at('23:00').do(REMIND_ChrgTime_Schedule)
  schedule.every().thursday.at('23:00').do(REMIND_ChrgTime_Schedule)
  schedule.every().friday.at('23:00').do(REMIND_ChrgTime_Schedule)
  schedule.every().saturday.at('23:00').do(REMIND_ChrgTime_Schedule)
  
  while True:
    schedule.run_pending()
    time.sleep(0.5)

if __name__ == '__main__':
  logger.info('Scheduler started.')
  __schedules()