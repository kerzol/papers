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
from papersite.email import send_confirmation_mail

def hash(password):
    m = hashlib.sha256()
    m.update(password)
    m.update(SALT1)
    return m.hexdigest()

def user_authenticated():
    return ('user' in session)

def get_user_id():
    if user_authenticated(): 
        return session['user']['userid']
    else:
        # Anoynomous
        return 1 

# populate user_authenticated() into jinja2 templates
@app.context_processor
def utility_processor():
    return dict(user_authenticated=user_authenticated)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        if request.form['email'] == "":
            error = 'Please use a valid email adress'
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
        else:
            con = get_db()
            try:
                with con:
                    con.execute('insert into users \
                    (username, email, password, valid) \
                    values (?, ?, ?, ?)',
                                [request.form['username'],
                                 request.form['email'],
                                 hash (request.
                                       form['password1'].
                                       encode('utf-8')),
                                 0
                             ])
                send_confirmation_mail (request.form['username'],
                                        request.form['email'])
                flash('A confirmation link has been sent to you. \n\
Please, check your mailbox (%s)' % request.form['email'])
                return redirect(url_for('index'))
            except sqlite3.IntegrityError:
                error="Sorry, that user name has already been taken \
                (or the e-mail has already been used by someone)"
    return render_template('users/register.html', error=error)


@app.route('/register/<string:key>')
def register_confirmation(key):
    error = None
    u = query_db('select userid,username,email,createtime,valid  \
                  from users     \
                  where key = ?',
                 [key], one=True)
    if u is not None:
        con = get_db()
        with con:
            con.execute('update users set valid = 1 \
                         where key = ?',
                         [key])
        session.permanent = True
        session['user'] = u
        flash('Hello ' + u['username'] +  \
              '. You were successfully confirm your email adress')
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        u = query_db('select userid,username,email,createtime,valid     \
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

@app.route("/logout")
def logout():
    # remove the user from the session if it's there
    session.pop('user', None)
    return redirect(url_for('index'))




### Main list of papers liked or uploaded by user
###############################
                  ##################
            ############

@app.route('/<string:username>')
@app.route('/<string:username>/page/<int:page>')
def usersite(username,page=1):
    """ Generate previews of papers uploaded/liked by specified user
    """
    u=query_db("select * from users where username = ?",
                      [username],one=True)
    if not u: abort(404)
    # count the paper uploaded/liked by this user
    count = query_db("select count(distinct p.paperid) as c        \
                      from papers as p, likes as l                 \
                      where                                        \
                         p.userid = ? or                           \
                         (p.paperid = l.paperid and l.userid = ?)  \
                     ", [u['userid'],u['userid']], one=True)['c']
    # how many papers on page?
    onpage = 3
    maxpage = int(ceil(float(count)/onpage))
    # todo. some papers ... are bad
    seq=query_db("select distinct p.*                            \
                    from papers as p, likes as l                 \
                    where                                        \
                       p.userid = ? or                           \
                       (p.paperid = l.paperid and l.userid = ?)  \
                  order by p.lastcommentat DESC                  \
                  limit ?, ?", [u['userid'],u['userid'],
                                (page-1)*onpage,onpage])

    commentsTail, commentsHead, likes, liked = previews(seq)

    return render_template('usersite.html', seq=seq,
                           user=u,
                           commentsTail=commentsTail, 
                           commentsHead=commentsHead,
                           likes=likes,liked=liked,
                           maxpage=maxpage, curpage=page,
                           headurl='/'+username)

@app.route('/<string:username>&Co')
def user_and_co(username):
    return "<h1> hello " + username + " and Company", 200
    
