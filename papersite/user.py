### Authentication
###############################
                  ##################
            ############
import hashlib, sqlite3
from papersite import app
from flask import session, flash, redirect, url_for
from papersite.db import query_db, get_db
from flask import abort, request, render_template
from papersite.config import SALT1
from papersite.email import send_confirmation_mail, \
    send_password_change_mail
from math import ceil
from papersite.spamdetector import is_spam

def hash(password):
    m = hashlib.sha256()
    m.update(password)
    m.update(SALT1)
    return m.hexdigest()

def user_authenticated():
    return ('user' in session)

## Anonymous is the first one
ANONYMOUS = 1

def get_user_id():
    if user_authenticated():
        return session['user']['userid']
    else:
        # Anoynomous
        return ANONYMOUS

def is_super_admin(userid):
    return 1 == query_db("select super_admin  \
                          from users          \
                          where userid = ?", [userid], one=True)['super_admin']

def get_user(userid):
    return query_db("select * from users where userid = ?",
                    [userid], one=True)

def is_author_of_comment(userid, commentid):
    return 1 == query_db("select count(*) as count \
                          from comments \
                          where userid = ? and commentid = ?",
                     [userid, commentid], one=True)['count']

def is_author_of_paper(userid, paperid):
    return 1 == query_db("select count(*) as count \
                          from papers \
                          where userid = ? and paperid = ?",
                     [userid, paperid], one=True)['count']

def handle_sqlite_exception(err):
    if ("users.username" in str(err)):
        return "Sorry, the user name '%s' has already been taken"  % request.form['username']
    if ("users.email" in str(err)):
        return "Sorry, the email addreser '%s' has already been taken"  % request.form['email']

# populate user_authenticated() into jinja2 templates
@app.context_processor
def utility_processor():
    return dict(user_authenticated=user_authenticated)

