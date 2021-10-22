# Search & Catalog
###############################
##################
############
from papersite import app
from flask import request, render_template, flash, redirect, url_for
from papersite.db import (query_db, get_db, get_domains, get_keywords, get_authors,
                          delete_author, delete_domain, delete_tag, delete_paper,
                          delete_papers_domain, delete_papers_authors, delete_papers_tags)
from papersite.user import (get_user_id, is_super_admin, is_author_of_paper,
                            is_author_of_comment, user_authenticated, ANONYMOUS)


def render_catalog(template_name, **context):
    domains = query_db("select * from domains order by domainname")
    keywords = query_db("select * from keywords order by keyword")
    authors = query_db("select * from authors order by fullname")
    users = query_db(
        "select * from users where valid = 1 or userid = 1 order by username")
    return render_template(template_name,
                           domains=domains,
                           keywords=keywords,
                           authors=authors,
                           users=users,
                           **context)

# add descriptions to the papers

def with_description(papers):
    for p in papers:
        p['domains'] = get_domains(p['paperid'])
        p['keywords'] = get_keywords(p['paperid'])
        p['authors'] = get_authors(p['paperid'])
    return papers


@app.route('/user/<string:name>', methods=['GET'])
def userinfo(name):
    u = query_db("select * from users where username = ?",
                 [name], one=True)
    if (u is None):
        return render_catalog('catalog/oneuser.html',
                              error="User " +
                              name + " is not found",
                              username=name)
    papers = query_db("select p.* from papers as p, likes as l   \
                     where                                     \
                      p.deleted_at is null and                 \
                      p.paperid = l.paperid and                \
                           l.userid = ?                        \
                     order by l.liketime desc", [u['userid']])
    return render_catalog('catalog/oneuser.html',
                          papers=with_description(papers),
                          username=u['username'])


@app.route('/domain/<string:domainname>', methods=['GET'])
def domain(domainname):
    domain = query_db("select domainid from domains where      \
                       domainname = ?",
                      [domainname], one=True)
    domain_not_assc = query_db('SELECT domainid FROM domains WHERE domainname = ?  \
                                and domainid not in (SELECT DISTINCT domainid FROM papers_domains)',[domainname])
    if (domain is None):
        return render_catalog('catalog/papers-in-domain.html',
                              error="Domain " +
                              domainname + " not found",
                              domainname=domainname)
    domainid = domain['domainid']
    papers = query_db("select p.*                                \
                     from papers as p,                         \
                          papers_domains as pd                 \
                     where p.deleted_at is null and            \
                           p.paperid=pd.paperid                \
                           and pd.domainid = ?                 \
                     order by p.lastcommentat desc", [domainid])
    return render_catalog('catalog/papers-in-domain.html',
                          entry=domain,
                          papers=with_description(papers),
                          domain_not_assc=domain_not_assc,
                          domainname=domainname)


@app.route('/tag/<string:keyword>', methods=['GET'])
def keyword(keyword):
    k = query_db("select keywordid from keywords where      \
                       keyword = ?",
                 [keyword], one=True)
    tag_not_assc = query_db('SELECT keyword FROM keywords WHERE keyword = ?  \
                                and keywordid not in (SELECT DISTINCT keywordid FROM papers_keywords)',[keyword])
    if (k is None):
        return render_catalog('catalog/papers-with-keyword.html',
                              error="Tag " +
                              keyword + " is not found",
                              keyword=keyword)
    keywordid = k['keywordid']
    papers = query_db("select p.*                                \
                     from papers as p,                         \
                          papers_keywords as pk                \
                     where                                     \
                           p.deleted_at is null and            \
                           p.paperid=pk.paperid and            \
                           pk.keywordid = ?                    \
                     order by p.lastcommentat desc", [keywordid])
    return render_catalog('catalog/papers-with-keyword.html',
                          entry=k,
                          papers=with_description(papers),
                          tag_not_assc=tag_not_assc,
                          keyword=keyword)


