from subprocess import Popen, PIPE, STDOUT
from papersite.db import (get_db, query_db)
from papersite import app
from flask import (render_template, Response)

### Dump data
###############################
                  ##################
            ############
@app.route("/dump/")
def dump():
  return render_template('dump.html')

@app.route('/dump.gz')
def dumpit():
  db = get_db()
  r = Popen(
    'sqlite3 db/papers.db < db/dump.sqlite-script | gzip',
    shell = True, stdout=PIPE, stdin=PIPE)

  return Response(r.stdout, mimetype = 'application/sql')


