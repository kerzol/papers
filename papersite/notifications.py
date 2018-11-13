### Notifications
###############################
                  ##################
            ############
from datetime import datetime
from papersite import app
import difflib
from papersite.email import send_mail
from papersite.db import (query_db, get_paper_w_uploader,
                          get_notifs,
                          get_authors, get_comment, get_uploader)
from papersite.user import (get_user_id,  user_authenticated,
                            ANONYMOUS)
from flask import url_for
from flask import session, flash, redirect, url_for, render_template

## TODO: store notifs in db

## We notify users who liked, commented this paper
##   or participated in the colloborative discussion.
def users_to_notify(paperid):
  who_like = who_likes(paperid)
  who_comment = commentators(paperid)

  users = who_like + who_comment
  ## We notify union of all these users
  ## but not the current_user (who make the action)
  ## and ANONYMOUS
  current_user_id = get_user_id()
  users = list(
    {v['userid']:v for v in users
     if v['userid'] != current_user_id and
        v['userid'] != ANONYMOUS}.values())
  return users

## select users who likes the paper
def who_likes(paperid):
  return query_db(
    "select u.*                             \
    from likes as l, users as u             \
    where l.userid = u.userid and           \
    l.paperid = ?                           ",
    [paperid])

## select users that commented the paper
## TODO: tree of comments
def commentators(paperid):
  return query_db(
    "select u.*                             \
    from comments as c, users as u          \
    where c.userid = u.userid and           \
          c.deleted_at is null and          \
          c.paperid = ?", [paperid])

## Currently, we notify users that liked at least one paper
##
## from the same uploader
## This behavior will change in the near future:
## user will follow other user, author, etc.
##
## TODO add maybe commented papers?
def users_to_notify_about_new_paper(paperid):
  users = query_db(
    "select distinct users.*                \
    from users as users,                    \
         likes as likes,                    \
         papers as papers_by_uploader,      \
         papers as newpapers,               \
         users as uploaders                 \
    where                                   \
         likes.userid = users.userid and    \
         likes.paperid = papers_by_uploader.paperid and \
         papers_by_uploader.userid = uploaders.userid and  \
         uploaders.userid = newpapers.userid   and  \
         newpapers.paperid = ?",
    [paperid])
  ## We notify union of all these users
  ## but not the current_user (who make the action)
  ## and ANONYMOUS
  current_user_id = get_user_id()
  users = list(
    {v['userid']:v for v in users
     if v['userid'] != current_user_id and
        v['userid'] != ANONYMOUS}.values())
  return users

def comment_was_added(paperid, commentid):
  # TODO: transform latex to smth more human readable
  url = url_for('onepaper', paperid=paperid, _external=True)
  url = url + '#comment-' + str(commentid)
  template = "%s,\n\n\
User '%s' just commented a paper you liked, uploaded or commented, or participated in the related discussion. \n\
Paper title: %s\n\
Comment:\n\n\
%s\n\n\
Url: %s\n\n\
Have a nice day,\n\
Papers' team\n\n\
P.S. If you wish so you can unsubscribe from notifications using this: %s\
"
  paper = get_paper_w_uploader(paperid)
  users = users_to_notify(paperid)
  comment = get_comment(commentid)
  for u in users:
    unsubscribe = url_for('mute_email_notifs', _external=True)
    msg = template % (u['username'],
                      comment['username'],
                      paper['title'],
                      comment['comment'],
                      url,
                      unsubscribe)
    # todo save message to notifs table
    send_mail(u['email'], msg, 'New comment for paper: %s' % (paper['title']))


def new_paper_was_added(paperid):
  url = url_for('onepaper', paperid=paperid, _external=True)
  paper = get_paper_w_uploader(paperid)
  authors = ", ".join([a['fullname'] for a in get_authors(paperid)])
  template = "Hello %s,\n\n\
a new paper was added to Papersˠ. The paper may interest you.\n\
Title: %s\n\
Authors: %s\n\
Uploader: %s\n\
Url: %s\n\n\
Have a good day,\n\
Papers' team\n\n\
P.S. If you wish so you can unsubscribe from notifications using this: %s\
"
  users = users_to_notify_about_new_paper(paperid)
  for u in users:
    unsubscribe = url_for('mute_email_notifs', _external=True)
    msg = template % (u['username'],
                      paper['title'],
                      authors,
                      paper['username'],
                      url,
                      unsubscribe)
    # todo save message to notifs table
    send_mail(u['email'], msg, 'New paper: %s' % (paper['title']))





### Frontend stuff
###############################

@app.template_filter('short_datetime')
def short_format_datetime(value):
    datetime_object = datetime.strptime(value, ("%Y-%m-%d %H:%M:%S"))
    return datetime_object.strftime('%A %d %b - %H:%M')

@app.template_filter('short_date')
def short_format_date(value):
    datetime_object = datetime.strptime(value, ("%Y-%m-%d %H:%M:%S"))
    return datetime_object.strftime('%A %d %b')

@app.route('/news')
def last_week_updates():

  # example link
  # https://papers-gamma.link/paper/52/#comment-1055

  ## Every notif is a tuple (link, text, createtime, username, type)
  ## TODO: use notifs table
  papers_n_comments = query_db(
         "select '/paper/' || p.paperid as link,   \
                  p.title as text,            \
                  p.createtime as createtime, \
                  u.username as username,     \
                  'paper' as type             \
           from papers as p                   \
                left join users as u on p.userid = u.userid   \
           where deleted_at is null                           \
                 and p.createtime > date('now','-10 days')    \
          UNION                                               \
          select                                              \
                 '/paper/' || c.paperid || '/#comment-' || c.commentid as link,  \
                 c.comment as text,                     \
                 c.createtime as createtime,            \
                 u.username as username,                \
                 'comment' as type                      \
                 from                                   \
                      comments as c                     \
                      left join users as u on c.userid = u.userid  \
                 where                                       \
                     c.deleted_at is null and                \
                     c.createtime > date('now','-10 days')    \
          \
          order by createtime desc \
        ")

  return render_template('news.html', 
                         notifs=papers_n_comments)



@app.route('/lastmonth')
def last_month_updates():

  # example link
  # https://papers-gamma.link/paper/52/#comment-1055

  papers = query_db(
         "select '/paper/' || p.paperid as link,    \
                  p.title as text,                  \
                  p.createtime as createtime,       \
                  u.username as username,           \
                  (select count(*) from comments c  \
                     where c.paperid = p.paperid    \
                       and c.deleted_at is null     \
                  ) as count_comment                \
           from papers as p                         \
                left join users as u on p.userid = u.userid       \
           where p.deleted_at is null                             \
                 and p.createtime > date('now','-30 days')        \
        ")
  return render_template('lastmonth.html',
                         notifs=papers)
