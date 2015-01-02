### Confirmation mails, news, etc
#######################################
                      #######################
               ############

import smtplib
import random, string
from email.mime.text import MIMEText
from papersite.config import MAIL_SERVER, MAIL_USER, MAIL_PASS
from papersite.db import query_db, get_db
from flask import url_for
import papersite.user
               
def send_confirmation_mail(username, usermail):
    key = ''.join(map( lambda x : random.choice(string.ascii_letters),
                       range(100)))

    # TODO: write key into db
    con = get_db()
    with con:
        con.execute('update users set key = ? \
                     where username = ?',
                    [key, username])
    
    # Create a text/plain message
    msg = MIMEText(
"Hello %s, \n\n\
 If you want to complete the registeration on 'Papers' \n\
 you should click on the following link:               \n\
 %s                                                    \n\n\
Good luck,\n\
Papers' team" % (username, url_for('register_confirmation',
                         key=key, _external=True)))
    msg['Subject'] = 'subj'
    msg['From'] = MAIL_USER
    msg['To'] = usermail
    
    # Send the message via our own SMTP server.
    s = smtplib.SMTP_SSL(MAIL_SERVER)
    s.login(MAIL_USER, MAIL_PASS)
    s.send_message(msg)
    s.quit()


def send_password_restore_mail(usermail):
    pass
