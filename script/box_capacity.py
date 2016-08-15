__author__ = 'sobhagya'

import sys
import datetime
sys.path.append('/var/www/html/wms/')
from library.db_connection import *
from library.file_creation import *
from library.mail_file import *

FILE_NAME = 'Box Capacity'

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
        select substr(b.box_name,1,instr(b.box_name, '-') - 1) as group_name,
            b.box_name,
            b.capacity,
            b.used,
            w.name as warehouse_name
        from
            boxes as b
            join warehouse w on w.id = b.warehouse_id
        where b.used = b.capacity;
"""
cursor.execute(query)
data = cursor.fetchall()

header = 'Group Name,Box Name,Capacity,Used,Warehouse Name\n'

email_data = "Hi<br><br>Please find attached list of Boxes whose capacity are filled completely."
file_create_and_mail(data, header, email_data)

db.close()