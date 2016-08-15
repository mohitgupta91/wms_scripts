__author__ = 'sobhagya'

import sys
import datetime
sys.path.append('/var/www/html/wms/')
from library.db_connection import *
from library.file_creation import *
from library.mail_file import *

FILE_NAME = 'Putaway Master'

def file_create_and_mail(result, header, email_data):
    today = datetime.datetime.now().strftime('%d_%m_%Y_%H_%M_%S')

    file_name = today+'_'+FILE_NAME+'.csv'
    file_create(result, header, file_name)

    query2 = "select to_email from reports where name ='"+FILE_NAME+"'"
    cursor.execute(query2)
    data = cursor.fetchall()
    to_email = data[0][0]
    send_mail(file_name, to_email, email_data)

query = """
        SELECT inv.created AS 'Putaway Date',
        inv.forwardAwbNumber AS 'rpu_waybill no',
        inv.barcode,
        inv.suborderCode,
        inv.issueCategory,
        (CASE WHEN r.id IS NOT NULL THEN r.rule_name ELSE bur.rule_name END) AS 'Rule name',
        inv.status,
        inv.product_name,
        inv.price,
        rtv.updated AS 'RTV date',
        rtv.courier_code,
        us.username,
        wh.code
        FROM wms.inventory inv
        LEFT JOIN wms.rules r ON r.id = inv.rule_id AND inv.is_bulk_rule <> 1
        LEFT JOIN wms.rtv_sheet_detail_inventory rts ON rts.productDetails_id = inv.id
        LEFT JOIN wms.rtv_sheet_detail rtv ON rtv.id = rts.rtv_sheet_detail_id #and inv.status = 'RTV'
        LEFT JOIN wms.bulk_upload_rules bur ON bur.id = inv.rule_id AND inv.is_bulk_rule = 1
                JOIN wms.users us ON us.id = inv.createdBy_id
                JOIN wms.warehouse wh ON wh.id = inv.warehouse_id
        WHERE inv.created BETWEEN CURDATE() - INTERVAL 1 DAY AND CURDATE()
        GROUP BY 3
        ORDER BY rtv.updated DESC;
"""
cursor.execute(query)
data = cursor.fetchall()

result = []

for row in data:
    query = """SELECT cc.zendesk_ticket_code as ticket_id,
            pd.name,
            pd.city,
            pd.state_code,
            pd.mobile,
            pd.email,
            pd.pincode,
            cri.item_price,
            cri.weight
            FROM customer_returned_package as crp
            JOIN customer_returned_item as cri on crp.id = cri.crp_id
            JOIN customer_complaint as cc on cri.cc_id = cc.id
            JOIN pickup_detail as pd on crp.pickup_detail_id = pd.id
            where cri.code ='"""+row[2]+"""';
        """
    cursor_rms.execute(query)
    data_rms = cursor_rms.fetchall()

    if data_rms is not None:
        new_row = []
        new_row.append(row[0])
        new_row.append(data_rms[0][0])
        new_row.append(row[1])
        new_row.append(row[2])
        new_row.append(row[3])
        new_row.append(row[4])
        new_row.append(row[5])
        new_row.append(row[6])
        new_row.append(row[7])
        new_row.append(row[8])
        new_row.append(row[9])
        new_row.append(row[10])
        new_row.append(row[11])
        new_row.append(row[12])
        new_row.append(data_rms[0][1])
        new_row.append(data_rms[0][2])
        new_row.append(data_rms[0][3])
        new_row.append(data_rms[0][4])
        new_row.append(data_rms[0][5])
        new_row.append(data_rms[0][6])
        new_row.append(data_rms[0][7])
        new_row.append(data_rms[0][8])

        result.append(new_row)
    else:
        result.append(row)

header = 'Putaway Date,Ticket ID,RPU WayBill No,Barcode,Suborder Code,Issue Category,Rule Name,Status,Product Name,Price,' \
         'RTV Date,Courier Code,Username,Warehouse Code,' \
         'Customer Name,City,State,Mobile,Email,Pincode,Price,Weight\n'

email_data = "Hi<br><br>Please find attached Putaway Master Data File."
file_create_and_mail(result, header, email_data)

db.close()