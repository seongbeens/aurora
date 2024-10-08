import pymysql
import configparser
from vars import *

# Enable Logging
errorLogger = logging.getLogger(__name__)
errorLogger.addHandler(ErrorLogHandler)

# Enable MySQL
def connect():
    ini = configparser.ConfigParser()
    ini.read('mysql_config.ini')
    return pymysql.connect(
        host=ini.get('mysql', 'host', fallback='localhost'),
        user=ini.get('mysql', 'user', fallback='root'),
        password=ini.get('mysql', 'password', fallback='root'),
        db=ini.get('mysql', 'db', fallback='aurora'),
        charset=ini.get('mysql', 'charset', fallback='utf8mb4')
    )

def createAccount(chat_id):
  try:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
      "INSERT INTO Accounts SET telegram_id = %s "\
    + "ON DUPLICATE KEY UPDATE date_recreate = current_timestamp", (chat_id))
    conn.commit()
    return True
  
  except Exception as e:
    errorLogger.error('createAccount: ' + str(e), exc_info = False)
    return False
  
  finally:
    conn.close()

def modifyAccount(chat_id, columns, tuples):
  try:
    conn = connect()
    cur = conn.cursor()
    for i, j in zip(columns, tuples):
      cur.execute(
        "UPDATE Accounts SET {} = %s WHERE telegram_id = %s".format(i), (j, chat_id))
    conn.commit()
    return True
  
  except Exception as e:
    errorLogger.error('modifyAccount: ' + str(e), exc_info = False)
    return False
  
  finally:
    conn.close()

def deleteAccount(chat_id):
  if not deleteVehicle(chat_id):
    return False

  try:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
      "UPDATE Accounts SET nickname = NULL, phone = NULL, email = NULL, "\
    + "token_refresh = NULL, token_access = NULL, vehicle_counts = NULL, default_vehicle = NULL "\
    + "WHERE telegram_id = %s", (chat_id))
    conn.commit()
    return True

  except Exception as e:
    errorLogger.error('deleteAccount: ' + str(e), exc_info = False)
    return False
  
  finally:
    conn.close()

def inquiryAccount(chat_id, columns): # 구문 변경
  try:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
      "UPDATE Accounts SET date_recent = current_timestamp WHERE telegram_id = %s", (chat_id))
    conn.commit()
    cur.execute(
      "SELECT {} FROM Accounts ".format(', '.join(columns))\
    + "WHERE telegram_id = %s", (chat_id))
    return cur.fetchone()
  
  except Exception as e:
    errorLogger.error('inquiryAccount: ' + str(e), exc_info = False)
    return False
  
  finally:
    conn.close()

def inquiryAccounts(columns = None): # 함수명 및 구문 변경
  try:
    conn = connect()
    cur = conn.cursor()
    if columns:
      cur.execute(
        "SELECT telegram_id, {} FROM Accounts".format(', '.join(columns)))
    else:
      cur.execute(
        "SELECT telegram_id FROM Accounts")
    return cur.fetchall()
  
  except Exception as e:
    errorLogger.error('inquiryAccounts: ' + str(e), exc_info = False)
    return False
  
  finally:
    conn.close()


def createVehicle(chat_id, veh_id, veh_name, vin):
  try:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
      "INSERT INTO Vehicles SET "\
    + "telegram_id = %s, vehicle_id = %s, vehicle_name = %s, vin = %s "\
    + "ON DUPLICATE KEY UPDATE vehicle_name = %s, vin = %s", (chat_id, veh_id, veh_name, vin, veh_name, vin))
    conn.commit()
    return True

  except Exception as e:
    errorLogger.error('createVehicle: ' + str(e), exc_info = False)
    return False
  
  finally:
    conn.close()

def modifyVehicle(chat_id, veh_id, columns, tuples):
  try:
    conn = connect()
    cur = conn.cursor()
    for i, j in zip(columns, tuples):
      cur.execute(
        "UPDATE Vehicles SET {} = %s ".format(i)\
      + "WHERE telegram_id = %s AND vehicle_id = %s", (j, chat_id, veh_id))
    conn.commit()
    return True
  
  except Exception as e:
    errorLogger.error('modifyVehicle: ' + str(e), exc_info = False)
    return False
  
  finally:
    conn.close()

