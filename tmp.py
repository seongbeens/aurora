import csv
import pymysql

conn = pymysql.connect(host = 'localhost', user = 'root', password = 'aurora', db = 'aurora', charset = 'utf8mb4')

# ACCOUNTS #
f = open('accounts.csv', 'r', encoding='utf8')
rd = csv.reader(f)
sql = "INSERT INTO Accounts (telegram_id, nickname, phone, email, banned, token_refresh, token_access, vehicle_counts, default_vehicle) "\
    + "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"

for line in rd:
  print(line)
  cur = conn.cursor()
  cur.execute(sql, (line[0], line[1], line[2], line[3], line[4], line[5], line[6], line[7], line[8]))

conn.commit()
f.close()

# VEHICLES #
f = open('vehicles.csv', 'r', encoding='utf8')
rd = csv.reader(f)
sql = "INSERT INTO Vehicles (telegram_id, vehicle_id, vin, vehicle_name, car_type, trim_badging, efficiency_package, exterior_color, wheel_type, odometer, car_version, latitude, longitude, battery_range, reminder_charge_complete, reminder_charge_time, sentry_schedule_1, sentry_schedule_2, sentry_schedule_3, sentry_schedule_4, sentry_schedule_5) "\
    + "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

for line in rd:
  if line[13] == '' : line[13] = None
  if line[14] == '' : line[14] = None
  if line[15] == '' : line[15] = None
  if line[16] == '' : line[16] = None
  if line[17] == '' : line[17] = None
  if line[18] == '' : line[18] = None
  if line[19] == '' : line[19] = None
  if line[20] == '' : line[20] = None
  print(line)
  cur = conn.cursor()
  cur.execute(sql, (line[0], line[1], line[2], line[3], line[4], line[5], line[6], line[7], line[8], line[9], line[10], line[11], line[12], line[13], line[14], line[15], line[16], line[17], line[18], line[19], line[20]))

conn.commit()
f.close()

conn.close()
