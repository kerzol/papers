### Notifications
###############################
                  ##################
            ############

from papersite.email import send_mail
from papersite.db import (query_db)

## TODO: store notifs in db

## We notify users liked this paper
## It's different from papersite.db.liked_by because here we want
## all user props, not only their names
def users_to_notify(paperid):
  return query_db(
    "select u.*                             \
    from likes as l, users as u             \
    where l.userid = u.userid and           \
    l.paperid = ?",
    [paperid])

## Currently, we notify users liked at laest one paper
## from the same uploader
## This behavior will change in the near future:
## user will follow other user, author, etc.
def users_to_notify_about_new_paper(paperid):
  return query_db(
    "select u.*                             \
    from likes as likes,                    \
         users as users,                    \
         papers as likedpapers,             \
         papers as newpapers,               \
         users as uploaders                 \
    where                                   \
         likes.userid = users.userid and    \
         likes.paperid = likedpapers.paperid and \
         likedpapers.userid = uploaders.userid   \
         uploasders.userid = newpapers.userid
         newpapers.paperid = ?",
    [paperid])


def review_was_changed(paperid, reviewid):
  message = 'wdiff of old dicsussion and new one'
  users = users_to_notify(paperid)
  for u in users:
    send_mail(usermail, message)

def comment_was_added(paperid, commentid):
  message = 'new comment by someone'
  users = users_to_notify(paperid)
  for u in users:
      send_mail(usermail, message)

def new_paper_was_added(paperid):
  message = 'paper was added'
  users = users_to_notify_about_new_paper(paperid):
  for u in users:
    send_mail(usermail, message)
