__author__ = 'sobhagya'

def html_table_data_append(result, header):
    email_data = '<table style="border:#dfdfdf solid 1px; border-collapse: collapse;">'

    # Header of the table
    email_data += '<tr bgcolor="#f1f1f1">'
    for data in header:
        email_data += '<td style="border: #dfdfdf solid 1px;">'+str(data).replace("'", "")+'</td>'
    email_data += '</tr>'

    # Body of the table
    for row in result:
        email_data += '<tr>'
        for data in row:
            email_data += '<td style="border: #dfdfdf solid 1px;">'+str(data).replace("'", "")+'</td>'
        email_data += '</tr>'

    email_data += '</table>'

    return email_data