@app.route('/hi', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        if request.form['email'] == "":
            error = 'Please use a valid email address'
        elif request.form['username'] == "":
            error = 'Do not forget about your name'
        elif request.form['password1'] != request.form['password2']:
            error = 'Password and retyped password do not match'
        elif request.form['password1'] == "":
            error = 'Password cannot be empty'
        elif "/" in request.form['username']:
            error = 'Username cannot contain symbol "/"'
        elif request.form['username'] in \
        [r.rule.split('/', maxsplit=2)[1] for r in app.url_map.iter_rules()]:
            error = 'You cannot use username "' + \
                    request.form['username']     + \
                    '", please choose another.'
        elif is_spam(request):
            return "<h1>Posted data looks like a spam, contact us if not</h1>", 403
        else:
            con = get_db()
            try:
                with con:
                    con.execute('insert into users \
                    (username, email, password, valid, about) \
                    values (?, ?, ?, ?, ?)',
                                [request.form['username'],
                                 request.form['email'],
                                 hash (request.
                                       form['password1'].
                                       encode('utf-8')),
                                 0,
                                 '...Some information about the user will someday appear here...'
                             ])
                send_confirmation_mail (request.form['username'],
                                        request.form['email'])
                flash('A confirmation link has been sent to you. \n\
Please, check your mailbox (%s). If it is not the case, please contact us.' % request.form['email'])
                return redirect(url_for('index'))
            except sqlite3.IntegrityError as err:
                error = handle_sqlite_exception(err)
    return render_template('users/register.html', error=error)

@app.route('/change-password/<string:key>', methods=['GET','POST'])
def set_new_password(key):
    error = None
    u = query_db('select userid, username, email,                   \
                         createtime, valid, about                   \
                  from users                                        \
                  where key = ?                                     \
                  and chpasstime > datetime("now","-2 days")',
                     [key], one=True)
    if u is not None:
        email = u['email']
        if request.method == 'POST':
            if request.form['password1'] != request.form['password2']:
                error = 'Password and retyped password do not match'
            elif request.form['password1'] == "":
                error = 'Password cannot be empty'
            else:
                con = get_db()
                with con:
                    con.execute('update users set \
                                 password = ?, valid = 1, key = null \
                                 where key = ?',
                                [hash (request.form['password1'].
                                       encode('utf-8')),
                                 key
                             ])
                    session.permanent = True
                    session['user'] = u
                    flash('Hello ' + u['username'] +  \
                          '. You have successfully changed your password')
                return redirect(url_for('usersite',username=session['user']['username']))
    else:
        email = 'brrrr. See red error above.'
        error = 'Not valid key'

    return render_template('users/restore2.html', key=key,
                           email=email,
                           error=error)

@app.route('/change-password', methods=['GET', 'POST'])
def new_password_link():
    error = None
    if request.method == 'POST':
        u = query_db('select userid,username,email,createtime,valid     \
                      from users                                        \
                      where email = ?',
                     [request.form['email']], one=True)
        if u is not None:
            send_password_change_mail (request.form['email'])
            flash('A confirmation link has been sent to you. \n\
                   Please, check your mailbox (%s)' %
                  request.form['email'])
            return redirect(url_for('index'))
        else:
            error = 'User with this email does not exists'
    return render_template('users/restore.html', error = error)

@app.route('/hi/<string:key>')
def register_confirmation(key):
    error = None
    u = query_db('select userid,username,email,   \
                         createtime,valid,about   \
                  from users                      \
                  where key = ?',
                 [key], one=True)
    if u is not None:
        con = get_db()
        with con:
            con.execute('update users set valid = 1, key = null \
                         where key = ?',
                         [key])
        session.permanent = True
        session['user'] = u
        flash('Hello ' + u['username'] +  \
              '. You have successfully confirmed your email address')
    return redirect(url_for('usersite',username=session['user']['username']))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        u = query_db('select userid,username,email,                     \
                             createtime,valid,about,notifs_muted        \
                      from users                                        \
                      where password = ? and email = ?',
                     [hash (request.
                            form['password']
                            .encode('utf-8')),
                      request.form['email']], one=True)
        if u is not None:
            if u['valid'] == 0:
                error = 'Please, check your mail box. We have \
                sent you an email.'
            elif 'rememberme' in request.form:
                session.permanent = True
            session['user'] = u
            flash('You were successfully logged in')
            return redirect(url_for('index'))
        else:
            error = 'Invalid credentials'
    return render_template('users/login.html', error=error)

@app.route("/editinfo", methods=['GET','POST'])
def editinfo():
    if not user_authenticated():
        return "<h1>Forbidden (maybe you forgot to login)</h1>", 403
    error = None
    if request.method == 'POST':
        if request.form['email'] == "":
            error = 'Please use a valid email address'
        elif request.form['username'] == "":
            error = 'Do not forget about your name'
        elif "/" in request.form['username']:
            error = 'Username cannot contain symbol "/"'
        elif request.form['username'] in \
             [r.rule.split('/', maxsplit=2)[1] for r in app.url_map.iter_rules()]:
            error = 'You cannot use username "' + \
                    request.form['username']     + \
                    '", please choose another.'
        else:
            con = get_db()
            if 'notifs_muted' in request.form:
                notifs_muted = request.form['notifs_muted']
            else:
                notifs_muted = 0
            try:
                with con:
                    con.execute('update users set about = ?, \
                                 email = ?, username = ?,    \
                                 notifs_muted = ?            \
                                 where userid = ?',
                                [request.form['about'],
                                 request.form['email'],
                                 request.form['username'],
                                 notifs_muted,
                                 session['user']['userid']])
                session['user']['email'] = request.form['email']
                session['user']['about'] = request.form['about']
                session['user']['username'] = request.form['username']
                session['user']['notifs_muted'] = notifs_muted
                # if all is good
                return redirect(url_for('usersite',username=session['user']['username']))
            except sqlite3.IntegrityError as err:
                error = handle_sqlite_exception(err)
    # if any error
    return render_template('users/editinfo.html', error=error)

@app.route("/mute-email-notifs", methods=['GET'])
def mute_email_notifs():
    if not user_authenticated():
        return "<h1>Forbidden (maybe you forgot to login)</h1>", 403
    con = get_db()
    with con:
        con.execute('update users set notifs_muted = 1 \
                     where userid = ?',
                     [session['user']['userid']])
        session['user']['notifs_muted'] = "1"
        flash('Email notifications are muted')
        return redirect(url_for('usersite',username=session['user']['username']))
    return redirect(url_for('usersite'))

@app.route("/unmute-email-notifs", methods=['GET'])
def unmute_email_notifs():
    if not user_authenticated():
        return "<h1>Forbidden (maybe you forgot to login)</h1>", 403
    con = get_db()
    with con:
        con.execute('update users set notifs_muted = 0 \
                     where userid = ?',
                     [session['user']['userid']])
        session['user']['notifs_muted'] = "0"
        flash('Email notifications are UN-muted')
        return redirect(url_for('usersite',username=session['user']['username']))
    return redirect(url_for('usersite'))


@app.route("/logout")
def logout():
    # remove the user from the session if it's there
    session.pop('user', None)
    return redirect(url_for('index'))
