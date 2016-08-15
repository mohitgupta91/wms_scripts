__author__ = 'sobhagya'

import sys
import datetime
sys.path.append('/var/www/html/wms/')
from datetime import date, timedelta
from library.db_connection import *
from library.file_creation import *
from library.mail_file import *
from library.html_data_creation import *

FILE_NAME = 'RPR To RTS'

TODAY_MINUS_SEVEN_DAYS = (date.today() - timedelta(days=7)).strftime('%d-%m-%Y')
TODAY_MINUS_ONE_DAY = (date.today() - timedelta(days=1)).strftime('%d-%m-%Y')

html_data = '<br><h2>Reports from ' + TODAY_MINUS_SEVEN_DAYS + ' to ' + TODAY_MINUS_ONE_DAY + '</h2>'

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
        SELECT inv.barcode,
            inv.suborderCode,
            inv.issueCategory,
            inv.created AS 'Putaway Date',
            rtv.updated AS 'Dispatch Date',
            (CASE WHEN ru.id IS NOT NULL THEN ru.rule_name ELSE bur.rule_name END) AS 'Rule name',
            u.username,
            wh.code,
            (CASE WHEN u.username = 'sumit.arora@nuvoex.com' AND inv.warehouse_id = 2 THEN 'Delhi WH'
            WHEN inv.warehouse_id = 2 THEN 'Delhi SD WH'
            WHEN inv.warehouse_id = 3 THEN 'Bang WH'
            WHEN inv.warehouse_id = 4 THEN 'Hyd WH'
            WHEN inv.warehouse_id = 5 THEN 'Mum WH'
            ELSE wh.code END) AS 'Warehouse',
            rpr.rpr_date_time
        FROM wms.inventory inv
            LEFT JOIN wms.rules ru ON ru.id = inv.rule_id AND inv.is_bulk_rule <> 1
            LEFT JOIN wms.bulk_upload_rules bur ON bur.id = inv.rule_id AND inv.is_bulk_rule = 1
            JOIN wms.rtv_sheet_detail_inventory rts ON inv.id = rts.productDetails_id
            JOIN wms.rtv_sheet_detail rtv ON rts.rtv_sheet_detail_id = rtv.id
            LEFT JOIN wms.users u ON u.id  = rtv.updatedBy_id
            LEFT JOIN wms.warehouse wh ON wh.id = rtv.warehouse_id
            LEFT JOIN wms.rpr rpr ON inv.barcode = rpr.barcode
        WHERE rtv.updated BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE()
            AND inv.status = 'RTV';
