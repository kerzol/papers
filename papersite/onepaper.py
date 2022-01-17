### One paper
###############################
                  ##################
            ############
import os, re, requests
import xml.etree.cElementTree as et
from papersite import app
from papersite.db import (query_db, get_db, get_authors, get_domains,
                          get_keywords, get_comment, get_comments,
                          get_insert_keyword, get_insert_author,
                          get_insert_domain, liked_by, likes,
                          delete_comment, delete_paper,
                          get_paper_w_uploader, histore_paper_info
)
from papersite.user import (get_user_id, is_super_admin, is_author_of_paper,
                            is_author_of_comment, user_authenticated, ANONYMOUS)
from werkzeug.utils import secure_filename
from flask import render_template, request, flash, redirect, url_for
from papersite.notifications import (new_paper_was_added,
                                     comment_was_added)

### Frontend stuff
###############################

@app.template_filter('is_internal_pdf')
def is_internal_pdf(link):
    return re.match('^/static/memory/pdfs/(.*)\.[Pp][Dd][Ff]$', str(link))

@app.template_filter('can_edit_comment')
def can_edit_comment(commentid):
    return can_delete_comment(commentid)

@app.template_filter('can_delete_comment')
def can_delete_comment(commentid):
    ## currently anonymous cannot delete any comments
    userid = get_user_id()
    if (userid == ANONYMOUS):
        return False
    else:
        return is_super_admin(userid) or is_author_of_comment(userid, commentid)

@app.template_filter('can_edit_paper')
def can_edit_paper(paperid):
    return can_delete_paper(paperid)

@app.template_filter('can_meta_edit_paper')
def can_meta_edit_paper(paperid):
    ## currently any registered user can edit meta information of any paper.
    ## should we make a moderation system or
    ## the system for local git-like views of PG? Smth like that:
    ## 1) User changes meta information. It affects only her own view.
    ## 2) User submits changes to global view.
    ## 3) Other members approve it.
    userid = get_user_id()
    if (userid == ANONYMOUS):
        return False
    return True
   
@app.template_filter('can_delete_paper')
def can_delete_paper(paperid):
    ## currently anonymous cannot delete any comments
    userid = get_user_id()
    if (userid == ANONYMOUS):
        return False
    else:
        return is_super_admin(userid) or is_author_of_paper(userid, paperid)


### Delete comments, papers, etc
###  Well actually we do not delete them from DB, just mark as deleted
###############################
                  ##################
            ############
            
@app.route('/delete-comment/<int:commentid>', methods=['GET'])
def delete_comment_with_check(commentid):
    if can_delete_comment(commentid):
        comment = query_db("select * from comments where commentid = ?",
                      [commentid], one=True)
        delete_comment(commentid)
        flash('You successfully removed the comment')
        return redirect(url_for('onepaper',
                                paperid=comment['paperid']))
    else:
        return "<h1>Forbidden</h1>", 403

@app.route('/paper/delete/<int:paperid>', methods=['GET'])
def delete_paper_with_check(paperid):
    if can_delete_paper(paperid):
        pap = query_db("select * from papers where paperid = ?",
                      [paperid], one=True)
        delete_paper(paperid)
        flash('You successfully removed the paper')
        return redirect(url_for('all'))
    else:
        return "<h1>Forbidden</h1>", 403


### Show paper, etc
###############################
                  ##################
            ############


@app.route('/paper/<int:paperid>', methods=['GET'])
@app.route('/paper/<int:paperid>/', methods=['GET'])
@app.route('/paper/<int:paperid>/<string:title>', methods=['GET'])
def onepaper(paperid, title = None):
    paper = get_paper_w_uploader(paperid)
    liked = query_db(
        "select count(*) as c            \
        from likes                       \
        where paperid=? and userid=?",
        [paperid,get_user_id()],
        one=True)['c']
    if paper['edited_at'] is not None:
        paper['edituser'] = query_db(
            "select username          \
             from users                \
        where userid = ?",
        [paper['edited_by']], one=True)['username']
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
                           liked=liked,
                           liked_by=liked_by(paperid))

