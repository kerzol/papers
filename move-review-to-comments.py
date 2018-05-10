from papersite import app
from papersite.db import (query_db, get_authors, get_domains, get_db,
                          get_review, get_keywords, get_comments,
                          liked_by)

with app.app_context():
  papers = query_db("select * from papers order by paperid")
  for p in papers:
    review = get_review(p['paperid'])
    print ( 'Paper id: ' + str(p['paperid'] ) )
    print ( 'Paper name: ' + p['title'] )
    print ( 'Review: ' )
    if (review is not None
        and review['review'] != 'Feel free to start an awesome discussion.'):
      con = get_db()
      with con:
        con.execute('insert into comments \
        (commentid,comment,userid,paperid) \
        values (?,?,?)',
                    [
                      -1,
                      review['review'],
                      review['userid'],
                      p['paperid']
                    ])
    print ('\n\n')