def deleteVehicle(chat_id, veh_id = None):
  try:
    conn = connect()
    cur = conn.cursor()
    if veh_id:
      cur.execute(
        "DELETE FROM Vehicles "\
      + "WHERE telegram_id = %s AND vehicle_id = %s", (chat_id, veh_id))
    else:
      cur.execute(
        "DELETE FROM Vehicles "\
      + "WHERE telegram_id = %s", (chat_id))
    conn.commit()
    return True
  
  except Exception as e:
    errorLogger.error('deleteVehicle: ' + str(e), exc_info = False)
    return False
  
  finally:
    conn.close()

def inquiryVehicle(chat_id, veh_id, columns):
  try:
    conn = connect()
    cur = conn.cursor()
    if veh_id:
      cur.execute(
        "SELECT {} FROM Vehicles ".format(', '.join(columns))\
      + "WHERE telegram_id = %s AND vehicle_id = %s", (chat_id, veh_id))
      return cur.fetchone()
    else:
      cur.execute(
        "SELECT {} FROM Vehicles ".format(', '.join(columns))\
      + "WHERE telegram_id = %s", (chat_id))
      return cur.fetchall()

  except Exception as e:
    errorLogger.error('inquiryVehicle: ' + str(e), exc_info = False)
    return False
  
  finally:
    conn.close()

def inquiryVehicles(columns = None):
  try:
    conn = connect()
    cur = conn.cursor()
    if columns:
      cur.execute(
        "SELECT telegram_id, vehicle_id, {} FROM Vehicles".format(', '.join(columns)))
    else:
      cur.execute(
        "SELECT telegram_id, vehicle_id FROM Vehicles")
    return cur.fetchall()

  except Exception as e:
    errorLogger.error('inquiryVehicles: ' + str(e), exc_info = False)
    return False

  finally:
    conn.close()


def modifySchedule(chat_id, veh_id, columns, tuples):
  try:
    conn = connect()
    cur = conn.cursor()

    if cur.execute("SELECT * FROM Schedules "\
    + "WHERE telegram_id = %s AND vehicle_id = %s", (chat_id, veh_id)) == 0:
      cur.execute("INSERT INTO Schedules SET telegram_id = %s, vehicle_id = %s", (chat_id, veh_id))
      conn.commit()

    for i, j in zip(columns, tuples):
      cur.execute(
        "UPDATE Schedules SET {} = %s ".format(i)\
      + "WHERE telegram_id = %s AND vehicle_id = %s", (j, chat_id, veh_id))
    conn.commit()
    return True
  
  except Exception as e:
    errorLogger.error('modifySchedule: ' + str(e), exc_info = False)
    return False
  
  finally:
    conn.close()

def inquirySchedule(chat_id, veh_id, columns):
  try:
    conn = connect()
    cur = conn.cursor()
    if veh_id:
      cur.execute(
        "SELECT {} FROM Schedules ".format(', '.join(columns))\
      + "WHERE telegram_id = %s AND vehicle_id = %s", (chat_id, veh_id))
      return cur.fetchone()
    else:
      cur.execute(
        "SELECT {} FROM Schedules ".format(', '.join(columns))\
      + "WHERE telegram_id = %s", (chat_id))
      return cur.fetchall()

  except Exception as e:
    errorLogger.error('inquirySchedule: ' + str(e), exc_info = False)
    return False
  
  finally:
    conn.close()

def inquirySchedules(columns = None):
  try:
    conn = connect()
    cur = conn.cursor()
    if columns:
      cur.execute(
        "SELECT telegram_id, vehicle_id, {} FROM Schedules".format(', '.join(columns)))
    else:
      cur.execute(
        "SELECT telegram_id, vehicle_id FROM Schedules")
    return cur.fetchall()

  except Exception as e:
    errorLogger.error('inquirySchedules: ' + str(e), exc_info = False)
    return False

  finally:
    conn.close()