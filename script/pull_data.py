__author__ = 'sobhagya'

import sys
import datetime
sys.path.append('/var/www/html/wms/')
from library.db_connection import *

############## Creating Temp RPR Table ###########
# query = """ DROP TABLE IF EXISTS `tmp`; """
# cursor.execute(query)
# db.commit()
#
# query = """
#         CREATE TABLE `tmp` (
#           `id` int(11) NOT NULL AUTO_INCREMENT,
#           `barcode` varchar(50) NOT NULL,
#           `rpr_date_time` datetime NOT NULL,
#           PRIMARY KEY (`id`)
#         ) ENGINE=InnoDB DEFAULT CHARSET=utf8
# """
# cursor.execute(query)
# db.commit()


query = """SELECT
            cri.code, COALESCE(CAST(crph.created AS char),'')
        FROM
            rms.customer_returned_item cri
                JOIN
            rms.customer_returned_package crp ON crp.id = cri.crp_id
                JOIN
            rms.crp_history crph ON crph.crp_id = crp.id
        WHERE
            crph.next_status_code = 'RPR'
            AND crph.previous_status_code <> 'RPR'
            AND crph.created < '2014-10-01'
            AND cri.code IS NOT NULL;
    """

cursor_rms.execute(query)
data_rms = cursor_rms.fetchall()

# if len(data_rms) > 1:
#     data_rms = str(data_rms)
#     data_rms = data_rms[1:len(data_rms)-1]
# else:
#     data_rms = str(data_rms)
#     data_rms = data_rms[1:len(data_rms)-2]
#

for row in data_rms:
    query = """ INSERT INTO tmp (barcode, rpr_date_time) VALUES """ + str(row)

    cursor.execute(query)
    db.commit()