@app.route('/author/<string:fullname>', methods=['GET'])
def author(fullname):
    a = query_db("select authorid from authors where      \
                       fullname = ?",
                 [fullname], one=True)
    author_not_assc = query_db('SELECT authorid FROM authors WHERE fullname = ?  \
                                and authorid not in (SELECT DISTINCT authorid FROM papers_authors)',[fullname])
    if (a is None):
        return render_catalog('catalog/papers-of-author.html',
                              error="Author " +
                              fullname + " is not found",
                              fullname=fullname)
    authorid = a['authorid']
    papers = query_db("select p.*                                \
                     from papers as p,                         \
                          papers_authors as pa                 \
                     where                                     \
                           p.deleted_at is null and            \
                           p.paperid=pa.paperid and            \
                           pa.authorid = ?                     \
                     order by p.lastcommentat desc", [authorid])
    return render_catalog('catalog/papers-of-author.html',
                          entry=a,
                          papers=with_description(papers),
                          author_not_assc=author_not_assc,
                          fullname=fullname)


@app.route('/catalog', methods=['GET'])
def catalog():
    if request.args.get('q'):
        # Check if the string q is white space?
        q = '%' + request.args.get('q') + '%'
        papers = query_db("select * from papers                    \
                         where                                     \
                               deleted_at is null and              \
                               lower(title) like  lower(?)         \
                         order by title", [q])
        ##### Search by Author #####
        papers += query_db("select p.* from                        \
                            papers p, authors a, papers_authors pa \
                            where                                  \
                                p.paperid = pa.paperid  and        \
                                a.authorid = pa.authorid and       \
                                p.deleted_at is null and           \
                                lower(a.fullname) like lower(?)    \
                            order by title", [q])
        ##### Search by Domain #####
        papers += query_db("select p.* from                        \
                            papers p, domains d, papers_domains pd \
                            where                                  \
                                p.paperid = pd.paperid  and        \
                                d.domainid = pd.domainid and       \
                                p.deleted_at is null and           \
                                lower(d.domainname) like lower(?)  \
                            order by title", [q])
        ##### Search by Keyword #####
        papers += query_db("select p.* from                          \
                            papers p, keywords k, papers_keywords pk \
                            where                                    \
                                p.paperid = pk.paperid  and          \
                                k.keywordid = pk.keywordid and       \
                                p.deleted_at is null and             \
                                lower(k.keyword) like lower(?)       \
                            order by title", [q])
    else:
        papers = []
    return render_catalog('catalog/catalog-search.html',
                          papers=with_description(papers))


####################### Modifications by Devhub01 ##############################

##### Domains #####
@app.template_filter('can_edit_domain')
def can_edit_domain(domainname):
    return can_delete_domain(domainname)

@app.template_filter('can_delete_domain')
def can_delete_domain(domainname):
    userid = get_user_id()
    if (userid == ANONYMOUS):
        return False
    else:
        return is_super_admin(userid)

##### Authors #####
@app.template_filter('can_edit_author')
def can_edit_author(fullname):
    return can_delete_author(fullname)

@app.template_filter('can_delete_author')
def can_delete_author(fullname):
    userid = get_user_id()
    if (userid == ANONYMOUS):
        return False
    else:
        return is_super_admin(userid)

##### Tags #####
@app.template_filter('can_edit_tag')
def can_edit_tag(tagname):
    return can_delete_tag(tagname)

@app.template_filter('can_delete_tag')
def can_delete_tag(tagname):
    userid = get_user_id()
    if (userid == ANONYMOUS):
        return False
    else:
        return is_super_admin(userid)

##### Deleting/Modifying the domains #####
@app.route('/domain/delete/<string:domainname>', methods=['GET'])
def delete_domain_with_check(domainname):
    if can_delete_domain(domainname):
        dom = query_db("select * from domains where domainname = ?",
                     [domainname], one=True)
        delete_domain(domainname)
        delete_papers_domain(dom['domainid'])
        flash('You successfully removed the domain')
        return redirect(url_for('catalog'))
    else:
        return "<h1>Forbidden</h1>", 403

