__author__ = 'sobhagya'

import sys
sys.path.append('/var/www/html/wms/')
from datetime import date, timedelta
from library.db_connection import *
from library.html_data_creation import *
from library.mail_file import *

FILE_NAME = 'Warehouse Wise Summary Reports'

TODAY_MINUS_SEVEN_DAYS = (date.today() - timedelta(days=7)).strftime('%d-%m-%Y')
TODAY_MINUS_ONE_DAY = (date.today() - timedelta(days=1)).strftime('%d-%m-%Y')

warehouse_wise_data = ''

########## Conditions for different warehouses ###########
cd_wh = [["Delhi SD WH", "crp.updated_by IN ('sharma.mohit@snapdeal.com','customer','sdrlmainqc@snapdeal.com','ankit.verma@snapdeal.com')",
              "u.username NOT IN ('sumit.arora@nuvoex.com','avijit.basu@snapdeal.com') AND inv.warehouse_id = 2"],
         ["Delhi Nuvo WH", "crp.updated_by in ('sdrldelqc@snapdeal.com') or (crp.updated_by = 'avijit.basu@snapdeal.com' AND crp.returns_center_code IN ('RMS-DEL','RMS-NUVO-DEL'))",
          "((u.username IN ('sumit.arora@nuvoex.com','avijit.basu@snapdeal.com') AND inv.warehouse_id = 2) OR (u.username IN ('sdrldelqc@snapdeal.com') AND inv.warehouse_id = 7))"],
         ["Bang WH", "crp.updated_by in ('sdrlblrqc@snapdeal.com') or (crp.updated_by in ('avijit.basu@snapdeal.com') and crp.returns_center_code = 'RMS-NUVO-BANG')",
          "inv.warehouse_id = 3"],
         ["Hyd WH", "crp.updated_by in ('beta.sahoo@snapdeal.com','sdrlhydqc@snapdeal.com')",
          "inv.warehouse_id = 4"],
         ["Mum WH", "crp.updated_by in ('naresh.babu@snapdeal.com','sdrlmumqc@snapdeal.com')",
          "inv.warehouse_id = 5"],
         ["Chn WH", "crp.updated_by in ('sdrlchnqc@snapdeal.com')",
          "inv.warehouse_id = 10"]]


email_cd_wh = ["Delhi Nuvo WH", "Bang WH", "Mum WH"]
email_wh = "navneet.singh@nuvoex.com, sumit.arora@nuvoex.com, priyank.kaushik@nuvoex.com, rohit.bhatt@nuvoex.com, sandeep.bhatt@nuvoex.com, ayush.goel@nuvoex.com"


########### Remove first column from object ##########
def remove_first_column(data):
    new_data = tuple()

    i = 0
    for col in data:
        if i == 0:
            i += 1
        else:
            new_data = new_data + (col,)

    return new_data


############# Combine two list into one ###############
def get_combine_list(data1, data2):
    result = []
    n1 = len(data1)
    n2 = len(data2)

    i = j = 0

    while i < n1 and j < n2:
        if data1[i][0] == data2[j][0]:
            new_row = data1[i] + remove_first_column(data2[j]) + ((data2[j][5]*100)/data1[i][1],) + ((data2[j][1]*100)/data1[i][2],)
            result.append(new_row)
            i += 1
            j += 1
        elif data1[i][0] < data2[j][0]:
            i += 1
        else:
            j += 1

    return result