@app.route('/comment/edit/<int:commentid>', methods=['GET','POST'])
def edit_comment(commentid):
    if not can_edit_comment(commentid):
        return "<h1>It's forbidden, my dear</h1>", 403
    error = None
    oldcomment = get_comment(commentid)
    if request.method == 'GET':
        return render_template('comment/editcomment.html', 
                               error=error,
                               comment=oldcomment,
        )
    if request.method == 'POST':
        con = get_db()
        # soft delete old comment
        delete_comment(oldcomment['commentid'])
        # create a new comment with same creation date
        # but add edited_by and edited_at info
        with con:
            con.execute('insert into comments \
                         (comment, userid, paperid, createtime, edited_at, edited_by) \
                         values (?, ?, ?, ?, datetime(), ?)',
                        [
                            request.form['comment'],
                            oldcomment['userid'],
                            oldcomment['paperid'],
                            oldcomment['createtime'],
                            get_user_id(),
                        ])
        # TODO: should we notify someone about comment edition ?
        if user_authenticated(): 
            flash('You successfully updated the comment')
        # TODO: allows anonymous to update comments
        last_c_id=query_db("SELECT last_insert_rowid() as lid",
                           one=True)['lid']
        return redirect(url_for('onepaper',
                                paperid=oldcomment['paperid'],
                                error=error)
                        + "#comment-"
                        + str(last_c_id))


@app.route('/paper/<int:paperid>/add-comment',
           methods=['POST'])
def add_comment(paperid):
    if not user_authenticated():
            return "<h1>Forbidden</h1>", 403
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
    
    # notify user about new comment
    comment_was_added(paperid, last_c_id)
    return redirect(url_for('onepaper',paperid=paperid, title = None, error=error)
                    + "#comment-"
                    + str(last_c_id))


### Add paper
###############################
                  ##################
            ############


