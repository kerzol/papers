INSERT INTO domains(domainid, domainname) VALUES(1, 'Complex networks');
INSERT INTO domains(domainid, domainname) VALUES(2, 'Artificial intelligence');
INSERT INTO domains(domainid, domainname) VALUES(3, 'Fake science');

INSERT INTO papers(paperid, title, getlink, userid) 
       VALUES (1,
       'Peaks and valleys in the size distribution of shortest path subgraphs', '/memory/pdfs/article-revisited2.pdf', 1);
insert into papers_domains (paperid, domainid)
       values (1,1);

INSERT INTO papers(paperid, title, getlink, userid) 
       VALUES (2,'II', '/memory/pdfs/II.pdf', 1);
insert into papers_domains (paperid, domainid)
       values (2,2);

INSERT INTO papers(paperid, title, getlink, userid)
       VALUES (3,'On the completeness of commutative factors', 
       '/memory/pdfs/wood.pdf', 1);
insert into papers_domains (paperid, domainid)
       values (3,3);
insert into papers_domains (paperid, domainid)
       values (3,2);

insert into keywords (keywordid, keyword)
       values (1,'lorem impsum');
insert into keywords (keywordid, keyword)
       values (2,'dolorem');
insert into keywords (keywordid, keyword)
       values (3,'kanji');


insert into papers_keywords (paperid,keywordid)
       values (1,1);

insert into papers_keywords (paperid,keywordid)
       values (1,2);

insert into papers_keywords (paperid,keywordid)
       values (1,3);



insert into authors (authorid, fullname)
       values (1, 'Sergey Kirgizov');


insert into authors (authorid, fullname)
       values (2, 'Clémence Magnien');

insert into papers_authors (paperid, authorid)
       values (1,1);

insert into papers_authors (paperid, authorid)
       values (1,2);

INSERT INTO comments(comment, userid, paperid) VALUES (

'Sed ut perspiciatis, unde omnis iste natus error sit voluptatem
 accusantium doloremque laudantium, totam rem aperiam eaque ipsa, quae
 ab illo inventore veritatis et quasi architecto beatae vitae dicta

 $$\aleph \stackrel{?}{\to} \beth $$


 sunt, explicabo. Nemo enim ipsam voluptatem, quia voluptas sit,
 aspernatur aut odit aut fugit, sed quia consequuntur magni dolores
 eos, qui ratione voluptatem sequi nesciunt'

,1,1);


INSERT INTO comments(comment, userid, paperid) VALUES (

'Lorem ipsum dolor sit amet:

 $$
 \Gamma(z) = \int_0^\infty t^{z-1}e^{-t}dt\,.
 $$
'

,1,1);


INSERT INTO comments(comment, userid, paperid) VALUES (

'Ramanujan was right!

$$
\frac{1}{\Bigl(\sqrt{\phi \sqrt{5}}-\phi\Bigr) e^{\frac25 \pi}} =
1+\frac{e^{-2\pi}} {1+\frac{e^{-4\pi}} {1+\frac{e^{-6\pi}}
{1+\frac{e^{-8\pi}} {1+\ldots} } } }
$$

But from this paper follows that Ramanujan was wrong, therefore you
made a mistake somewhere.
'

,1,1);

INSERT INTO comments(comment, userid, paperid) VALUES (

'Ramanujan was right!

$$
\frac{1}{\Bigl(\sqrt{\phi \sqrt{5}}-\phi\Bigr) e^{\frac25 \pi}} =
1+\frac{e^{-2\pi}} {1+\frac{e^{-4\pi}} {1+\frac{e^{-6\pi}}
{1+\frac{e^{-8\pi}} {1+\ldots} } } }
$$

But from this paper follows that Ramanujan was wrong, therefore you
made a mistake somewhere.
'

,1,2);
