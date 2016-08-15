__author__ = 'sobhagya'

import sys
import warnings
sys.path.append('/var/www/html/wms/')
from datetime import date, timedelta
from library.db_connection import *
from library.html_data_creation import *
from library.mail_file import *

warnings.filterwarnings("ignore", "Unknown table.*")

FILE_NAME = 'Summary Reports'

TODAY_MINUS_SEVEN_DAYS = (date.today() - timedelta(days=7)).strftime('%d-%m-%Y')
TODAY_MINUS_ONE_DAY = (date.today() - timedelta(days=1)).strftime('%d-%m-%Y')

#html_data = '<html><head><meta http-equiv="content-type" content="text/html; charset=utf-8" /></head><body>'

html_data = '<br><h2>Reports from ' + TODAY_MINUS_SEVEN_DAYS + ' to ' + TODAY_MINUS_ONE_DAY + '</h2>'

############## Creating Temp RPR Table ###########
query = """ DROP TABLE IF EXISTS `tmp_rpr`; """
cursor.execute(query)
db.commit()

query = """
        CREATE TABLE `tmp_rpr` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `barcode` varchar(50) NOT NULL,
          `rpr_date_time` datetime NOT NULL,
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8
"""
cursor.execute(query)
db.commit()


############ Select RPR and Insert into the WMS ########
query = """
        SELECT
            cri.code, CAST(crph.created AS char)
        FROM
            rms.customer_returned_item cri
                JOIN
            rms.customer_returned_package crp ON crp.id = cri.crp_id
                JOIN
            rms.crp_history crph ON crph.crp_id = crp.id
        WHERE
            crph.next_status_code = 'RPR'
            AND crph.previous_status_code <> 'RPR'
            AND crph.created BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE()
            AND cri.code is not null;
"""

cursor_rms.execute(query)
data_rms = cursor_rms.fetchall()

if len(data_rms) > 1:
    data_rms = str(data_rms)
    data_rms = data_rms[1:len(data_rms)-1]
else:
    data_rms = str(data_rms)
    data_rms = data_rms[1:len(data_rms)-2]

query = """ INSERT INTO tmp_rpr (barcode, rpr_date_time) VALUES """ + data_rms

cursor.execute(query)
db.commit()


############# RPI #######################
query = """
        SELECT A.date,
            COALESCE(A.total_rpi,0) AS total_rpi,
            COALESCE(B.total_rpr,0) AS total_rpr,
            COALESCE(C.total_qc,0) AS total_qc FROM
        (
            (SELECT DATE(created) AS DATE, COUNT(*) AS total_rpi FROM customer_returned_package WHERE
                created BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE()
                GROUP BY 1
            ) A

            LEFT JOIN (SELECT DATE(created) AS DATE, COUNT(*) AS total_rpr FROM crp_history
                WHERE next_status_code = 'RPR' AND previous_status_code <> 'RPR' AND
                created BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE()
                GROUP BY 1
            ) B ON A.date = B.date

            LEFT JOIN (SELECT DATE(created) AS DATE, COUNT(*) AS total_qc FROM cri_history
                WHERE next_status_code = 'PDC' AND previous_status_code <> 'PDC' AND
                created BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE()
                GROUP BY 1
            ) C ON A.date = C.date
        )
"""
cursor_rms.execute(query)
data = cursor_rms.fetchall()


query = """
        SELECT
            COALESCE(A.putaway,0) AS 'Total Putaway',
            COALESCE(A.liquidate,0) AS '45 days hold',
            COALESCE(A.non_faulty,0) AS 'SOI-Non Faulty',
            COALESCE(A.courier_debit,0) AS 'Courier Debit',
            COALESCE(B.returns,0) AS 'Total Dispatch'
        FROM
        (
            (SELECT DATE(inv.created) AS DATE,
            COUNT(DISTINCT inv.id) AS putaway ,
            COUNT(DISTINCT CASE WHEN ru.rule_name LIKE ('Liquidate%')  THEN inv.id END) AS 'liquidate',
            COUNT(DISTINCT CASE WHEN ru.rule_name LIKE ('%Non Faulty%') THEN inv.id END) AS 'non_faulty',
            COUNT(DISTINCT CASE WHEN bur.rule_name LIKE ('%Courier Debit%') THEN inv.id END) AS 'courier_debit'
            FROM wms.inventory inv
            LEFT JOIN wms.rules ru ON ru.id = inv.rule_id AND inv.is_bulk_rule <> 1
            LEFT JOIN wms.bulk_upload_rules bur ON bur.id = inv.rule_id AND inv.is_bulk_rule = 1
            WHERE inv.created BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE()
                GROUP BY 1
            ) A

            LEFT JOIN (SELECT DATE(rtv.updated) AS DATE, COUNT(DISTINCT inv.id) AS RETURNS
            FROM wms.rtv_sheet_detail rtv
            JOIN wms.rtv_sheet_detail_inventory rts ON rts.rtv_sheet_detail_id = rtv.id
            JOIN wms.inventory inv ON inv.id = rts.productDetails_id
            WHERE rtv.updated BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE() AND inv.status = 'RTV'
                GROUP BY 1
            ) B ON A.date = B.date
        );
"""
cursor.execute(query)
data2 = cursor.fetchall()

