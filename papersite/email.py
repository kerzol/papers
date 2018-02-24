### Confirmation mails, news, etc
#######################################
                      #######################
               ############

import smtplib, random, string, datetime
from email.mime.text import MIMEText
from papersite.config import MAIL_SERVER, MAIL_USER, MAIL_PASS
from papersite.db import query_db, get_db
from flask import url_for
import papersite.user

## send notifs, if notifs are not muted
def send_mail(usermail, message):
    u = query_db('select userid,username,email,createtime,valid     \
                  from users                                        \
                  where email = ?',
                 [usermail], one=True)
    if (not u.notifs_muted):
        # Create a text/plain message
        msg = MIMEText(message)
        msg['Subject'] = 'Change password'
        msg['From'] = MAIL_USER
        msg['To'] = usermail

        # Send the message via our own SMTP server.
        s = smtplib.SMTP_SSL(MAIL_SERVER)
        s.login(MAIL_USER, MAIL_PASS)
        s.send_message(msg)
        s.quit()


def send_confirmation_mail(username, usermail):
    key = ''.join(map( lambda x : random.choice(string.ascii_letters),
                       range(100)))

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
    msg['Subject'] = 'Email confirmation'
    msg['From'] = MAIL_USER
    msg['To'] = usermail
    
    # Send the message via our own SMTP server.
    s = smtplib.SMTP_SSL(MAIL_SERVER)
    s.login(MAIL_USER, MAIL_PASS)
    s.send_message(msg)
    s.quit()


def send_password_change_mail(usermail):
    key = ''.join(map( lambda x : random.choice(string.ascii_letters),
                       range(100)))

    con = get_db()
    with con:
        con.execute('update users set     \
                     key = ?,             \
                     chpasstime = ?       \
                     where email = ?',
                    [key, datetime.datetime.now(), usermail])

    u = query_db('select userid,username,email,createtime,valid     \
                  from users                                        \
                  where email = ?',
                 [usermail], one=True)

    # Create a text/plain message
    msg = MIMEText(
"Hello %s, \n\n\
 If you want to change your password on 'Papers' site  \n\
 you should click on the following link:               \n\
 %s                                                    \n\n\
 This link will be valid for 2 days only \n\n\
Good luck,\n\
Papers' team" % (u['username'], url_for('set_new_password',
                                        key=key, _external=True)))
    msg['Subject'] = 'Change password'
    msg['From'] = MAIL_USER
    msg['To'] = usermail

    # Send the message via our own SMTP server.
    s = smtplib.SMTP_SSL(MAIL_SERVER)
    s.login(MAIL_USER, MAIL_PASS)
    s.send_message(msg)
    s.quit()
