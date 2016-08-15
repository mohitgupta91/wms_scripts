__author__ = 'sobhagya'
# -*- coding: utf-8 -*-
# import sys
# sys.path.append('/var/www/html/wms/')
from datetime import date, timedelta
from library.db_connection import *
from library.html_data_creation import *
from library.mail_file import *

FILE_NAME = 'Email To Seller'

# Get Constant Email Address from the DB.
query2 = "select to_email from reports where name ='"+FILE_NAME+"'"
cursor.execute(query2)
data = cursor.fetchall()
constant_email = data[0][0]

query1=""" SELECT distinct inv.vendor_code AS 'Vendor Code'
            FROM rtv_sheet_detail rtv
                JOIN rtv_sheet_detail_inventory rtvi ON rtvi.rtv_sheet_detail_id = rtv.id
                JOIN inventory inv ON rtvi.productDetails_id = inv.id
                JOIN manifest_rtv_sheet_detail mr ON mr.rtvSheet_id = rtv.id
                JOIN manifest m ON m.id = mr.manifest_id
            WHERE m.created BETWEEN CURDATE() - INTERVAL 150 DAY AND NOW()
                AND rtv.return_warehouse = 'vendor';
"""
cursor.execute(query1)
vendors = cursor.fetchall()
print vendors

for seller in vendors:
    # print seller[0]
    query = """ SELECT  inv.suborderCode AS 'SubOrder',
                        inv.seller_name AS 'Vendor Name',
                        inv.product_name AS 'Product Name',
                        inv.issueCategory AS 'Issue Category',
                        rtv.created AS 'Sent On',
                        CONCAT(rtv.awb_number,'(',rtv.courier_code,')') AS 'Awb No'
                FROM rtv_sheet_detail rtv
                    JOIN rtv_sheet_detail_inventory rtvi ON rtvi.rtv_sheet_detail_id = rtv.id
                    JOIN inventory inv ON rtvi.productDetails_id = inv.id
                    JOIN manifest_rtv_sheet_detail mr ON mr.rtvSheet_id = rtv.id
                    JOIN manifest m ON m.id = mr.manifest_id
                WHERE m.created BETWEEN CURDATE() - INTERVAL 150 DAY AND NOW()
                    AND rtv.return_warehouse = 'vendor' and inv.vendor_code='""" + str(seller[0]).replace("'","\\'") + """';
    """

    cursor.execute(query)
    data = cursor.fetchall()
    print data
    header = []

    for col in cursor.description:
        header.append(col[0].title())

# for row in data:
    html_data = u"""Dear Partner,<br><br>
                We have received below listed complaints from our customers for return of your products.
                Post validation of the concern, we are sending the following products back to you.
                We request you to kindly acknowledge the receipt of the products within 5 working days,
                else they will be considered as accepted.<br><br>
                हमें अपने ग्राहकों से आपके प्रोडक्ट्स वापस करने के समबन्ध में निम्नलिखित शिकायतें मिली हैं।
                शिकायतों की जांच के पश्चात, हम यह प्रोडक्ट्स आपको वापस भेज रहे हैं।<br>
                आपसे निवेदन हैं कि, प्रोडक्ट मिलने के 5 दिनों के अंदर पुष्टि करे, अन्यथा प्रोडक्ट्स स्वीकार किये
                माने जायेंगे।. <br><br>
              """
    # result = []
    # result.append(data)
    html_data += html_table_data_append(data, header)

    html_data += u"""<br><br>Note:
                <li>For issue category “Customer wants a size change” and “Customer doesn’t want
                anymore”, your rating will not be affected and penalty will not be charged.
                <br>
                “Customer wants a size change” और “Customer doesn’t want anymore” जैसी
                शिकायतों के लिए आपके रेटिंग पर कोई असर नही होगी और आपको कोई पेनल्टी भी नही
                देनी होगी।
                <br><br>
                <li>If customer has requested for replacement, a new suborder id will be generated in
                your panel automatically and therefore sending product manually is not required.
                <br>
                यदि ग्राहक ने प्रोडक्ट्स को बदलने की मांग की है, तो एक नया सब- ओर्डर आपके पैनल में
                दिखाई देगा, इसलिए प्रोडक्ट्स को अलग से भेजने की आवश्यकता नहीं है।<br>

                In case of any queries please feel free to contact sellershelp@snapdeal.com
                Thank you for your on-going business partnership with us.
                <br><br>
                Sincerely,<br>
                Complaints Validation Team
                """

    # Get email from the DB.
    query2 = """SELECT COALESCE(rd.email,''),COALESCE(re.email,'')
                FROM receiver_detail rd
                    JOIN rtv_sheet_detail rtv ON rtv.receiverDetail_id = rd.id
                    JOIN rtv_sheet_detail_inventory rtvi ON rtvi.rtv_sheet_detail_id = rtv.id
                    JOIN inventory inv ON rtvi.productDetails_id = inv.id
                    LEFT JOIN receiver_email re ON rd.name = re.code
                WHERE inv.suborderCode =  '""" + str(data[0][0]) + """' order by rd.id desc limit 1;
    """
    cursor.execute(query2)
    data2 = cursor.fetchall()

    subject = 'Products returned by customers'
    email_cc = None
    row_count = cursor.rowcount

    if row_count != 0:
        to_email = data2[0][0]
        if data2[0][1] != '':
            to_email += "," + data2[0][1]
        if constant_email != '':
            to_email += "," + constant_email
        to_email = 'mohit.gupta@snapdeal.com'
        send_mail_without_file_subject(to_email, html_data, subject,email_cc)