result = []

i = 0
for row in data:
    new_row = row + data2[i]
    result.append(new_row)
    i += 1

header = ['Date', 'Total RPI', 'Total Returns Received', 'Total QC', 'Total Putaway', '45 days hold', 'SOI-Non Faulty', 'Courier Debit', 'Total Dispatch']
html_data += '<br><br><strong>Total RPI and RPR and Putaway Report.</strong><br>'
html_data += html_table_data_append(result, header)


############## RPR ######################
query = """
        SELECT A.date,
            COALESCE(A.total_rpr,0) AS total_rpr,
            COALESCE(A.total_qc,0) AS total_qc,
            COALESCE(A.qc,0) AS '%_qc'
            FROM
        (
            (SELECT DATE(crph.created) AS DATE,
                COUNT(*) AS total_rpr,
                COUNT(CASE WHEN crih.status_date IS NOT NULL THEN cri.crp_id END) AS total_qc,
                ROUND(COUNT(CASE WHEN crih.status_date IS NOT NULL THEN cri.crp_id END)/COUNT(*)*100,0) AS qc
            FROM rms.crp_history crph
                JOIN rms.customer_returned_item cri ON cri.crp_id = crph.crp_id
                LEFT JOIN rms.cri_history crih ON crih.cri_id = cri.id AND crih.next_status_code = 'PDC' AND crih.previous_status_code <> 'PDC'
            WHERE crph.next_status_code = 'RPR' AND crph.previous_status_code <> 'RPR' AND
                crph.created BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE()
                GROUP BY 1
            ) A
        );
"""
cursor_rms.execute(query)
data = cursor_rms.fetchall()

query = """
        SELECT
            COALESCE(A.putaway,0) AS 'Total Putaway',
            COALESCE(A.liquidate,0) AS '45 days hold',
            COALESCE(A.non_faulty,0) AS 'SOI-Non Faulty',
            COALESCE(A.courier_debit,0) AS 'Courier Debit',
            COALESCE(A.returns,0) AS 'Total Returns',
            COALESCE(A.rtv_per,0) AS '%_rtv'
        FROM
        (
                (SELECT DATE(rpr.rpr_date_time) AS DATE,
                        COUNT(DISTINCT inv.id) AS putaway ,
                        COUNT(DISTINCT CASE WHEN ru.rule_name LIKE ('Liquidate%')  THEN inv.id END) AS 'liquidate',
                        COUNT(DISTINCT CASE WHEN ru.rule_name LIKE ('%Non Faulty%') THEN inv.id END) AS 'non_faulty',
                        COUNT(DISTINCT CASE WHEN bur.rule_name LIKE ('%Courier Debit%') THEN inv.id END) AS 'courier_debit',
                        COUNT(CASE WHEN inv.status = 'RTV' THEN inv.id END) AS 'returns',
                        ROUND(COUNT(CASE WHEN inv.status = 'RTV' THEN inv.id END)/COUNT(rpr.id)*100,0) AS rtv_per
                    FROM wms.tmp_rpr rpr
                        LEFT JOIN wms.inventory inv ON rpr.barcode = inv.barcode
                        LEFT JOIN wms.rules ru ON ru.id = inv.rule_id AND inv.is_bulk_rule <> 1
                        LEFT JOIN wms.bulk_upload_rules bur ON bur.id = inv.rule_id AND inv.is_bulk_rule = 1
                    GROUP BY 1
            ) A
        );
"""
cursor.execute(query)
data2 = cursor.fetchall()

result = []

i = 0
for row in data2:
    new_row = data[i] + row
    result.append(new_row)
    i += 1

header = ['Date', 'Total Returns Received',	'Total QC', '%_QC/RPR', 'Total Putaway', '45 days hold', 'SOI-Non Faulty', 'Courier Debit', 'Total Dispatch', '%_Dispatch']
html_data += '<br><br><strong>Total RPR Report.</strong><br>'