@app.route('/domain/edit/<string:domainname>', methods=['GET', 'POST'])
def edit_domain(domainname):
    if not can_delete_domain(domainname):
        return "<h1>It's forbidden, my dear</h1>", 403
    error = None
    domain = query_db("select *     \
                     from domains   \
                     where domainname = ?",
                      [domainname], one=True)

    if request.method == 'GET':
        request.form.id = domain['domainid']
        request.form.name = domain['domainname']

    if request.method == 'POST':
        if request.form['name'] == "":
            error = 'Please enter a valid name'

        else:
            con = get_db()
            with con:
                con.execute('update domains set domainname = ? \
                            where domainid = ? ',
                            [request.form['name'], request.form['id']])
                flash('You successfully modified the domain')
                return redirect(url_for('domain', domainname=request.form['name']))
    return render_template('catalog/edit.html',
                           entry=domain,
                           editname="domain",
                           error=error,
                           name=domainname,
                           titleP="Edit the domain",
                           domains=query_db("select * from domains where not (domainname = ?)", [domainname]))

##### Deleting/Modifying the Authors ######
@app.route('/author/delete/<string:fullname>', methods=['GET'])
def delete_author_with_check(fullname):
    if can_delete_author(fullname):
        author = query_db("select * from authors where fullname = ?",
                          [fullname], one=True)
        delete_author(fullname)
        delete_papers_authors(author['authorid'])
        flash('You successfully removed the author')
        return redirect(url_for('catalog'))
    else:
        return "<h1>Forbidden</h1>", 403

@app.route('/author/edit/<string:fullname>', methods=['GET', 'POST'])
def edit_author(fullname):
    if not can_delete_author(fullname):
        return "<h1>It's forbidden, my dear</h1>", 403
    error = None
    author = query_db("select *     \
                     from authors   \
                     where fullname = ?",
                      [fullname], one=True)

    if request.method == 'GET':
        request.form.id = author['authorid']
        request.form.name = author['fullname']
    if request.method == 'POST':
        if request.form['name'] == "":
            error = 'Please enter a valid name'
        else:
            con = get_db()
            with con:
                con.execute('update authors set fullname = ? \
                            where authorid = ?',
                            [request.form['name'], request.form['id']])
                flash('You successfully modified the author')
                return redirect(url_for('author',fullname=request.form['name']))
    return render_template('catalog/edit.html',
                        editname="author",
                        error=error,
                        name=fullname,
                        titleP="Edit the author",
                        authors=query_db("select * from authors where not (fullname = ?)",[fullname]))


###### Deleting/Modifying the tags ######
@app.route('/tag/delete/<string:keyword>', methods=['GET'])
def delete_tag_with_check(keyword):
    if can_delete_tag(keyword):
        tag = query_db("select * from keywords where keyword = ?",
                       [keyword], one=True)
        delete_tag(keyword)
        delete_papers_tags(tag['keywordid'])

        flash('You successfully removed the tag')
        return redirect(url_for('catalog'))
    else:
        return "<h1>Forbidden</h1>", 403


@app.route('/tag/edit/<string:keyword>', methods=['GET', 'POST'])
def edit_tag(keyword):
    if not can_delete_tag(keyword):
        return "<h1>It's forbidden, my dear</h1>", 403
    error = None
    tag = query_db("select *     \
                     from keywords   \
                     where keyword = ?",
                     [keyword], one=True)

    if request.method == 'GET':
        request.form.id = tag['keywordid']
        request.form.name = tag['keyword']

    if request.method == 'POST':
        if request.form['name'] =="":
            error = 'Please fill the name'
        else:
            con = get_db()
            with con:
                con.execute('update keywords set keyword = ? \
                                    where keywordid = ?',
                            [request.form['name'], request.form['id']])
                flash('You successfully modified the tag')
                return redirect(url_for('keyword',
                                        keyword=request.form['name']))
    return render_template('catalog/edit.html',
                           editname="tag",
                           error=error,
                           name=keyword,
                           titleP="Edit the tag",
                           keywords=query_db("select * from keywords where not (keyword = ?)", [keyword]))
