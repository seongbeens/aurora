#from os import stat
import time
import json
import requests
import mysql as sql
from vars import *

# Enable Logging
errorLogger = logging.getLogger(__name__)
errorLogger.addHandler(ErrorLogHandler)

# Internal Def.

def __inquiryToken(chat_id):
	return sql.inquiryAccount(chat_id, ['token_access'])[0]

def __vehicles(token, type = 0):
	url = 'https://owner-api.teslamotors.com/api/1/vehicles'
	headers = {'Authorization': 'Bearer ' + token, 'User-Agent': 'Shortcuts'}
	r = requests.get(url, headers = headers)
	if type == 100: return json.loads(r.content)['count']
	elif type == 200: return json.loads(r.content)['response']
	else: return r.status_code

def __state(id, token, column):
	url = 'https://owner-api.teslamotors.com/api/1/vehicles/{}'.format(id)
	headers = {'Authorization': 'Bearer ' + token, 'User-Agent': 'Shortcuts'}
	r = requests.get(url, headers = headers)
	if r.status_code == 429: return r.status_code
	return json.loads(r.content)['response'][column]

def __vehdata(id, token):
	url = 'https://owner-api.teslamotors.com/api/1/vehicles/{}/vehicle_data'.format(id)
	headers = {'Authorization': 'Bearer ' + token, 'User-Agent': 'Shortcuts'}
	for _ in range(0, 10):
		r = requests.get(url, headers = headers)
		if r.status_code == 429: return r.status_code
		d = json.loads(r.content)['response']
		if d: return d
		time.sleep(3)
	return False

def __chrgsites(id, token):
	url = 'https://owner-api.teslamotors.com/api/1/vehicles/{}/nearby_charging_sites'.format(id)
	headers = {'Authorization': 'Bearer ' + token, 'User-Agent': 'Shortcuts'}
	for _ in range(0, 5):
		r = requests.get(url, headers = headers)
		if r.status_code == 429: return r.status_code
		d = json.loads(r.content)['response']
		if d: return d
		time.sleep(3)
	return False

def __wakeUp(id, token):
	url = 'https://owner-api.teslamotors.com/api/1/vehicles/{}/wake_up'.format(id)
	headers = {'Authorization': 'Bearer ' + token, 'User-Agent': 'Shortcuts'}
	for _ in range(0, 8):
		r = requests.post(url, headers = headers)
		d = json.loads(r.content)['response']['state']
		if d == 'online': return True
		time.sleep(15)
	return False

def __unlock(id, token):
	url = 'https://owner-api.teslamotors.com/api/1/vehicles/{}/command/door_unlock'.format(id)
	headers = {'Authorization': 'Bearer ' + token, 'User-Agent': 'Shortcuts'}
	for _ in range(0, 5):
		r = requests.post(url, headers = headers)
		d = json.loads(r.content)['response']['result']
		if d is True: return True
		time.sleep(3)
	return False

def __lock(id, token):
	url = 'https://owner-api.teslamotors.com/api/1/vehicles/{}/command/door_lock'.format(id)
	headers = {'Authorization': 'Bearer ' + token, 'User-Agent': 'Shortcuts'}
	for _ in range(0, 5):
		r = requests.post(url, headers = headers)
		d = json.loads(r.content)['response']['result']
		if d is True: return True
		time.sleep(3)
	return False

def __window(id, token, command, lat = 0, lon = 0):
	url = 'https://owner-api.teslamotors.com/api/1/vehicles/{}/command/window_control'.format(id)
	headers = {'Authorization': 'Bearer ' + token, 'User-Agent': 'Shortcuts'}
	for _ in range(0, 5):
		r = requests.post(url, headers = headers, data = {'command': command, 'lat': lat, 'lon': lon})
		d = json.loads(r.content)['response']['result']
		if d is True: return True
		time.sleep(3)
	return False

def __sentry(id, token, bools):
	url = 'https://owner-api.teslamotors.com/api/1/vehicles/{}/command/set_sentry_mode'.format(id)
	headers = {'Authorization': 'Bearer ' + token, 'User-Agent': 'Shortcuts'}
	for _ in range(0, 5):
		r = requests.post(url, headers = headers, data = {'on': bools})
		d = json.loads(r.content)['response']['result']
		if d is True: return True
		time.sleep(3)
	return False

def __flashlights(id, token):
	url = 'https://owner-api.teslamotors.com/api/1/vehicles/{}/command/flash_lights'.format(id)
	headers = {'Authorization': 'Bearer ' + token, 'User-Agent': 'Shortcuts'}
	for _ in range(0, 5):
		r = requests.post(url, headers = headers)
		d = json.loads(r.content)['response']['result']
		if d is True: return True
		time.sleep(3)
	return False

