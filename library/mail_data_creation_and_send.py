__author__ = 'sobhagya'

from library.mail_file import *

def html_table_data_append_and_mail(result, header, email_data, to_email):
    email_data = '<html><body>' + email_data
    email_data += '<table width="100%" style="text-align:center;border-top:4px solid #dbd9d9;border-bottom:4px solid #dbd9db9;border-collapse:collapse;">'

    # Header of the table
    email_data += '<tr>'
    for data in header:
        email_data += '<td style="padding:7px 5px;border:1px solid #ccc;font-size:12px;font-family:Segoe UI,arial;">'+str(data)+'</td>'
    email_data += '</tr>'

    # Body of the table
    #email_data += '<tbody>'

    for row in result:
        email_data += '<tr>'
        for data in row:
            email_data += '<td style="padding:12px 5px;border:1px solid #ccc;font-size:12px;font-family:Segoe UI,arial;">'+str(data)+'</td>'
        email_data += '</tr>'

    email_data += '</table>'
    email_data += '</body></html>'

    send_mail_without_file(to_email, email_data)