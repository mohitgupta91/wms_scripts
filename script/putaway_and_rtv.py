__author__ = 'sobhagya'

import sys
sys.path.append('/var/www/html/wms/')
from library.db_connection import *
from library.mail_data_creation_and_send import *

FILE_NAME = 'Putaway and RTV'

query = """
        SELECT DATE(inv.created) AS 'Putaway_Date',
            COUNT(DISTINCT inv.id) AS 'total_putaway',
            COUNT(DISTINCT rtv.id) AS 'total_rtv_initiated',
            COUNT(DISTINCT CASE WHEN inv.status = 'RTV' THEN rtv.id END) AS 'total_rtv_completed',
            COUNT(DISTINCT rtv.id) - COUNT(DISTINCT CASE WHEN inv.status = 'RTV' THEN rtv.id END) as pending
        FROM wms.inventory inv
        LEFT JOIN wms.rtv_sheet_detail_inventory rts ON rts.productDetails_id = inv.id
        LEFT JOIN  wms.rtv_sheet_detail rtv ON rtv.id = rts.rtv_sheet_detail_id
        WHERE inv.created BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE()
        GROUP BY 1
"""
cursor.execute(query)
data = cursor.fetchall()

header = ['Date', 'Putaway','RTV Initiated','RTV Completed','Pending']
email_data = 'Hi<br><br><strong>Please find putaway, rtv initiated, rtv completed and pending.</strong><br>'


# Get email from the DB.
query2 = "select to_email from reports where name ='"+FILE_NAME+"'"
cursor.execute(query2)
data2 = cursor.fetchall()
to_email = data2[0][0]

html_table_data_append_and_mail(data, header, email_data, to_email)

db.close()