def __hvac(id, token, togg):
	url = 'https://owner-api.teslamotors.com/api/1/vehicles/{}/command/auto_conditioning_'.format(id) + togg
	headers = {'Authorization': 'Bearer ' + token, 'User-Agent': 'Shortcuts'}
	for _ in range(0, 5):
		r = requests.post(url, headers = headers)
		d = json.loads(r.content)['response']['result']
		if d is True: return True
		time.sleep(3)
	return False

def __temps(id, token, value):
	url = 'https://owner-api.teslamotors.com/api/1/vehicles/{}/command/set_temps'.format(id)
	headers = {'Authorization': 'Bearer ' + token, 'User-Agent': 'Shortcuts'}
	for _ in range(0, 5):
		r = requests.post(url, headers = headers, data = {'driver_temp': value, 'passenger_temp': value})
		d = json.loads(r.content)['response']['result']
		if d is True:
			return True
		time.sleep(3)
	return False

def __port(id, token, togg):
	url = 'https://owner-api.teslamotors.com/api/1/vehicles/{}/command/charge_port_door_'.format(id) + togg
	headers = {'Authorization': 'Bearer ' + token, 'User-Agent': 'Shortcuts'}
	for _ in range(0, 5):
		r = requests.post(url, headers = headers)
		d = json.loads(r.content)['response']['result']
		if d is True: return True
		time.sleep(3)
	return False

def __data_request(id, token, params):
	url = 'https://owner-api.teslamotors.com/api/1/vehicles/{}/data_request/'.format(id) + params
	headers = {'Authorization': 'Bearer ' + token, 'User-Agent': 'Shortcuts'}
	for _ in range(0, 10):
		r = requests.get(url, headers = headers)
		d = json.loads(r.content)['response']
		if d: return d
	return False

############################################################################################################

# External Def.
# COMMON
def verifyConn(token):
	for _ in range(0, 5):
		if __vehicles(token) == 200: return True
	
	return False #401

# GENERATE
def generateVehicles(chat_id, token): # 함수명 변경
	try:
		for i in __vehicles(token, 200):
			if sql.createVehicle(
				chat_id, i['id'], i['display_name'], i['vin']): pass
			else: return False
		return True

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

# GET
def getVehCounts(chat_id, token = None):
	try:
		if not token: token = __inquiryToken(chat_id)
		return __vehicles(token, 100)

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def getVehCurrent(chat_id, veh_id = None): #veh_id가 없으면 전체 vehicles 리스트 return
	try:
		token = __inquiryToken(chat_id)
		if not veh_id:	
			return __vehicles(token, 200)
		else:
			return __state(veh_id, token, 'state')

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def getVehName(chat_id, veh_id):
	try:
		token = __inquiryToken(chat_id)
		return __state(veh_id, token, 'display_name')

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def getVehData(chat_id, veh_id):
	try:
		token = __inquiryToken(chat_id)
		for _ in range(0, 9):
			data = __vehdata(veh_id, token)
			if data: return data
		return False

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def getNearbyChrgSites(chat_id, veh_id):
	try:
		token = __inquiryToken(chat_id)
		return __chrgsites(veh_id, token)

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

# WAKE
def wakeVehicle(chat_id, veh_id): # 함수 분리
	try:
		token = __inquiryToken(chat_id)
		if __wakeUp(veh_id, token): return True
		else: return False

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def wakeVehicles(chat_id): # 함수 분리
	try:
		token = __inquiryToken(chat_id)
		for i in __vehicles(token, 200):
			if __wakeUp(i['id'], token): pass
			else: return False
			return True

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

# DATA_REQUEST
def getChargeState(chat_id, veh_id):
	try:
		token = __inquiryToken(chat_id)
		for _ in range(0, 9):
			_data = __data_request(veh_id, token, 'charge_state')
			if _data: return _data
		return False

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def getClimateState(chat_id, veh_id):
	try:
		token = __inquiryToken(chat_id)
		for _ in range(0, 9):
			_data = __data_request(veh_id, token, 'climate_state')
			if _data: return _data
		return False

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def getDriveState(chat_id, veh_id):
	try:
		token = __inquiryToken(chat_id)
		for _ in range(0, 9):
			_data = __data_request(veh_id, token, 'drive_state')
			if _data: return _data
		return False

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def getVehicleConfig(chat_id, veh_id):
	try:
		token = __inquiryToken(chat_id)
		for _ in range(0, 9):
			_data = __data_request(veh_id, token, 'vehicle_config')
			if _data: return _data
		return False

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def getVehicleState(chat_id, veh_id):
	try:
		token = __inquiryToken(chat_id)
		for _ in range(0, 9):
			_data = __data_request(veh_id, token, 'vehicle_state')
			if _data: return _data
		return False

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

