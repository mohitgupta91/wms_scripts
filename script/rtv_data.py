__author__ = 'sobhagya'

import sys
import datetime
sys.path.append('/var/www/html/wms/')
from library.db_connection import *
from library.file_creation import *
from library.mail_file import *

FILE_NAME = 'RTV Data'

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
        SELECT rtv.created AS 'RTV date',
        rts.rtv_sheet_detail_id,
        inv.suborderCode,
        inv.barcode,
        inv.product_name,
        inv.issueCategory,
        inv.seller_name,
        inv.vendor_code,
        inv.price,
        inv.created AS 'Putaway Date',
        inv.forwardAwbNumber AS 'rpu_waybill no',
        inv.manifestDate,
        rtv.courier_code AS 'RTV_courier',
        rtv.awb_number AS 'RTV_waybill no',
        us.username,
        wh.code
        FROM wms.rtv_sheet_detail rtv
    JOIN wms.rtv_sheet_detail_inventory rts ON rts.rtv_sheet_detail_id = rtv.id
    JOIN wms.inventory inv ON inv.id = rts.productDetails_id
    JOIN wms.warehouse wh ON wh.id = rtv.warehouse_id
    LEFT JOIN wms.users us ON us.id = rtv.updatedBy_id
    WHERE rtv.updated BETWEEN NOW() - INTERVAL 7 DAY AND NOW() AND rtv.courier_code IS NOT NULL
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
            where cri.code ='"""+row[3]+"""';
        """
    cursor_rms.execute(query)
    data_rms = cursor_rms.fetchall()

    if data_rms is not None:
        new_row = []
        new_row.append(row[0])
        new_row.append(row[1])
        new_row.append(data_rms[0][0])
        new_row.append(row[2])
        new_row.append(data_rms[0][1])
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
        new_row.append(row[13])
        new_row.append(row[14])
        new_row.append(row[15])
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

header = 'RTV date,RTV Sheet Detail Id,Ticket Id,Suborder Code,Customer Name,Barcode,' \
         'Product Name,Issue Category,Seller Name,Vendor Code,Price,Putaway Date,RPU WayBill No,' \
         'Manifest Date,RTV Courier,RTV WayBill No,Username,Warehouse Code,' \
         'City,State,Mobile,Email,Pincode,Price,Weight\n'

email_data = "Hi<br><br>Please find attached RTV Data File."
file_create_and_mail(result, header, email_data)

db.close()
