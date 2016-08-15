__author__ = 'sobhagya'

import sys
import datetime
sys.path.append('/var/www/html/wms/')
from library.db_connection import *
from library.file_creation import *
from library.mail_file import *

FILE_NAME = 'Liquidation'

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
        (CASE WHEN bur.id IS NOT NULL THEN  bur.rule_name
        WHEN r.id IS NOT NULL THEN r.rule_name END) AS 'Rule_name',
        inv.suborderCode,
        rts.rtv_sheet_detail_id,
        inv.barcode,
        inv.issueCategory,
        inv.product_name,
        inv.forwardAwbNumber AS 'rpu_waybill no',
        inv.seller_name,
        inv.vendor_code,
        gp.created AS 'Gate Pass Date',
        us.username
        FROM wms.inventory inv
        LEFT JOIN wms.rules r ON r.id = inv.rule_id
        LEFT JOIN wms.rtv_sheet_detail_inventory rts ON rts.productDetails_id = inv.id
        LEFT JOIN wms.rtv_sheet_detail rtv ON rtv.id = rts.rtv_sheet_detail_id
        LEFT JOIN wms.bulk_upload_rules bur ON bur.id = inv.rule_id
        JOIN wms.users us ON us.id = inv.createdBy_id
        LEFT JOIN wms.gate_pass gp ON inv.barcode = gp.barcode
        WHERE inv.created > '2014-10-18' AND (bur.rule_name IN ('Bulk Courier Debit','Return to Customer')
        OR r.rule_name IN ('Liquidate'));
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
            where cri.code ='"""+row[4]+"""';
        """
    cursor_rms.execute(query)
    data_rms = cursor_rms.fetchall()

    if data_rms is not None:
        new_row = []
        new_row.append(row[0])
        new_row.append(row[1])
        new_row.append(data_rms[0][0])
        new_row.append(row[2])
        new_row.append(row[3])
        new_row.append(row[4])
        new_row.append(row[5])
        new_row.append(row[6])
        new_row.append(row[7])
        new_row.append(row[8])
        new_row.append(row[9])
        if row[10] is not None:
            new_row.append('Y')
            new_row.append(row[10])
        else:
            new_row.append('N')
            new_row.append('')
        new_row.append(row[11])
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

header = 'Putaway Date,Rule Name,Ticket Id,Suborder Code,RTV Sheet Detail Id,Barcode,Issue Category,Product Name,RPU WayBill No,Seller Name,' \
         'Vendor Code,Gatepass,Gatepass Date,Username,' \
         'Customer Name,City,State,Mobile,Email,Pincode,Price,Weight\n'

email_data = "Hi<br><br>Please find attached Liquidation File."
file_create_and_mail(result, header, email_data)

db.close()