# COMMANDS
def lockToggle(chat_id, veh_id):
	try:
		token = __inquiryToken(chat_id)

		for _ in range(0, 9):
			_data = __data_request(veh_id, token, 'vehicle_state')
			if _data: break

		if _data:
			if _data['locked']:
				if __unlock(veh_id, token): return 1
				else: return False
			elif not _data['locked']:
				if __lock(veh_id, token): return 0
				else: return False
			else: return False
		else: return False

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def windowToggle(chat_id, veh_id):
	try:
		token = __inquiryToken(chat_id)

		for _ in range(0, 9):
			_data = __data_request(veh_id, token, 'vehicle_state')
			if _data: break

		if _data:
			if ((_data['fd_window'] == 0) & (_data['fp_window'] == 0)
			  & (_data['rd_window'] == 0) & (_data['rp_window'] == 0)):
				if __window(veh_id, token, 'vent'): return 1
				else: return False
			else:
				for _ in range(0, 9):
					_data = __data_request(veh_id, token, 'drive_state')
					if _data: break
				if __window(veh_id, token, 'close',
					_data['latitude'], _data['longitude']): return 0
				else: return False
		else: return False

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def sentryToggle(chat_id, veh_id):
	try:
		token = __inquiryToken(chat_id)

		for _ in range(0, 9):
			_data = __data_request(veh_id, token, 'vehicle_state')
			if _data: break

		if _data:
			if not _data['sentry_mode']:
				if __sentry(veh_id, token, True): return 1
				else: return False
			elif _data['sentry_mode']:
				if __sentry(veh_id, token, False): return 0
				else: return False
			else: return False
		else: return False

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def flashlights(chat_id, veh_id):
	try:
		token = __inquiryToken(chat_id)

		if __flashlights(veh_id, token): return True
		else: return False

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def HVACToggle(chat_id, veh_id):
	try:
		token = __inquiryToken(chat_id)

		for _ in range(0, 9):
			_data = __data_request(veh_id, token, 'climate_state')
			if _data: break

		if _data:
			if not _data['is_climate_on']:
				_dtemp = _data['driver_temp_setting']
				_ptemp = _data['passenger_temp_setting']
				if __hvac(veh_id, token, 'start'): return _dtemp
				else: return False
			elif _data['is_climate_on']:
				if __hvac(veh_id, token, 'stop'): return 0
				else: return False
			else: return False
		else: return False

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def setHVACTemp(chat_id, veh_id, value):
	try:
		token = __inquiryToken(chat_id)

		for _ in range(0, 9):
			if __temps(veh_id, token, value): return True
		
		return False

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def portToggle(chat_id, veh_id):
	try:
		token = __inquiryToken(chat_id)

		for _ in range(0, 9):
			_data = __data_request(veh_id, token, 'charge_state')
			if _data: break

		if _data:
			if not _data['charge_port_door_open']:
				if __port(veh_id, token, 'open'): return 1
				else: return False
			elif _data['charge_port_door_open']:
				if _data['charging_state'] == 'Disconnected':
					if __port(veh_id, token, 'close'): return 0
					else: return False
				else: return -1
			else: return False
		else: return False

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def portUnlock(chat_id, veh_id):
	try:
		token = __inquiryToken(chat_id)

		for _ in range(0, 9):
			_data = __data_request(veh_id, token, 'charge_state')
			if _data: break

		if _data:
			if _data['charge_port_door_open']:
				if __port(veh_id, token, 'open'): return 1
				else: return False
			else: return 0
		else: return False

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False


# Schedule
def SentrySchedule(chat_id, veh_id, switch):
	try:
		token = __inquiryToken(chat_id)

		for _ in range(10):
			if __wakeUp(veh_id, token): break
			
		if switch == '0':
			for _ in range(10):
				if __sentry(veh_id, token, False): return True
		
		if switch == '1':
			for _ in range(10):
				if __sentry(veh_id, token, True): return True
		
		return False

	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

