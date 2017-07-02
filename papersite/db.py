### DATABASE STUFF 
###############################
                  ##################
            ############

from papersite import app
from flask import g
import papersite.config
import sqlite3


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(papersite.config.DATABASE)
        db.row_factory = dict_factory
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# fancy sqlrow -> dict converter
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_authors(paperid):
    return query_db("select                                      \
                        a.authorid, a.fullname                   \
                      from                                       \
                        papers_authors as pa,                    \
                        authors as a                             \
                      where                                      \
                           pa.authorid = a.authorid and          \
                           pa.paperid = ?",
                     [paperid])

def get_domains(paperid): 
    return query_db("select                                      \
                        d.domainid, d.domainname from            \
                        domains as d, papers_domains as pd       \
                      where                                      \
                        pd.domainid = d.domainid and             \
                        pd.paperid = ?",
                     [paperid])

                       
def get_keywords(paperid):
    return query_db("select                                      \
                         k.keywordid, k.keyword                  \
                       from keywords as k, papers_keywords as pk \
                       where                                     \
                         pk.keywordid = k.keywordid and          \
                         pk.paperid = ?",
                      [paperid])

def get_comments(paperid):
    return query_db("select                                      \
                          c.commentid, c.comment, c.userid,      \
                                           c.createtime,         \
                          u.username                             \
                          from                                   \
                               comments as c,                    \
                               users as u                        \
                          where c.userid = u.userid and          \
                                c.paperid = ?                    \
                          order by c.commentid                   \
                          ",
                     [paperid])


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


def likes(paperid):
    return query_db(
        "select count(*) as c                   \
        from likes                              \
        where paperid=?",
        [paperid],
        one=True)['c']

def liked_by(paperid):
    return query_db(
        "select u.username as username          \
        from likes as l, users as u             \
        where l.userid = u.userid and           \
        l.paperid=?",
        [paperid])
