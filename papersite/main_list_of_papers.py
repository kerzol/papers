### Main list of papers
###############################
                  ##################
            ############
from papersite import app
from papersite.db import (query_db, get_authors, get_domains,
                          get_keywords, get_comments)
from flask import redirect, url_for, render_template
from math import ceil
from papersite.user import get_user_id




def previews(seq):
    """ for a sequence of papers, i.e. 'select * from papers',
        we extract additional info about comments, authors, etc.
        In order to render the list of previews <paper|comments>.
        We use this at main page and also at sites of users
    """
    likes = {}
    liked = {}
    commentsHead = {}
    commentsTail = {}
    for paper in seq:
        likes[paper['paperid']] = query_db(
                         "select count(*) as c                   \
                          from likes                             \
                          where paperid=?",
            [paper['paperid']],
            one=True)['c']

        liked[paper['paperid']] = query_db(
            "select *                        \
            from likes                       \
            where paperid=? and userid=?",
            [paper['paperid'],get_user_id()],
            one=True)


        commentsHead[paper['paperid']] = query_db(
                       "                                         \
                          select                                 \
                          c.commentid, c.comment, c.userid,      \
                                           c.createtime,         \
                          u.username                             \
                          from comments as c, users as u         \
                          where                                  \
                                c.userid = u.userid and          \
                                c.paperid = ?                    \
                          order by c.commentid                   \
                         limit 2                                 \
                       ",
            [paper['paperid']]);

        # construct a list of comments ids
        
        
        ids_in_head=[  str(c['commentid']) for c in 
                   commentsHead[paper['paperid']]]

        good_injection='(' + ','.join(ids_in_head) + ')';
        
        # donot cosider a comments with id from the list head
        # we cannot bind into 'in (?)', therefore we inject!
        commentsTail[paper['paperid']] = query_db(
                "select * from                            \
                  (                                       \
                   select                                 \
                   c.commentid, c.comment, c.userid,      \
                   c.createtime,                          \
                   u.username                             \
                  from comments as c, users as u          \
                  where                                          \
                   c.userid = u.userid and                       \
                   c.commentid not in " + good_injection + " and \
                   c.paperid = ?                                 \
                  order by c.commentid desc                      \
                  limit 2)                                       \
                 order by commentid                              \
                       ",
            [paper['paperid']]);

    return (commentsTail, commentsHead, likes, liked)

@app.route('/all/')
@app.route('/all/page/<int:page>')
def all(page=1):

    count=query_db("select count(*) as c from papers",one=True)['c']
    # how many papers on page?
    onpage = 5
    maxpage = int(ceil(float(count)/onpage))

    seq=query_db("select *                                       \
                    from papers as p                             \
                  order by p.lastcommentat DESC                  \
                  limit ?, ?", [(page-1)*onpage,onpage])

    commentsTail, commentsHead, likes, liked = previews(seq)

    return render_template('main-list.html', seq=seq,
                           commentsTail=commentsTail, 
                           commentsHead=commentsHead,
                           likes=likes,liked=liked,
                           maxpage=maxpage, curpage=page,
                           headurl='/all')


@app.route('/')
@app.route('/page/<int:page>')
def index(page=1):
    # if user_authenticated():
    #     return "home page (/username + friend's posts) of user under id " + str(get_user_id()),200
    # else:
    #     return redirect(url_for('all'))
    return redirect(url_for('all'))
