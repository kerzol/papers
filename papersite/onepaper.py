### One paper
###############################
                  ##################
            ############
from papersite import app
from papersite.db import query_db, get_db
from papersite.user import get_user_id,  user_authenticated
from papersite.main_list_of_papers import (get_authors, get_domains,
                                           get_keywords, get_comments)
from werkzeug import secure_filename
import os
from flask import render_template, request, flash, redirect, url_for

@app.route('/paper/<int:paperid>/<string:title>', methods=['GET'])
def onepaper(paperid, title):
    paper=query_db("select p.paperid, p.getlink,                 \
                                 p.title,                        \
                                 p.userid, p.createtime,         \
                                 u.username                      \
                           from papers as p,                     \
                                users as u                       \
                          where                                  \
                                p.userid   = u.userid   and      \
                                p.paperid = ?",
                   [paperid], one=True)
    liked = query_db(
        "select count(*) as c            \
        from likes                       \
        where paperid=? and userid=?",
        [paperid,get_user_id()],
        one=True)['c']
    authors=get_authors(paperid)
    domains=get_domains(paperid)                       
    keywords=get_keywords(paperid)
    comments=get_comments(paperid)
    return render_template('paper/onepaper.html', 
                           entry=paper,
                           comments=comments,
                           authors=authors,
                           domains=domains,
                           keywords=keywords,
                           likes=likes(paperid),liked=liked)


@app.route('/paper/<int:paperid>/<string:title>/add-comment',
           methods=['POST'])
def add_comment(paperid, title):
    con = get_db()
    error = None
    with con:
        con.execute('insert into comments \
        (comment,userid,paperid) \
        values (?,?,?)',
                        [
                            # here we do not escape, because we will
                            # do it in jinja
                            request.form['comment'],
                            get_user_id(),
                            paperid
                        ])
        con.execute('update papers set lastcommentat=datetime() \
                       where paperid = ?', [paperid])
        if user_authenticated(): 
            flash('You successfully commented the paper')
        else: 
            flash('You anonymously commented the paper')

    last_c_id=query_db("SELECT last_insert_rowid() as lid",
                       one=True)['lid']
    return redirect(url_for('onepaper',paperid=paperid,
                                    title=title, error=error)
                    + "#comment-"
                    + str(last_c_id))




### Add paper
###############################
                  ##################
            ############


ALLOWED_EXTENSIONS = set(['pdf'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# If there is no such keyword/author/domain in db, 
# we will insert in into db
def get_insert_keyword(keyword):
    con = get_db()
    with con:
        con.execute("INSERT OR IGNORE INTO keywords(keyword)     \
                     VALUES(?)", [keyword])
        id = con.execute("SELECT keywordid FROM keywords         \
                          WHERE keyword = ?", 
                         [keyword]).fetchone()['keywordid']
    return id


def get_insert_author(fullname):
    con = get_db()
    with con:
        con.execute("INSERT OR IGNORE INTO authors(fullname)      \
                     VALUES(?)", [fullname])
        id = con.execute("SELECT authorid FROM authors            \
                     WHERE fullname = ?",
                    [fullname]).fetchone()['authorid']
    return id


def get_insert_domain(domainname):
    con = get_db()
    with con:
        con.execute("INSERT OR IGNORE INTO domains(domainname)    \
                     VALUES(?)", [domainname])
        id = con.execute("SELECT domainid FROM domains            \
                     WHERE domainname = ?", 
                         [domainname]).fetchone()['domainid']
    return id


def parse_list(list):
    return map(str.strip, list.rstrip(', ').split(','))


@app.route('/paper/add', methods=['GET','POST'])
def add_paper():
    error = None
    if request.method == 'POST':
        paper_file = request.files['pdf']
        if not paper_file or not allowed_file(paper_file.filename):
            error = 'Please choose a pdf file'
        elif request.form['title'] == "":
            error = 'Please add a title'
        elif request.form['domains'] == "":
            error = 'Please specify at least one domain'
        elif request.form['authors'] == "":
            error = 'Please add some authors'
        elif request.form['keywords'] == "":
            error = 'Please add some keywords'
        else:
            con = get_db()
            # todo: lock db?
            with con:
              con.execute('insert into papers(title,userid)         \
                             values (?,?)',
                             [request.form['title'], get_user_id()])

              paperid = con.execute("SELECT last_insert_rowid() as lid"
                                    ).fetchone()['lid']

              authors_ids = map(get_insert_author,
                                parse_list(request.form['authors']))
              map(lambda authorid:
                  con.execute('insert into papers_authors             \
                              (paperid, authorid)                     \
                              values(?,?)',[paperid, authorid]),
                  authors_ids)

              domains_ids = map(get_insert_domain,
                               parse_list(request.form['domains']))
              map(lambda domainid:
                  con.execute('insert into papers_domains             \
                               (paperid, domainid)                    \
                               values(?,?)',[paperid, domainid]),
                  domains_ids)

              keywords_ids = map(get_insert_keyword,
                               parse_list(request.form['keywords']))
              map(lambda keywordid:
                  con.execute('insert into papers_keywords            \
                            (paperid, keywordid)                      \
                            values(?,?)',[paperid, keywordid]),
                  keywords_ids)
              

              filename = str(paperid) + "-" +                       \
                       secure_filename(paper_file.filename)
              ppdf = os.path.join(app.config['UPLOAD_FOLDER'],filename)
              paper_file.save(ppdf)
              con.execute("update papers set getlink = ?             \
                           where paperid=?",
                          ['/static/memory/pdfs/'+filename, paperid])

              ## this is just a hack.
              filename = str(paperid) + ".png"
              ppng = os.path.join(app.config['PREVIEW_FOLDER'],
                                  filename)

              os.system('papersite/gen.sh ' + ppdf +  ' ' + ppng)
              # end of hack
              flash('You successfully upload the paper')
            return redirect(url_for('onepaper',
                                    paperid=paperid,
                                    title=request.form['title']))
    return render_template('paper/add.html', 
                           error=error,
                           domains=query_db ("select * from domains"),
                           keywords=query_db ("select * from keywords"),
                           authors=query_db ("select * from authors"))


### Like a paper
###############################
                  ##################
            ############

def likes(paperid):
    return query_db(
        "select count(*) as c                   \
        from likes                              \
        where paperid=?",
        [paperid],
        one=True)['c']

@app.route('/paper/<int:paperid>/<string:title>/like', methods=['GET'])
def like_paper(paperid,title):
    if not user_authenticated():
        return "<h1>Forbidden (anonymous cannot like)</h1>", 403
    con = get_db()
    with con:
        con.execute('insert into likes (paperid,userid) values (?,?)',
                    [paperid, get_user_id()])
    return str(likes(paperid))

@app.route('/paper/<int:paperid>/<string:title>/unlike', methods=['GET'])
def unlike_paper(paperid,title):
    if not user_authenticated():
        return "<h1>Forbidden (anonymous cannot unlike)</h1>", 403
    con = get_db()
    with con:
        con.execute('delete from likes where \
                     paperid = ? and userid=?',
                    [paperid, get_user_id()])
    return str(likes(paperid))