html_data += html_table_data_append(result, header)


############## Warehouse wise Report ##################

from warehouse_wise_summary_report import *
html_data += warehouse_wise_data


######## QC to RTS Summary ###############
query = """
        SELECT (CASE WHEN crp.updated_by IN ('sharma.mohit@snapdeal.com','customer','sdrlmainqc@snapdeal.com','ankit.verma@snapdeal.com') THEN 'Delhi SD WH'
                WHEN crp.updated_by in ('sdrlblrqc@snapdeal.com') or (crp.updated_by in ('avijit.basu@snapdeal.com') and crp.returns_center_code = 'RMS-NUVO-BANG') THEN 'Bang WH'
                WHEN crp.updated_by in ('sdrldelqc@snapdeal.com') or (crp.updated_by = 'avijit.basu@snapdeal.com' AND crp.returns_center_code IN ('RMS-DEL','RMS-NUVO-DEL')) THEN 'Delhi Nuvo WH'
                WHEN crp.updated_by in ('beta.sahoo@snapdeal.com','sdrlhydqc@snapdeal.com') THEN 'Hyd WH'
                WHEN crp.updated_by in ('naresh.babu@snapdeal.com','sdrlmumqc@snapdeal.com') THEN 'Mum WH'
                when crp.updated_by in ('sdrlchnqc@snapdeal.com') THEN 'Chn WH'
                ELSE crp.updated_by END) AS 'QC Warehouse',
            COUNT(crp.id) AS 'Total QC',
            COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) <=1 THEN crp.id END) AS '1Day',
            ROUND(COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) <=1 THEN crp.id END)/COUNT(crp.id)*100,1.0) AS '(%)1 day',

            COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) <=2 THEN crp.id END) AS '2Day',
            ROUND(COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) <=2 THEN crp.id END)/COUNT(crp.id)*100,1.0) AS '(%)2 day',
            COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) <=3 THEN crp.id END) AS '3Day',
            ROUND(COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) <=3 THEN crp.id END)/COUNT(crp.id)*100,1.0) AS '(%)3 day',
            COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) <=5 THEN crp.id END) AS '5Day',
            ROUND(COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) <=5 THEN crp.id END)/COUNT(crp.id)*100,1.0) AS '(%)5 day',

            COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) >5 THEN crp.id END) AS '>5Day',
            ROUND(COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) >5 THEN crp.id END)/COUNT(crp.id)*100,1.0) AS '(%)>5 day'

        FROM rms.customer_returned_item cri
        JOIN rms.customer_complaint cc ON cc.id = cri.cc_id
        JOIN rms.customer_returned_package crp ON crp.id = cri.crp_id
        JOIN rms.cri_history crih ON crih.cri_id = cri.id AND crih.next_status_code <> crih.previous_status_code AND crih.next_status_code = 'PDC'
        JOIN rms.crp_history crph ON crph.crp_id = crp.id AND crph.next_status_code <> crph.previous_status_code AND crph.next_status_code = 'RPR'
        WHERE crih.status_date BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE()

        GROUP BY 1
        UNION
        SELECT 'Total' AS 'QC Warehouse' ,
            COUNT(crp.id) AS 'Total QC',
            COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) <=1 THEN crp.id END) AS '1Day',
            ROUND(COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) <=1 THEN crp.id END)/COUNT(crp.id)*100,1.0) AS '(%)1 day',

            COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) <=2 THEN crp.id END) AS '2Day',
            ROUND(COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) <=2 THEN crp.id END)/COUNT(crp.id)*100,1.0) AS '(%)2 day',
            COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) <=3 THEN crp.id END) AS '3Day',
            ROUND(COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) <=3 THEN crp.id END)/COUNT(crp.id)*100,1.0) AS '(%)3 day',
            COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) <=5 THEN crp.id END) AS '5Day',
            ROUND(COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) <=5 THEN crp.id END)/COUNT(crp.id)*100,1.0) AS '(%)5 day',

            COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) >5 THEN crp.id END) AS '>5Day',
            ROUND(COUNT(CASE WHEN DATEDIFF(crih.status_date, crph.created) >5 THEN crp.id END)/COUNT(crp.id)*100,1.0) AS '(%)>5 day'

        FROM rms.customer_returned_item cri
        JOIN rms.customer_complaint cc ON cc.id = cri.cc_id
        JOIN rms.customer_returned_package crp ON crp.id = cri.crp_id
        JOIN rms.cri_history crih ON crih.cri_id = cri.id AND crih.next_status_code <> crih.previous_status_code AND crih.next_status_code = 'PDC'
        JOIN rms.crp_history crph ON crph.crp_id = crp.id AND crph.next_status_code <> crph.previous_status_code AND crph.next_status_code = 'RPR'
        WHERE crih.status_date BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE()
        GROUP BY 1
        ORDER BY 2;
"""

