__author__ = 'sobhagya'

import sys
sys.path.append('/var/www/html/wms/')
from library.db_connection import *
from library.html_data_creation import *
from library.mail_file import *

FILE_NAME = 'Tracking Numbers Left'

# html_data = '<html><body>'

query = """
        SELECT tn.courier_code,
            COUNT(tn.tracking_number) AS total_left
        FROM tracking_numbers AS tn
        JOIN couriers AS c
        ON c.code = tn.courier_code and c.enabled = 1
        WHERE tn.is_used = 0
        group by courier_code;"""

cursor.execute(query)
data = cursor.fetchall()

header = ['Courier Code', 'Tracking Numbers']
html_data = 'Hi<br><br><strong>Tracking Numbers Left.</strong><br>'

html_data += html_table_data_append(data, header)
# html_data += '</body></html>'

# Get email from the DB.
query2 = "select to_email from reports where name ='"+FILE_NAME+"'"
cursor.execute(query2)
data2 = cursor.fetchall()
to_email = data2[0][0]

send_mail_without_file(to_email, html_data)

db.close()