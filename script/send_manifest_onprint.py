__author__ = 'mohit'

import sys
import datetime
import xml.etree.ElementTree as ET
sys.path.append('/var/www/html/wms/')
from library.db_connection import *
from library.file_creation import *
from library.mail_file import *

FILE_NAME = 'Manifest Data'


def file_create_and_mail(result, header, to_email, email_data, email_subject):
    today = datetime.datetime.now().strftime('%d_%m_%Y_%H_%M_%S')
    #print to_email
    file_name = today+'_'+FILE_NAME+'.csv'
    file_create(result, header, file_name)

    send_mail_with_file_subject(file_name, to_email, email_data, email_subject)


# Exclude these headers since these are present in all the tables and have redundant data.
exclude_header = ['id', 'created', 'updated', 'createdBy_id', 'updatedBy_id']

# Get all column name of inventory
query = """SELECT * FROM inventory LIMIT 1;"""
cursor.execute(query)
data = cursor.fetchall()

inventory = []
for row in cursor.description:
    if not any(row[0] in s for s in exclude_header):
        inventory.append(row[0])

# Get all column name of rtv_sheet_detail
query = """SELECT * FROM rtv_sheet_detail LIMIT 1;"""
cursor.execute(query)
data = cursor.fetchall()

rtv = []
for row in cursor.description:
    if not any(row[0] in s for s in exclude_header):
        rtv.append(row[0])


# Get all column name of receiver_detail
query = """SELECT * FROM receiver_detail LIMIT 1;"""
cursor.execute(query)
data = cursor.fetchall()

rd = []
for row in cursor.description:
    if not any(row[0] in s for s in exclude_header):
        rd.append(row[0])


# Get all column name of warehouse
query = """SELECT * FROM warehouse LIMIT 1;"""
cursor.execute(query)
data = cursor.fetchall()

wh = []
for row in cursor.description:
    if not any(row[0] in s for s in exclude_header):
        wh.append(row[0])

# Manifest - Created
manifest = ['created']

#inventory = ['order_code', 'barcode', 'seller_name', 'product_name', 'vendor_code', 'forwardAwbNumber', 'price', 'weight', 'suborderCode', 'shipping_mode', 'issueCategory']
#rtv = ['awb_number', 'created', 'bag']
#rd = ['address_line1', 'address_line2', 'city', 'state', 'pincode', 'contact_number', 'email']

query = """
        SELECT c.code,
            c.name,
            c.primary_email,
            c.secondary_email,
            c.soft_data_header,
            c.soft_data_template,
            c.soft_data_subject
        FROM couriers c
            WHERE c.enabled = 1 AND c.soft_data_template <> '';
"""
cursor.execute(query)
data = cursor.fetchall()
#print data

query="""
        Select wh.name from warehouse wh
        """
cursor.execute(query)
warehouseList=cursor.fetchall()

for courier in data:
    tree = ET.ElementTree(ET.fromstring(courier[5]))
    root = tree.getroot()

    header = ""
    mapHeader = []
    mapValue = []

    for column in root.findall('Column'):
        header += column.find('Title').text + ","
        mapHeader.append(column.find('Map').text)
        if column.find('Value') is not None:
            mapValue.append(column.find('Value').text)
        else:
            mapValue.append('')

    header = header[:-1] + "\n"

    if len(mapHeader) > 0:
        column_string = ""

        index = 0
        for item in mapHeader:
            if item == "sno":
                column_string += "(@n := @n + 1) as SNO,"
            #elif item == "rtvlNo":
             #   column_string += "CONCAT('RTVL', rtv.id),"
            #elif any(item == s for s in inventory):
            #    column_string += "inv." + item + ","
            #elif any(item == s for s in rtv):
            #    column_string += "rtv." + item + ","
            #elif any(item == s for s in rd):
            #    column_string += "rd." + item + ","
            #elif any(item == s for s in wh):
            #    column_string += "wh." + item + ","
            #elif any(item == s for s in manifest):
            #    column_string += "m." + item + ","
            else:
                column_string += "'" + mapValue[index] + "',"

            index += 1

        column_string = column_string[:-1] + " "
	for wh in warehouseList:
		query = """
                	SELECT """ + column_string + """
                	FROM manifest
                    	LEFT JOIN manifest_rtv_sheet_detail  ON manifest.id = manifest_rtv_sheet_detail.manifest_id
                    	LEFT JOIN rtv_sheet_detail ON manifest_rtv_sheet_detail.rtvSheet_id = rtv_sheet_detail.id
                    	LEFT JOIN receiver_detail  ON rtv_sheet_detail.receiverDetail_id = receiver_detail.id
                    	LEFT JOIN rtv_sheet_detail_inventory ON rtv_sheet_detail.id = rtv_sheet_detail_inventory.rtv_sheet_detail_id
                    	LEFT JOIN inventory ON rtv_sheet_detail_inventory.productDetails_id = inventory.id
                    	LEFT JOIN warehouse  ON warehouse.id = rtv_sheet_detail.warehouse_id
                    	LEFT JOIN address_details ON warehouse.id =address_details.id
                    	CROSS JOIN (SELECT @n := 0) as dummy
                	WHERE manifest.courier_code = '""" + courier[0] + """'
                    	AND manifest.created BETWEEN NOW() - INTERVAL 10 Minute AND NOW() and is_email_sent=1 and warehouse.name='"""+wh[0]+"""';

      		          """
		cursoy.execute(query)
        	data_manifest = cursor.fetchall()
        	#print data_manifest
        	to_email = courier[2]
        	if courier[3] is not None:
            		to_email += "," + courier[3]

        	if courier[4] is not None:
            		email_data = courier[4].replace('\n', '<br />')
        	else:
            		email_data = "Hi<br><br>Please find attached Manifest File."

        	if courier[6] is not None:
            		email_subject = courier[6]+" : "+wh[0]
        	else:
            		email_subject = "Snapdeal Support"+" : "+wh[0]
        		#to_email = 'mohit.gupta@snapdeal.com'
        	if cursor.rowcount > 0:
            		file_create_and_mail(data_manifest, header, to_email, email_data, email_subject)

	query = """Update manifest m set m.is_email_sent = 0 WHERE m.courier_code = '""" + courier[0] + """' and m.is_email_sent=1; """
        #cursor.execute(query)
        db.commit()

db.close()
