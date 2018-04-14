### Notifications
###############################
                  ##################
            ############
            
import difflib
from papersite.email import send_mail
from papersite.db import (query_db, get_paper_w_uploader,
                          get_authors, get_comment, get_uploader,
                          get_review, get_review_before_last)
from papersite.user import (get_user_id,  user_authenticated,
                            ANONYMOUS)
from flask import url_for
from flask import session, flash, redirect, url_for

## TODO: store notifs in db

## We notify users who liked, commented this paper
##   or participated in the colloborative discussion.
def users_to_notify(paperid):
  who_like = who_likes(paperid)
  who_comment = commentators(paperid)
  who_discuss = discussion_participators(paperid)

  print (who_like)
  print (who_comment)
  print (who_discuss)
  users = who_like + who_comment + who_discuss
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

## select users that participated in the
## colloborative discussion of this paper
def discussion_participators(paperid):
    return query_db("select u.*             \
            from reviews as r, users as u   \
            where r.userid = u.userid and   \
                  r.paperid = ?",
            [paperid])

## Currently, we notify users that liked at least one paper
##
## from the same uploader
## This behavior will change in the near future:
## user will follow other user, author, etc.
##
## TODO add maybe commented, discussed papers?
def users_to_notify_about_new_paper(paperid):
  return query_db(
    "select users.*                         \
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

def review_was_changed(paperid):
  # TODO: transform latex to smth more human readable
  url = url_for('onepaper', paperid=paperid, _external=True)
  url = url + '#review'
  template = "Hello %s,\n\n\
User '%s' just changed the paper collaborative discussion. It may interests you.\n\n\
Paper title: %s\n\
Changes:\n\n\
%s\n\n\
Url: %s\n\
Papers' team"
  # word diff
  users = users_to_notify(paperid)
  last_review = get_review(paperid)
  before_last_review = get_review_before_last(paperid)
  paper = get_paper_w_uploader(paperid)
  a = (before_last_review['review'] + '\n').splitlines(keepends=True)
  b = (last_review['review'] + '\n').splitlines(keepends=True)
  diff = difflib.ndiff(a, b)
  word_diff = ''.join(diff)
  for u in users:
    msg = template % (u['username'],
                      last_review['username'],
                      paper['title'],
                      word_diff,
                      url)
    # todo save message to notifs table
    send_mail(u['email'], msg, 'News about paper: %s' % (paper['title']))


def comment_was_added(paperid, commentid):
  # TODO: transform latex to smth more human readable
  url = url_for('onepaper', paperid=paperid, _external=True)
  url = url + '#comment-' + str(commentid)
  template = "Aloha %s,\n\n\
User '%s' just commented a paper you liked, uploaded or commented, or participated in the related discussion. \n\
Paper title: %s\n\
Comment:\n\n\
%s\n\n\
Url: %s\n\n\
Have a nice day,\n\
Papers' team"
  paper = get_paper_w_uploader(paperid)
  users = users_to_notify(paperid)
  comment = get_comment(commentid)
  for u in users:
    msg = template % (u['username'],
                      comment['username'],
                      paper['title'],
                      comment['comment'],
                      url)
    # todo save message to notifs table
    send_mail(u['email'], msg, 'New comment for paper: %s' % (paper['title']))


def new_paper_was_added(paperid):
  url = url_for('onepaper', paperid=paperid, _external=True)
  paper = get_paper_w_uploader(paperid)
  authors = ", ".join([a['fullname'] for a in get_authors(paperid)])
  template = "Hello %s,\n\n\
a new paper was added to Papersˠ. The paper may interests you.\n\
Title:    %s\n\
Authors:  %s\n\
Uploader: %s\n\
Url: %s\n\n\
Have a good day,\n\
Papers' team"
  users = users_to_notify_about_new_paper(paperid)
  for u in users:
    msg = template % (u['username'],
                      paper['title'],
                      authors,
                      paper['username'],
                      url)
    # todo save message to notifs table
    send_mail(u['email'], msg, 'New paper: %s' % (paper['title']))
