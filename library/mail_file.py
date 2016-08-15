__author__ = 'sobhagya'
# -*- coding: utf-8 -*-
import os

def send_mail(filename, email_to, email_data):

    subject = 'WMS Reports'
    file_link = "/var/www/html/wms/Reports/"
    file_link += filename
    os.system("php sendMail.php '" + str(file_link) + "' '" + str(email_to) + "' '" + str(email_data) +
              "' '" + str(subject) + "' '" + str(filename) + "' ")

def send_mail_with_file_subject(filename, email_to, email_data, email_subject):

    subject = email_subject
    file_link = "/var/www/html/wms/Reports/"
    file_link += filename
    os.system("php sendMail.php '" + str(file_link) + "' '" + str(email_to) + "' '" + str(email_data) +
              "' '" + str(subject) + "' '" + str(filename) + "' ")

def send_mail_without_file(email_to, email_data):

    subject = 'WMS Reports'
    os.system("php sendMail.php '" + str(email_to) + "' '" + str(email_data) +
              "' '" + str(subject) + "' ")


def send_mail_without_file_subject(email_to, email_data, subject,email_cc = None):
    if email_cc == None:
        os.system("php sendMail.php '" + str(email_to) + "' '" + email_data.encode('utf-8') +
              "' '" + str(subject) + "' ")
    else:
        os.system("php sendMail.php '" + str(email_to) + "' '" + email_data.encode('utf-8') +
              "' '" + str(subject) + "' '"+str(email_cc) +"' '"+"'dummy'" + "' ")
