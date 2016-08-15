__author__ = 'sobhagya'

import sys
sys.path.append('/var/www/html/wms/')
from datetime import date, timedelta
from library.db_connection import *
from library.html_data_creation import *
from library.mail_file import *

FILE_NAME = 'Email To Center'

# Get Constant Email Address from the DB.
query2 = "select to_email from reports where name ='"+FILE_NAME+"'"
cursor.execute(query2)
data = cursor.fetchall()

constant_email = data[0][0]

query_vendors = """ SELECT distinct rd.name AS 'Seller_Name'
                FROM rtv_sheet_detail rtv
                    JOIN rtv_sheet_detail_inventory rtvi ON rtvi.rtv_sheet_detail_id = rtv.id
                    JOIN inventory inv ON rtvi.productDetails_id = inv.id
                    JOIN manifest_rtv_sheet_detail mr ON mr.rtvSheet_id = rtv.id
                    JOIN manifest m ON m.id = mr.manifest_id
                    JOIN receiver_detail rd ON rd.id = rtv.receiverDetail_id
                WHERE m.created BETWEEN CURDATE() - INTERVAL 1 DAY AND NOW()
                    AND rtv.return_warehouse = 1;
"""
cursor.execute(query_vendors)
vendors = cursor.fetchall()

for seller in vendors:
    query = """ SELECT inv.barcode AS 'Barcode',
                    inv.ticket_id AS 'Ticket_Id',
                    inv.suborderCode AS 'Subordercode',
                    inv.order_code AS 'order_code',
                    inv.forwardAwbNumber AS 'Forwardawbnumber',
                    inv.product_name AS 'Product_Name',
                    inv.issueCategory AS 'Issuecategory',
                    inv.seller_name AS 'Seller_Name',
                    rd.name AS 'Soi Center Name',
                    rtv.courier_code AS 'Dispatch_Courier',
                    rtv.awb_number AS 'Dispatch_Waybill No',
                    DATE_FORMAT(rtv.created,'%d-%b-%y') AS 'Dispatch Date'
            FROM rtv_sheet_detail rtv
                JOIN rtv_sheet_detail_inventory rtvi ON rtvi.rtv_sheet_detail_id = rtv.id
                JOIN inventory inv ON rtvi.productDetails_id = inv.id
                JOIN manifest_rtv_sheet_detail mr ON mr.rtvSheet_id = rtv.id
                JOIN manifest m ON m.id = mr.manifest_id
                JOIN receiver_detail rd ON rd.id = rtv.receiverDetail_id
            WHERE m.created BETWEEN CURDATE() - INTERVAL 1 DAY AND NOW()
                AND rtv.return_warehouse = 1 and rd.name = '""" + str(seller[0]).replace("'","\\'") + """';
    """

    cursor.execute(query)
    data = cursor.fetchall()
       
    header = []

    for col in cursor.description:
        header.append(col[0].title())

    # for row in data:
    html_data = """Dear Partner, <br><br>
    Please note we have received below complaints from our customers, so we are sending the same back to you. <br><br>
    Please let us know if you require any support from our side. <br><br>
    Note :- kindly acknowledge the receipt of product within 7 working day else it will consider as accepted <br>
    for any query kindly mark mail to rts@snapdeal.com <br>
    """

    # result = []
    # result.append(row)
    html_data += html_table_data_append(data, header)
    
    # Get email from the DB.
    query2 = """SELECT COALESCE(rd.email,''),COALESCE(re.email,'')
                FROM receiver_detail rd
                    JOIN rtv_sheet_detail rtv ON rtv.receiverDetail_id = rd.id
                    JOIN rtv_sheet_detail_inventory rtvi ON rtvi.rtv_sheet_detail_id = rtv.id
                    JOIN inventory inv ON rtvi.productDetails_id = inv.id
                    LEFT JOIN receiver_email re ON rd.name = re.code
                WHERE inv.ticket_id =  '""" + str(data[0][1]) + """' order by rd.id desc limit 1;
    """
    cursor.execute(query2)
    data2 = cursor.fetchall()

    subject = 'Customer Complaint Product'

    row_count = cursor.rowcount

    if row_count != 0:
        to_email = data2[0][0]
        if data2[0][1] != '':
            to_email += "," + data2[0][1]
        if constant_email != '':
            to_email += "," + constant_email
        # to_email = 'mohit.gupta@snapdeal.com'
        send_mail_without_file_subject(to_email, html_data, subject)