# Token
class Token:
  def __init__(self, chat_id):
    # Initialize 'self.'
    self.chat_id = chat_id

    __refresh_token = sql.inquiryAccount(chat_id, ['token_refresh'])
    if __refresh_token: self.refresh_token = __refresh_token[0]
    
    __access_token = sql.inquiryAccount(chat_id, ['token_access'])
    if __access_token: self.access_token = __access_token[0]

  def generate(self, refresh_token = None):
    if not refresh_token:
      refresh_token = self.refresh_token

    # Exchange bearer token for access token
    url = 'https://auth.tesla.com/oauth2/v3/token'
    payload = { 'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': 'ownerapi',
                'scope': 'openid email offline_access' }

    response = requests.post(url, json = payload)
    
    # Verify vaild refresh token
    if not response.status_code == 200: return False

    # Get new sso refresh token
    sso_refresh_token = json.loads(response.text)['refresh_token']

    # Get new owner api access token from sso access token
    sso_access_token = json.loads(response.text)['access_token']

    owner_api_url = 'https://owner-api.teslamotors.com/oauth/token'
    owner_api_payload = { 'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                          'client_id': '81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384' }

    owner_api_headers = { 'Authorization': 'Bearer ' + sso_access_token }
    owner_api_response = requests.post(owner_api_url, json = owner_api_payload, headers = owner_api_headers)
    owner_api_access_token = json.loads(owner_api_response.text)['access_token']

    self.refresh_token = sso_refresh_token
    self.access_token = owner_api_access_token

    return owner_api_access_token


  def renewal(self):
    # Exchange bearer token for access token
    url = 'https://auth.tesla.com/oauth2/v3/token'
    payload = { 'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': 'ownerapi',
                'scope': 'openid email offline_access' }

    response = requests.post(url, json = payload)
    
    # Verify vaild refresh token
    if not response.status_code == 200: return 1

    # Get new sso refresh token
    sso_refresh_token = json.loads(response.text)['refresh_token']

    # Get new owner api access token from sso access token
    sso_access_token = json.loads(response.text)['access_token']

    owner_api_url = 'https://owner-api.teslamotors.com/oauth/token'
    owner_api_payload = { 'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                          'client_id': '81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384' }

    owner_api_headers = { 'Authorization': 'Bearer ' + sso_access_token }
    owner_api_response = requests.post(owner_api_url, json = owner_api_payload, headers = owner_api_headers)
    owner_api_access_token = json.loads(owner_api_response.text)['access_token']

    # Verify Exist
    if owner_api_access_token:
      self.access_token = owner_api_access_token
    else: return 2

    # Count Vehicles
    try: vehicle_cnts = getVehCounts(self.chat_id, owner_api_access_token)
    except: return 3

    # Number of Vehicles (0 < n < 2)
    if vehicle_cnts == 0: return 4
    elif vehicle_cnts > 2: return 5

    # Append Number of Vehicles into DB
    if sql.modifyAccount(self.chat_id, ['vehicle_counts'], [vehicle_cnts]): pass
    else: return 6

    # Append Tokens into DB
    if sql.modifyAccount(self.chat_id, ['token_refresh', 'token_access'], [sso_refresh_token, owner_api_access_token]): pass
    else: return 7

    # Create Vehicle Data into DB
    if generateVehicles(self.chat_id, owner_api_access_token): pass
    else: return 8
    
    return 0


  def verify(self, access_token = None):
    if access_token:
      if verifyConn(access_token): return True

    elif self.access_token:
      if verifyConn(self.access_token): return True

    return False

'''
def fnWakeUp(token):
	print('******************** fnWakeUp() initiated. ********************') #Debug
	try:
		for i in _vehicles(token, 200):
			if i['state'] == 'online': pass
			elif 'asleep':
				if _wakeUp(i['id']): pass
				else:
					print('fnWakeUp(): Wake up Failed.') #Debug
					return False
			else:
				print('fnWakeUp(): Vehicle Connection Error.', i['state']) #Debug
				return False
		return True
	except:
		print('fnWakeUp(): Exception error that occurred in the TRY syntax.')
		return False

def fnStatus():
	print('******************** fnStatus() initiated. ********************') #Debug
	try:
		for i in _vehicles(200):
			vid = i['id']
			state = i['state']
			name = i['display_name']
			print(vid, name, state)
			if state == 'online':
				if _chrgState(vid) == None:
					print('fnStatus(): Failed to check the charging status.')
				elif 'Disconnected':
					print('fnStatus(): Disconnected.')
				elif 'Charging':
					print('fnStatus(): Already Charging.')
				elif 'NoPower':
					print('fnStatus(): NoPower.')
					#bot.send_message(chat_id = 1704527105, text = '[경부하 충전 시간 알리미]\n오후 11시부터 경부하 전력 시간대입니다.\n충전 대기 중인 차량의 충전을 시작해주세요.')
					print('fnStatus(): [Telegram] Sent a message successfully.')
			elif 'asleep':
				main()
				break
			else:
				print('fnStatus(): Vehicle Connection Error.', state)
				#bot.send_message(chat_id = 1704527105, text = '[경부하 충전 시간 알리미]\n차량과의 연결에 실패했습니다.\n로그를 확인하시기 바랍니다.')
	except:
		print('fnStatus(): Exception error that occurred in the TRY syntax.')

def main():
	print('******************** main() initiated. ********************') #Debug
	for i in range(0, 4):
		if fnWakeUp():
			fnStatus()
			return True
		else: continue
	print('main(): fnWakeUp Return False.')
	#bot.send_message(chat_id = 1704527105, text = '[경부하 충전 시간 알리미]\n차량을 깨울 수 없습니다.\n로그를 확인하시기 바랍니다.')
	return False

'''