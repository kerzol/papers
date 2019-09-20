### Search & Catalog
###############################
                  ##################
            ############
from papersite import app
from flask import request, render_template
from papersite.db import (query_db, get_domains,
                          get_keywords, get_authors)

def render_catalog(template_name, **context):
    domains=query_db ("select * from domains order by domainname")
    keywords=query_db ("select * from keywords order by keyword")
    authors=query_db ("select * from authors order by fullname")
    users=query_db ("select * from users where valid = 1 or userid = 1 order by username")
    return render_template(template_name,
                           domains=domains,
                           keywords=keywords,
                           authors=authors,
                           users=users,
                           **context)

# add descriptions to the papers 
def with_description (papers):
    for p in papers:
        p['domains']=get_domains(p['paperid'])
        p['keywords']=get_keywords(p['paperid'])
        p['authors']=get_authors(p['paperid'])
    return papers

@app.route('/user/<string:name>', methods=['GET'])
def userinfo(name):
    u=query_db("select * from users where username = ?",
                      [name],one=True)
    if (u is None):
        return render_catalog('catalog/oneuser.html', 
                               error = "User " + \
                                        name + " is not found",
                              username=name)
    papers=query_db("select p.* from papers as p, likes as l   \
                     where                                     \
                      p.deleted_at is null and                 \
                      p.paperid = l.paperid and                \
                           l.userid = ?                        \
                     order by l.liketime desc",[u['userid']])    
    return render_catalog('catalog/oneuser.html',
                           papers=with_description(papers),
                           username=u['username'])

@app.route('/domain/<string:domainname>', methods=['GET'])
def domain(domainname):
    d=query_db("select domainid from domains where      \
                       domainname = ?", 
                      [domainname], one=True)
    if (d is None):
        return render_catalog('catalog/papers-in-domain.html', 
                               error = "Domain " + \
                                        domainname + " not found",
                               domainname=domainname)
    domainid=d['domainid']
    papers=query_db("select p.*                                \
                     from papers as p,                         \
                          papers_domains as pd                 \
                     where p.deleted_at is null and            \
                           p.paperid=pd.paperid                \
                           and pd.domainid = ?                 \
                     order by p.lastcommentat desc",[domainid])
    return render_catalog('catalog/papers-in-domain.html',
                           papers=with_description(papers), 
                           domainname=domainname)

@app.route('/tag/<string:keyword>', methods=['GET'])
def keyword(keyword):
    k=query_db("select keywordid from keywords where      \
                       keyword = ?", 
                      [keyword], one=True)
    if (k is None):
        return render_catalog('catalog/papers-with-keyword.html', 
                               error = "Tag " + \
                                        keyword + " is not found",
                               keyword=keyword)
    keywordid=k['keywordid']
    papers=query_db("select p.*                                \
                     from papers as p,                         \
                          papers_keywords as pk                \
                     where                                     \
                           p.deleted_at is null and            \
                           p.paperid=pk.paperid and            \
                           pk.keywordid = ?                    \
                     order by p.lastcommentat desc",[keywordid])
    return render_catalog('catalog/papers-with-keyword.html',
                           papers=with_description(papers),
                           keyword=keyword)

@app.route('/author/<string:fullname>', methods=['GET'])
def author(fullname):
    a=query_db("select authorid from authors where      \
                       fullname = ?", 
                      [fullname], one=True)
    if (a is None):
        return render_catalog('catalog/papers-of-author.html', 
                               error = "Author " + \
                                        fullname + " is not found",
                               fullname=fullname)
    authorid=a['authorid']
    papers=query_db("select p.*                                \
                     from papers as p,                         \
                          papers_authors as pa                 \
                     where                                     \
                           p.deleted_at is null and            \
                           p.paperid=pa.paperid and            \
                           pa.authorid = ?                     \
                     order by p.lastcommentat desc",[authorid])
    return render_catalog('catalog/papers-of-author.html',
                           papers=with_description(papers),
                           fullname=fullname)


@app.route('/catalog', methods=['GET'])
def catalog():
    if request.args.get('q'):
        q = '%' + request.args.get('q') + '%'
        papers=query_db("select * from papers                      \
                         where                                     \
                               deleted_at is null and              \
                               lower(title) like  lower(?)         \
                         order by title",[q])
    else: 
        papers = []
    return render_catalog('catalog/catalog-search.html',
                           papers=with_description(papers))