ALLOWED_EXTENSIONS = set(['pdf','PDF'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def parse_list(list):
    return map(str.strip, list.rstrip(', ').split(','))


@app.route('/paper/add', methods=['GET','POST'])
def add_paper():
    error = None
    if request.method == 'POST':
        if not user_authenticated():
            return "<h1>Forbidden (maybe you forgot to login)</h1>", 403
        paper_file = request.files['pdf'] 
        downLoadPaper = True if (request.form['arxiv-url'] != "") else False
        if not downLoadPaper and (not paper_file or not allowed_file(paper_file.filename)):
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
            if downLoadPaper:
                # Checks if the arXiv URL is valid by getting the ID out of it.
                try:
                    arXivId = request.form['arxiv-url'].split('/abs/')[1]
                except IndexError :
                    error = 'Please enter a valid arXiv URL'
                    return render_template('paper/add.html', 
                           error=error,
                           domains=query_db ("select * from domains"),
                           keywords=query_db ("select * from keywords"),
                           authors=query_db ("select * from authors"))
                url = 'https://arxiv.org/pdf/'+arXivId
                paper_file = requests.get(url, stream= True)
            con = get_db()
            with con:
              con.execute('insert into papers(title,userid)         \
                             values (?,?)',
                             [request.form['title'], get_user_id()])

              paperid = con.execute("SELECT last_insert_rowid() as lid"
                                    ).fetchone()['lid']

              authors_ids = map(get_insert_author,
                                parse_list(request.form['authors']))
              for authorid in authors_ids:
                  con.execute('insert into papers_authors             \
                              (paperid, authorid)                     \
                              values(?,?)',[paperid, authorid])

              domains_ids = map(get_insert_domain,
                               parse_list(request.form['domains']))
              for domainid in domains_ids:
                  con.execute('insert into papers_domains             \
                               (paperid, domainid)                    \
                               values(?,?)',[paperid, domainid])

              keywords_ids = map(get_insert_keyword,
                               parse_list(request.form['keywords']))
              for keywordid in keywords_ids:
                  con.execute('insert into papers_keywords            \
                            (paperid, keywordid)                      \
                            values(?,?)',[paperid, keywordid])

              if downLoadPaper:
                    filename_pdf = arXivId+'.pdf'
                    filename_pdf = filename_pdf.replace('/', '-')
                    with open(app.config['UPLOAD_FOLDER']+'/'+filename_pdf, 'wb') as fd:
                        fd.write(paper_file.content)
                    ppdf = os.path.join(app.config['UPLOAD_FOLDER'],filename_pdf)
              else:
                    filename_pdf = str(paperid) + "-" +                       \
                        secure_filename(paper_file.filename)
                    ppdf = os.path.join(app.config['UPLOAD_FOLDER'],filename_pdf)
                    paper_file.save(ppdf)
              ## this is just a hack.
              ## In order to generate first page
              # should we use a hash value as file name ???
              filename_png = str(paperid) + ".png"
              ppng = os.path.join(app.config['PREVIEW_FOLDER'],filename_png)
              os.system('papersite/gen.sh ' + ppdf +  ' ' + ppng)
              con.execute('update papers set img = ? where paperid = ?', [filename_png, paperid])
              # end of hack

              ## Sometimes authors provide a url to their paper
              ## in this case we don't store a full paper, we use the url instead
              if request.form['url'] != "" or request.form['arxiv-url'] != "":
                  os.remove(ppdf)
                  if request.form['url'] != "":
                      url = request.form['url']
                  con.execute("update papers set getlink = ?             \
                               where paperid=?",
                              [url, paperid])
              else:
                  con.execute("update papers set getlink = ?             \
                               where paperid=?",
                              ['/static/memory/pdfs/'+filename_pdf, paperid])

              ## notify some users by email about this paper
              new_paper_was_added(paperid)
              
              flash('You successfully upload the paper')
              return redirect(url_for('onepaper',
                                    paperid=paperid,
                                    title=request.form['title']))
    return render_template('paper/add.html', 
                           error=error,
                           domains=query_db ("select * from domains"),
                           keywords=query_db ("select * from keywords"),
                           authors=query_db ("select * from authors"))


### Edit papers, comments etc
###############################
                  ##################
            ############

@app.route('/paper/meta-edit/<int:paperid>', methods=['GET','POST'])
def edit_paper_meta_information(paperid):
    ### edit Title, authors, tags and domains lists
    if not can_meta_edit_paper(paperid):
        return "<h1>It's forbidden fro you, my sweetie.</h1>", 403
    error = None
    paper = query_db("select *     \
                     from papers   \
                     where paperid = ?",
    [paperid], one=True)
    
    if request.method == 'GET':
        request.form.title = paper['title']
        request.form.authors = ", ".join([x['fullname'] for x in get_authors(paperid)])
        request.form.domains = ", ".join([x['domainname'] for x in get_domains(paperid)])
        request.form.keywords= ", ".join([x['keyword'] for x in get_keywords(paperid)])
    
    if request.method == 'POST':
        histore_paper_info(paper)
        if request.form['title'] == "":
            error = 'Please add a title'
        elif request.form['domains'] == "":
            error = 'Please specify at least one domain'
        elif request.form['authors'] == "":
            error = 'Please add some authors'
        elif request.form['keywords'] == "":
            error = 'Please add some keywords'
        else:
            con = get_db()
            with con:
              con.execute('update papers set title = ?, edited_by = ?, \
                                             edited_at = datetime()    \
                           where paperid = ?',
                             [request.form['title'], get_user_id(), paperid])
              authors_ids = map(get_insert_author,
                                parse_list(request.form['authors']))
              con.execute('delete from papers_authors where paperid = ?',
                          [paperid])
              for authorid in authors_ids:
                  con.execute('insert into papers_authors             \
                              (paperid, authorid)                     \
                              values(?,?)',[paperid, authorid])

              domains_ids = map(get_insert_domain,
                               parse_list(request.form['domains']))
              con.execute('delete from papers_domains where paperid = ?',
                          [paperid])
              for domainid in domains_ids:
                  con.execute('insert into papers_domains             \
                               (paperid, domainid)                    \
                               values(?,?)',[paperid, domainid])

              keywords_ids = map(get_insert_keyword,
                               parse_list(request.form['keywords']))
              con.execute('delete from papers_keywords where paperid = ?',
                          [paperid])
              for keywordid in keywords_ids:
                  con.execute('insert into papers_keywords            \
                            (paperid, keywordid)                      \
                            values(?,?)',[paperid, keywordid])

              ## TODO: notify some users by email about changes
              
              flash('You successfully modified the paper')
              return redirect(url_for('onepaper',
                                    paperid=paperid,
                                    title=request.form['title']))
    return render_template('paper/meta-edit.html', 
                           error=error,
                           paperid=paperid,
                           domains=query_db ("select * from domains"),
                           keywords=query_db ("select * from keywords"),
                           authors=query_db ("select * from authors"))
            

@app.route('/paper/edit/<int:paperid>', methods=['GET','POST'])
def edit_paper(paperid):
    if not can_edit_paper(paperid):
        return "<h1>It's forbidden, my dear</h1>", 403
    error = None
    paper = query_db("select *     \
                     from papers   \
                     where paperid = ?",
    [paperid], one=True)
    
    if request.method == 'GET':
        request.form.title = paper['title']
        request.form.authors = ", ".join([x['fullname'] for x in get_authors(paperid)])
        request.form.domains = ", ".join([x['domainname'] for x in get_domains(paperid)])
        request.form.keywords= ", ".join([x['keyword'] for x in get_keywords(paperid)])
        if not is_internal_pdf (paper['getlink']):
            request.form.url = paper['getlink']
    
    if request.method == 'POST':
        histore_paper_info(paper)
        paper_file = request.files['pdf']
        if paper_file and not allowed_file(paper_file.filename):
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
            with con:
              con.execute('update papers set title = ?, edited_by = ?, \
                                             edited_at = datetime()    \
                           where paperid = ?',
                             [request.form['title'], get_user_id(), paperid])
              authors_ids = map(get_insert_author,
                                parse_list(request.form['authors']))
              con.execute('delete from papers_authors where paperid = ?',
                          [paperid])
              for authorid in authors_ids:
                  con.execute('insert into papers_authors             \
                              (paperid, authorid)                     \
                              values(?,?)',[paperid, authorid])

              domains_ids = map(get_insert_domain,
                               parse_list(request.form['domains']))
              con.execute('delete from papers_domains where paperid = ?',
                          [paperid])
              for domainid in domains_ids:
                  con.execute('insert into papers_domains             \
                               (paperid, domainid)                    \
                               values(?,?)',[paperid, domainid])

              keywords_ids = map(get_insert_keyword,
                               parse_list(request.form['keywords']))
              con.execute('delete from papers_keywords where paperid = ?',
                          [paperid])
              for keywordid in keywords_ids:
                  con.execute('insert into papers_keywords            \
                            (paperid, keywordid)                      \
                            values(?,?)',[paperid, keywordid])

              if paper_file:
                  filename_pdf = str(paperid) + "-" +                       \
                                 secure_filename(paper_file.filename)
                  ppdf = os.path.join(app.config['UPLOAD_FOLDER'],filename_pdf)
                  paper_file.save(ppdf)
                  ## this is just a hack.
                  ## In order to generate first page
                  # should we use a hash value as file name ???
                  oldfilename = query_db('select img from papers where paperid = ?',
                           [paperid], one = True)['img']
                  # Two cases we have. The transformations are the following
                  # * 12312.png    -->   12312-1.png
                  # * 213123-12.png -->  213123-13.png
                  #
                  print (oldfilename)
                  if oldfilename is None:
                      oldfilename = str(paperid) + ".png" # Another hack, lol
                  ab = oldfilename.split('.')[0].split('-')
                  if len(ab) == 1:
                      # first case here, so
                      filename_png = str(paperid) + "-1.png"
                  else:
                      # second case, already updated at least once
                      # we Increment
                      incu = str(int(ab[1]) + 1)
                      filename_png = str(paperid) + "-" + incu + ".png"
                  os.remove (os.path.join(app.config['PREVIEW_FOLDER'],oldfilename))
                  ppng = os.path.join(app.config['PREVIEW_FOLDER'],filename_png)
                  os.system('papersite/gen.sh ' + ppdf +  ' ' + ppng)
                  con.execute('update papers set img = ? where paperid = ?', [filename_png, paperid])
                  # end of hack

              ## Sometimes authors provide a url to their paper
              ## in this case we don't store a full paper, we use the url instead
              if request.form['url'] != "":
                  if paper_file:
                      # a file was just uploaded, we already took the first page. It is a fair use.
                      # We delete the file
                      os.remove(ppdf)
                  else:
                      # The following magick will happens...
                      # we test if a link is to un existing papers,
                      link = paper['getlink']
                      if (is_internal_pdf(link)):
                          filename_pdf = link.replace('/static/memory/pdfs/', '')
                          ppdf = os.path.join(app.config['UPLOAD_FOLDER'],filename_pdf)
                          os.remove(ppdf)
                      # here we will delete file that was already uploaded some time ago
                      # but now was remplaced by un URL.
                  con.execute("update papers set getlink = ?             \
                               where paperid=?",
                              [request.form['url'], paperid])
              elif paper_file:
                  con.execute("update papers set getlink = ?             \
                               where paperid=?",
                              ['/static/memory/pdfs/'+filename_pdf, paperid])

              ## TODO: notify some users by email about changes
              
              flash('You successfully modified the paper')
              return redirect(url_for('onepaper',
                                    paperid=paperid,
                                    title=request.form['title']))
    return render_template('paper/edit.html', 
                           error=error,
                           paperid=paperid,
                           domains=query_db ("select * from domains"),
                           keywords=query_db ("select * from keywords"),
                           authors=query_db ("select * from authors"))


### Like a paper
###############################
                  ##################
            ############


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

### Get paper informations from ArXiv
###############################
                  ##################
            ############


@app.route('/paper/arxiv/<string:field>', methods=['GET'])
@app.route('/paper/arxiv/<string:field>/<string:paperid>', methods=['GET'])
def get_arxiv_paper(field, paperid = ""):
    error = ""
    code = 0
    if field == "" or field.isspace() :
        error = "Please enter a valid id"
        code = 400
    else:
        if paperid == "" or paperid.isspace():
            r = requests.get('http://export.arxiv.org/api/query?id_list=' + field)
        else:
            r = requests.get('http://export.arxiv.org/api/query?id_list=' + field + "/" + paperid)
        if(r.status_code != 200):
            if(r.status_code == 404):
                error = "The paper with this id was not found"
                code = 404
            elif(r.status_code == 400):
                error = "Invalid ArXiv id"
                code = 400
            else:
                error = "An error occured"
                code = r.status_code
        else:            
            content = r.content.decode("utf-8")
            content = content.replace("\n", "")
            title = re.findall("<title>(.*?)</title>",content, re.DOTALL)
            title = " ".join(title[0].split())
            authors_name = re.findall("<name>(.*?)</name>",content, re.DOTALL)
            domains = re.findall("<category term=\"(.*?)\"", content, re.DOTALL)
            paper_info = {
                "title": title,
                "authors": ",".join(authors_name),
                "domains": ",".join(domains)
            }
            return paper_info, 200
    er = {"error": error}
    return er, code
