import pandas as pd
from vars import *

# Enable Logging
errorLogger = logging.getLogger(__name__)
errorLogger.addHandler(ErrorLogHandler)

# ACCOUNTS.CSV
def createAccount(chat_id):
	try:
		df = pd.read_csv('accounts.csv', dtype = 'str')
		df = df.loc[(df['telegram_id'] != str(chat_id))]
		df.append({'telegram_id': str(chat_id)}, ignore_index = True)\
		.to_csv('accounts.csv', index = False)
		return True
	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def modifyAccount(chat_id, columns, tuples):
	try:
		df = pd.read_csv('accounts.csv', dtype = 'str')
		# Check Incorrect Column
		if 'telegram_id' in columns: return False
		else: # Verified Correct Column
			for i, j in zip(columns, tuples):
				df.loc[(df['telegram_id'] == str(chat_id)), i] = str(j)
			df.to_csv('accounts.csv', index = False)
			return True
	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def deleteAccount(chat_id):
	def _deleteVehicle(chat_id):
		try:
			df = pd.read_csv('vehicles.csv', dtype = 'str')
			df = df.loc[~(df['telegram_id'] == str(chat_id))]
			df.to_csv('vehicles.csv', index = False)
			return True
		except Exception as e:
			errorLogger.critical(e, exc_info = False)
			return False
	
	try:
		if _deleteVehicle(chat_id):
			df = pd.read_csv('accounts.csv', dtype = 'str')
			if pd.notnull(df.loc[(df['telegram_id'] == str(chat_id)), 'banned']).values.any():
				_banned = df.loc[(df['telegram_id'] == str(chat_id)), 'banned'].values[0]
			else: _banned = '0'
			df = df.loc[~(df['telegram_id'] == str(chat_id))]
			df.append({'telegram_id': str(chat_id), 'banned' : str(_banned)}, ignore_index = True)\
			.to_csv('accounts.csv', index = False)
			return True
		else: return False
	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def inquiryAccount(chat_id, column):
	try:
		df = pd.read_csv('accounts.csv', dtype = 'str')
		if pd.notnull(df.loc[(df['telegram_id'] == str(chat_id)), column]).values.any():
			return df.loc[(df['telegram_id'] == str(chat_id)), column].values[0]
		else: return False
	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def inquiryAccount_whole(column):
	try:
		df = pd.read_csv('accounts.csv', dtype = 'str')
		return df.loc[:, column].drop_duplicates().values
	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False


# VEHICLES.CSV
def createVehicle(chat_id, veh_id, vin, name):
	try:
		df = pd.read_csv('vehicles.csv', dtype = 'str')
		df = df.loc[~((df['telegram_id'] == str(chat_id)) & (df['vehicle_id'] == str(veh_id)))]
		df.append({
			'telegram_id': str(chat_id),
			'vehicle_id': str(veh_id),
			'vin': str(vin),
			'veh_name': str(name)
			}, ignore_index = True)\
		.to_csv('vehicles.csv', index = False)
		return True
	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def modifyVehicle(chat_id, veh_id, columns, tuples):
	try:
		df = pd.read_csv('vehicles.csv', dtype = 'str')
		# Check Incorrect Column
		if ('telegram_id' or 'vehicle_id') in columns: return False
		else: # Verified Correct Column
			for i, j in zip(columns, tuples):
				df.loc[((df['telegram_id'] == str(chat_id)) & (df['vehicle_id'] == str(veh_id))), i] = str(j)
			df.to_csv('vehicles.csv', index = False)
			return True
	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def inquiryVehicle(chat_id, column, veh_id = None):
	try:
		df = pd.read_csv('vehicles.csv', dtype = 'str')
		if veh_id:
			if pd.notnull(df.loc[((df['telegram_id'] == str(chat_id)) & (df['vehicle_id'] == str(veh_id))), column]).values.any():
				return df.loc[((df['telegram_id'] == str(chat_id)) & (df['vehicle_id'] == str(veh_id))), column].values[0]
			else: return False
		else:
			if pd.notnull(df.loc[(df['telegram_id'] == str(chat_id)), column]).values.any():
				return df.loc[(df['telegram_id'] == str(chat_id)), column].values
			else: return False
	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False

def inquiryVehicle_whole(column):
	try:
		df = pd.read_csv('vehicles.csv', dtype = 'str')
		return df.loc[:, column].drop_duplicates().values
	except Exception as e:
		errorLogger.critical(e, exc_info = False)
		return False
