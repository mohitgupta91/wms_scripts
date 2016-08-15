__author__ = 'sobhagya'

import sys
import datetime
sys.path.append('/var/www/html/wms/')
from library.db_connection import *

query = """select barcode from inventory where customer_name is null and barcode <> '\CRI13000826';"""

cursor.execute(query)
data = cursor.fetchall()

for row in data:
    query = """select
                pd.name as customer_name
            from
                customer_returned_item cri
                    JOIN
                customer_returned_package crp ON crp.id = cri.crp_id
                    JOIN
                pickup_detail pd ON pd.id = crp.pickup_detail_id
            where
                cri.code = '"""+ row[0] +"""';
        """

    cursor_rms.execute(query)
    data_rms = cursor_rms.fetchall()

    query = """Update inventory set customer_name = '""" + str(data_rms[0][0]).replace("'", "''") + """' where barcode ='""" + row[0] + """';"""

    cursor.execute(query)
    db.commit()
