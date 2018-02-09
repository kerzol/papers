### Notifications
###############################
                  ##################
            ############

from papersite.email import send_mail

## We notify users liked this paper
def get_users_to_notify(paperid):
  todo

## Currently, we notify users liked at laest one paper
## from the same uploader
## This behavior will change in the near future:
## user will follow other user, author, etc.
def get_users_to_notify_about_new_paper(paperid):
  todo

def review_was_changed(paperid, reviewid):
  message = 'wdiff of old dicsussion and new one'
  users = get_users_to_notify(paperid)
  for u in users:
    send_mail(usermail, message)

def comment_was_added(paperid, commentid):
  message = 'new comment by someone'
  users = get_users_to_notify(paperid)
  for u in users:
      send_mail(usermail, message)

def new_paper_was_added(paperid):
  message = 'paper was added'
  users = get_users_to_notify_about_new_paper(paperid):
  for u in users:
    send_mail(usermail, message)
