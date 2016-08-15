__author__ = 'sobhagya'

import sys
sys.path.append('/var/www/html/wms/')
from library.db_connection import *
from library.mail_data_creation_and_send import *

FILE_NAME = 'RPI'

query = """
        select A.date,
            COALESCE(A.total_rpi,0) as total_rpi,
            COALESCE(B.total_rpr,0) as total_rpr,
            COALESCE(C.total_qc,0) as total_qc from
        (
            (select date(created) as date, count(*) as total_rpi from customer_returned_package where
                created >= curdate() - 6
                AND created <= now() group by date(created)
            ) A

            left join (select date(created) as date, count(*) as total_rpr from crp_history
                where next_status_code = 'RPR' and previous_status_code <> 'RPR' and
                created >= curdate() - 6
                AND created <= now() group by date(created)
            ) B on A.date = B.date

            left join (select date(created) as date, count(*) as total_qc from cri_history
                where next_status_code = 'PDC' and previous_status_code <> 'PDC' and
                created >= curdate() - 6
                AND created <= now() group by date(created)
            ) C on A.date = C.date
        )
"""
cursor_rms.execute(query)
data = cursor_rms.fetchall()

query = """
        select
            COALESCE(A.putaway,0) as total_putaway,
            COALESCE(B.returns,0) as total_returns,
            COALESCE(C.gatepass,0) as total_gatepass,
            COALESCE(A.putaway,0) - (COALESCE(B.returns,0) + COALESCE(C.gatepass,0)) as total_liquidation
        from
        (
            (select date(created) as date, count(*) as putaway from inventory where
                created >= curdate() - 6
                AND created <= now() group by date(created)
            ) A

            left join (select date(created) as date, count(*) as returns from inventory where
                status = 'RTV' and
                created >= curdate() - 6
                AND created <= now() group by date(created)
            ) B on A.date = B.date

            left join (select date(created) as date, count(*) as gatepass from gate_pass where
                created >= curdate() - 7
                AND created <= now() group by date(created)
            ) C on A.date = C.date
        )
"""
cursor.execute(query)
data2 = cursor.fetchall()

result = []

i = 0
for row in data2:
    new_row = data[i] + row
    result.append(new_row)
    i += 1

header = ['Date', 'Total RPI', 'Total RPR',	'Total QC', 'Total Putaway', 'Total Returns', 'Total Gatepass', 'Total Liquidation']
email_data = 'Hi<br><br><strong>Please find total RPI, RPR, QC, Putaway, Returns, Gatepass, Liquidation Report for past 7 days.</strong><br>'


# Get email from the DB.
query2 = "select to_email from reports where name ='"+FILE_NAME+"'"
cursor.execute(query2)
data2 = cursor.fetchall()
to_email = data2[0][0]

html_table_data_append_and_mail(result, header, email_data, to_email)

db.close()