cursor_rms.execute(query)
data_rms = cursor_rms.fetchall()

header = []
for row in cursor_rms.description:
    header.append(row[0].title())

html_data += '<br><br><strong>Please find RPR to QC Report.</strong><br>'
html_data += html_table_data_append(data_rms, header)


######## Summary RPR to RTS Report############
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
html_data += '<br><br><strong>Please find RPR To RTS Report.</strong><br>'

html_data += html_table_data_append(data, header)


############## Courier Wise RTV ######################
query = """
         SELECT (CASE WHEN rtv.courier_code LIKE 'DTDC%' THEN 'DTDC'
            WHEN rtv.courier_code LIKE 'JV%' THEN 'JV'
            WHEN rtv.courier_code LIKE 'Gati%' THEN 'Gati'
            WHEN rtv.courier_code LIKE 'Delhivery%' THEN 'Delhivery'
            WHEN rtv.courier_code LIKE 'SAP%' THEN 'SAP'
            WHEN rtv.courier_code LIKE 'Delhidart%' THEN 'Delhidart'
            ELSE rtv.courier_code
            END) AS 'Courier',
            COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 1 DAY THEN inv.id ELSE 0 END) AS 'Yest',
            COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 2 DAY THEN inv.id ELSE 0 END) AS 'Yest - 1 days',
            COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 3 DAY THEN inv.id ELSE 0 END) AS 'Yest - 2 days',
            COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 4 DAY THEN inv.id ELSE 0 END) AS 'Yest - 3 days',
            COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 5 DAY THEN inv.id ELSE 0 END) AS 'Yest - 4 days',
            COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 6 DAY THEN inv.id ELSE 0 END) AS 'Yest - 5 days',
			COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 7 DAY THEN inv.id ELSE 0 END) AS 'Yest - 6 days'

        FROM wms.rtv_sheet_detail rtv
        JOIN wms.rtv_sheet_detail_inventory rts ON rts.rtv_sheet_detail_id = rtv.id
        JOIN wms.inventory inv ON inv.id = rts.productDetails_id
        WHERE rtv.created BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE() AND inv.status = 'RTV'
        GROUP BY 1
        UNION
        SELECT 'Total' AS 'Courier',
            COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 1 DAY THEN inv.id ELSE 0 END) AS 'Yest',
            COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 2 DAY THEN inv.id ELSE 0 END) AS 'Yest - 1 days',
            COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 3 DAY THEN inv.id ELSE 0 END) AS 'Yest - 2 days',
            COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 4 DAY THEN inv.id ELSE 0 END) AS 'Yest - 3 days',
            COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 5 DAY THEN inv.id ELSE 0 END) AS 'Yest - 4 days',
            COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 6 DAY THEN inv.id ELSE 0 END) AS 'Yest - 5 days',
			COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 7 DAY THEN inv.id ELSE 0 END) AS 'Yest - 6 days'
        FROM wms.rtv_sheet_detail rtv
        JOIN wms.rtv_sheet_detail_inventory rts ON rts.rtv_sheet_detail_id = rtv.id
        JOIN wms.inventory inv ON inv.id = rts.productDetails_id
        WHERE rtv.created BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE() AND inv.status = 'RTV'
        GROUP BY 1;
"""
cursor.execute(query)
data = cursor.fetchall()

header = []

for row in cursor.description:
    header.append(row[0].title())

html_data += '<br><br><strong>Courier Wise RTV Report.</strong><br>'

html_data += html_table_data_append(data, header)
#html_data += '</body></html>'

# Get email from the DB.
query2 = "select to_email from reports where name ='"+FILE_NAME+"'"
cursor.execute(query2)
data2 = cursor.fetchall()
to_email = data2[0][0]

send_mail_without_file(to_email, html_data)

########## DROP The tmp_rpr table ##########
query = """ DROP TABLE IF EXISTS `tmp_rpr`; """
cursor.execute(query)
db.commit()

db.close()
db_rms.close()