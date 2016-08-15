__author__ = 'sobhagya'

import csv

def file_create(result,header,fileName):

    file_link = "/var/www/html/wms/Reports/"
    file = open(file_link + fileName, 'w')
    file.write(header)
    writer = csv.writer(file,delimiter=',')
    writer.writerows(result)
    file.close()
