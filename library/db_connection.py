__author__ = 'sobhagya'

import MySQLdb

# WMS DB Connection present on local system.
db = MySQLdb.connect(host="127.0.0.1" ,port=3306, user="root",  passwd="Hash33##", db="wms")
cursor = db.cursor()

# RMS DB Connection
db_rms = MySQLdb.connect(host="127.0.0.1" ,port=3313, user="mg7011IU",  passwd="m@1107#g", db="rms")
cursor_rms = db_rms.cursor()