for cur in cd_wh:
    html_data_warehouse = '<br><h2>Reports from ' + TODAY_MINUS_SEVEN_DAYS + ' to ' + TODAY_MINUS_ONE_DAY + '</h2>'

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
                    JOIN rms.customer_returned_package crp ON crp.id = crph.crp_id
                    LEFT JOIN rms.cri_history crih ON crih.cri_id = cri.id AND crih.next_status_code = 'PDC' AND crih.previous_status_code <> 'PDC'
                WHERE crph.next_status_code = 'RPR' AND crph.previous_status_code <> 'RPR' AND
                    crph.created BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE() AND (""" + cur[1] + """)
                    GROUP BY 1
                ) A
            );
    """
    cursor_rms.execute(query)
    data = cursor_rms.fetchall()

    query = """
           SELECT A.date,
                COALESCE(A.putaway,0) AS 'Putaway',
                COALESCE(A.liquidate,0) AS '45 days hold',
                COALESCE(A.non_faulty,0) AS 'SOI-Non Faulty',
                COALESCE(A.courier_debit,0) AS 'Courier Debit',
                COALESCE(A.returns,0) AS 'Total Returns'
            FROM
            (
                (SELECT DATE(rpr.rpr_date_time) AS DATE,
                    COUNT(inv.id) AS putaway ,
                    COUNT(CASE WHEN ru.rule_name LIKE ('Liquidate%') THEN inv.id END) AS 'liquidate',
                    COUNT(CASE WHEN ru.rule_name LIKE ('%Non Faulty%') THEN inv.id END) AS 'non_faulty',
                    COUNT(CASE WHEN bur.rule_name LIKE ('%Courier Debit%') THEN inv.id END) AS 'courier_debit',
                    COUNT(CASE WHEN inv.status = 'RTV' THEN inv.id END) AS 'returns'

                FROM wms.tmp_rpr rpr
                    LEFT JOIN wms.inventory inv ON rpr.barcode = inv.barcode
                    LEFT JOIN wms.rules ru ON ru.id = inv.rule_id AND inv.is_bulk_rule <> 1
                    LEFT JOIN wms.bulk_upload_rules bur ON bur.id = inv.rule_id AND inv.is_bulk_rule = 1
                    LEFT JOIN wms.users u ON u.id = inv.createdBy_id
                WHERE """ + cur[2] + """
                    GROUP BY 1
                ) A
            );


    """
    cursor.execute(query)
    data2 = cursor.fetchall()

    # result = []

    print cur[0]
    # i = 0
    # for row in data2:
    #     if cursor.rowcount > i:
    #         new_row = data[i] + row
    #     else:
    #         new_row = row
    #     result.append(new_row)
    #     i += 1

    result = get_combine_list(data, data2)

    header = ['Date', 'Total Returns Received',	'Total QC', '%_QC/RPR', 'Putaway', '45 days hold', 'SOI-Non Faulty', 'Courier Debit', 'Total Dispatch', '%_Dispatch', '%_Putaway/QC']
    html_data_warehouse += '<br><br><strong>' + cur[0] + ' Summary Report.</strong><br>'

    html_data_warehouse += html_table_data_append(result, header)

    ######### For Overall Summary Report #########
    warehouse_wise_data += '<br><br><strong>' + cur[0] + ' Summary Report.</strong><br>'
    warehouse_wise_data += html_table_data_append(result, header)

    query = """
       SELECT A.date,
                COALESCE(A.putaway,0) AS 'Putaway',
                COALESCE(A.liquidate,0) AS '45 days hold',
                COALESCE(A.non_faulty,0) AS 'SOI-Non Faulty',
                COALESCE(A.courier_debit,0) AS 'Courier Debit',
                COALESCE(A.returns,0) AS 'Total Dispatch'
            FROM
            (
                (SELECT DATE(inv.created) AS DATE,
                    COUNT(*) AS putaway ,
                    COUNT(CASE WHEN ru.rule_name LIKE ('Liquidate%') THEN inv.id END) AS 'liquidate',
                    COUNT(CASE WHEN ru.rule_name LIKE ('%Non Faulty%') THEN inv.id END) AS 'non_faulty',
                    COUNT(CASE WHEN bur.rule_name LIKE ('%Courier Debit%') THEN inv.id END) AS 'courier_debit',
                    COUNT(CASE WHEN inv.status = 'RTV' THEN inv.id END) AS 'returns'

                FROM wms.inventory inv
                    LEFT JOIN wms.rules ru ON ru.id = inv.rule_id AND inv.is_bulk_rule <> 1
                    LEFT JOIN wms.bulk_upload_rules bur ON bur.id = inv.rule_id AND inv.is_bulk_rule = 1
                    LEFT JOIN wms.users u ON u.id = inv.createdBy_id
                WHERE inv.created BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE() AND """ + cur[2] + """
                    GROUP BY 1
                ) A
            );
    """
    cursor.execute(query)
    data = cursor.fetchall()

    header = []
    for row in cursor.description:
        header.append(row[0].title())

    html_data_warehouse += '<br><br><strong>Total Putaway and Returns.</strong><br>'
    html_data_warehouse += html_table_data_append(data, header)


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
                COUNT(CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 7 DAY THEN inv.id ELSE 0 END) AS 'Yest - 6 days'

            FROM wms.rtv_sheet_detail rtv
                JOIN wms.rtv_sheet_detail_inventory rts ON rts.rtv_sheet_detail_id = rtv.id
                JOIN wms.inventory inv ON inv.id = rts.productDetails_id
                LEFT JOIN wms.users u ON u.id = inv.createdBy_id
            WHERE rtv.created BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE() AND inv.status = 'RTV' AND """ + cur[2] + """
                GROUP BY 1
            UNION
            SELECT 'Total' AS 'Courier',
                COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 1 DAY THEN inv.id ELSE 0 END) AS 'Yest',
                COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 2 DAY THEN inv.id ELSE 0 END) AS 'Yest - 1 days',
                COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 3 DAY THEN inv.id ELSE 0 END) AS 'Yest - 2 days',
                COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 4 DAY THEN inv.id ELSE 0 END) AS 'Yest - 3 days',
                COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 5 DAY THEN inv.id ELSE 0 END) AS 'Yest - 4 days',
                COUNT(DISTINCT CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 6 DAY THEN inv.id ELSE 0 END) AS 'Yest - 5 days',
                COUNT(CASE WHEN DATE(rtv.updated) = DATE(NOW())-INTERVAL 7 DAY THEN inv.id ELSE 0 END) AS 'Yest - 6 days'
            FROM wms.rtv_sheet_detail rtv
                JOIN wms.rtv_sheet_detail_inventory rts ON rts.rtv_sheet_detail_id = rtv.id
                JOIN wms.inventory inv ON inv.id = rts.productDetails_id
                LEFT JOIN wms.users u ON u.id = inv.createdBy_id
            WHERE rtv.created BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE() AND inv.status = 'RTV' AND """ + cur[2] + """
                GROUP BY 1;
    """
    cursor.execute(query)
    data = cursor.fetchall()

    header = []

    for row in cursor.description:
        header.append(row[0].title())

    html_data_warehouse += '<br><br><strong>Courier Wise Dispatch Report of ' + cur[0] + '.</strong><br>'

    html_data_warehouse += html_table_data_append(data, header)

    # Get email from the DB.
    query2 = "select to_email from reports where name ='"+FILE_NAME+"'"
    cursor.execute(query2)
    data2 = cursor.fetchall()
    if cur[0] in email_cd_wh:
        to_email = email_wh + "," + data2[0][0]
    else:
        to_email = data2[0][0]

    send_mail_without_file(to_email, html_data_warehouse)