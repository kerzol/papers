### Notifications
###############################
                  ##################
            ############
            
import difflib
from papersite.email import send_mail
from papersite.db import (query_db, get_paper_w_uploader,
                          get_authors, get_comment,
                          get_review, get_review_before_last)
from papersite.user import get_user_id,  user_authenticated
from flask import url_for
from flask import session, flash, redirect, url_for

## TODO: store notifs in db

## We notify users liked this paper
## It's different from papersite.db.liked_by, caz here we want
## all user props, not only their names
def users_to_notify(paperid):
  ## get liked users
  ## avoiding self-notifications
  users = query_db(
    "select u.*                             \
    from likes as l, users as u             \
    where l.userid = u.userid and           \
    l.paperid = ? and u.userid <> ?         ",
    [paperid, get_user_id() ])
  ## then add the author of the paper, but not 
  ## the user with userid=1. He is an anonymous stranger.
  ## He cannot into notifications.
  author = query_db(
    "select u.*                     \
     from users as u, papers as p   \
     where u.userid = p.userid      \
     and p.paperid = ? and u.userid <> ? and u.userid <> 1",
    [paperid, get_user_id() ], one=True)

  if author is not None:
    users.append(author)
  return users

## Currently, we notify users that liked at least one paper
## from the same uploader
## This behavior will change in the near future:
## user will follow other user, author, etc.
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
User '%s' just changed the collaborative discussion about a paper you liked or uploaded.\n\n\
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
User '%s' just commented a paper you liked or uploaded.\n\
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