"""
cursor.execute(query)
data = cursor.fetchall()

result = []

for row in data:
    # query = """ SELECT rpr_date_time from rpr WHERE barcode ='""" + row[0] + """';"""
    #
    # cursor.execute(query)
    # wms_data = cursor.fetchall()
    # row_count_wms = cursor.rowcount

    if row[9] is None:
        query = """
            SELECT cri.code, CAST(crph.created AS char) AS 'RPR Date'
                FROM rms.customer_returned_item cri
                JOIN rms.customer_complaint cc ON cc.id  = cri.cc_id
                JOIN rms.customer_returned_package crp ON crp.id  = cri.crp_id
                JOIN rms.crp_history crph ON crph.crp_id = crp.id  AND crph.next_status_code <> crph.previous_status_code AND crph.next_status_code = 'RPR'
            WHERE cri.code ='""" + row[0] + """';
            """
        cursor_rms.execute(query)
        data_rms = cursor_rms.fetchall()

        row_count_rms = cursor_rms.rowcount

        if row_count_rms == 0:
            rpr_date = ''
        else:
            rpr_date = data_rms[0][1]
            if len(data_rms) > 1:
                data_rms = str(data_rms)
                data_rms = data_rms[1:len(data_rms)-1]
            else:
                data_rms = str(data_rms)
                data_rms = data_rms[1:len(data_rms)-2]

            query = """ INSERT INTO rpr (barcode, rpr_date_time) VALUES """ + data_rms

            cursor.execute(query)
            db.commit()

    else:
        rpr_date = row[9]


    new_row = []
    new_row.append(row[1])
    new_row.append(row[2])
    new_row.append(row[3])
    new_row.append(row[4])
    new_row.append(rpr_date)
    new_row.append(row[5])
    new_row.append(row[6])
    new_row.append(row[7])
    new_row.append(row[8])

    result.append(new_row)


######## Summary ############
query = """
        SELECT (CASE WHEN ((u.username IN ('sumit.arora@nuvoex.com','avijit.basu@snapdeal.com') AND inv.warehouse_id = 2)
            OR (u.username IN ('sdrldelqc@snapdeal.com') AND inv.warehouse_id = 7))	 THEN 'Delhi Nuvo WH'
            WHEN u.username NOT IN ('sumit.arora@nuvoex.com','avijit.basu@snapdeal.com') AND inv.warehouse_id = 2 THEN 'Delhi SD WH'
            WHEN inv.warehouse_id = 3 THEN 'Bang WH'
            WHEN inv.warehouse_id = 4 THEN 'Hyd WH'
            WHEN inv.warehouse_id = 5 THEN 'Mum WH'
            WHEN inv.warehouse_id = 10 THEN 'Chn WH'
            ELSE wh.code  END) AS 'WH',
        ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(rtv.updated, rpr.rpr_date_time)<=1 THEN inv.id END)/COUNT(DISTINCT inv.id)*100,1) AS '%1 day',
        ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(rtv.updated, rpr.rpr_date_time)<=2 THEN inv.id END)/COUNT(DISTINCT inv.id)*100,1) AS '%2 day',
        ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(rtv.updated, rpr.rpr_date_time)<=3 THEN inv.id END)/COUNT(DISTINCT inv.id)*100,1) AS '%3 day',
        ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(rtv.updated, rpr.rpr_date_time)<=5 THEN inv.id END)/COUNT(DISTINCT inv.id)*100,1) AS '%5 day',
        ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(rtv.updated, rpr.rpr_date_time) >5 THEN inv.id END)/COUNT(DISTINCT inv.id)*100,1) AS '% >5 day',
        COUNT(DISTINCT inv.id) AS 'Total Dispatch'

        FROM wms.inventory inv
        JOIN wms.rpr rpr ON rpr.barcode = inv.barcode
        JOIN wms.rtv_sheet_detail_inventory rts ON inv.id = rts.productDetails_id
        JOIN wms.rtv_sheet_detail rtv ON rts.rtv_sheet_detail_id = rtv.id
        LEFT JOIN wms.users u ON u.id  = rtv.updatedBy_id
        LEFT JOIN wms.warehouse wh ON wh.id = rtv.warehouse_id
        WHERE rtv.updated BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE() AND inv.status = 'RTV'
        GROUP BY 1
        UNION
        SELECT 'total'  as 'warehouse' ,
        ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(rtv.updated, rpr.rpr_date_time)<=1 THEN inv.id END)/COUNT(DISTINCT inv.id)*100,1) AS '%1 day',
        ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(rtv.updated, rpr.rpr_date_time)<=2 THEN inv.id END)/COUNT(DISTINCT inv.id)*100,1) AS '%2 day',
        ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(rtv.updated, rpr.rpr_date_time)<=3 THEN inv.id END)/COUNT(DISTINCT inv.id)*100,1) AS '%3 day',
        ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(rtv.updated, rpr.rpr_date_time)<=5 THEN inv.id END)/COUNT(DISTINCT inv.id)*100,1) AS '%5 day',
        ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF(rtv.updated, rpr.rpr_date_time) >5 THEN inv.id END)/COUNT(DISTINCT inv.id)*100,1) AS '% >5 day',
        COUNT(DISTINCT inv.id) AS 'Total Dispatch'

        FROM wms.inventory inv
        JOIN wms.rpr rpr ON rpr.barcode = inv.barcode
        JOIN wms.rtv_sheet_detail_inventory rts ON inv.id = rts.productDetails_id
        JOIN wms.rtv_sheet_detail rtv ON rts.rtv_sheet_detail_id = rtv.id
        LEFT JOIN wms.users u ON u.id  = rtv.updatedBy_id
        LEFT JOIN wms.warehouse wh ON wh.id = rtv.warehouse_id
        WHERE rtv.updated BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE() AND inv.status = 'RTV'
        ORDER BY 7;
"""

cursor.execute(query)
data = cursor.fetchall()

header = ['Warehouse', '%1 day', '%2 day', '%3 day', '%5 day', '% >5 day', 'Total Dispatch']
html_data += '<br><br>Please find RPR To RTS Report.</strong><br>'

html_data += html_table_data_append(data, header)


header = 'Suborder Code,Issue Category,Putaway Date,Dispatch Date,QC Date,Rule Name,Username,Warehouse Code,Warehouse\n'
file_create_and_mail(result, header, html_data)

db.close()