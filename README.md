Papersᵞ — Discussing board for scientific papers 
================================================
http://papers-gamma.link

Library  of papers/preprints  written  by you.
Comfortable place to discuss articles/preprints.

Use  it to  organise  open peer  review process  or  to discuss  final
versions of  papers.  List  of papers/preprints  that you  like.  Here
"you" can  refer to  a new generation  scientific journal.   When such
journal likes  (using a symbol ☆)  a paper it means  that this article
got published.


Installation
------------

Install python3, flask, sqlite3, and ghostscript

0. run 'git submodule init && git sumbodule update' to fetch required librarires (MathJax and marked)

1. ./clear.sh will initialize sqlite database, pdf's storage and log directory

2. Copy papersite/config.py.example to papersite/config.py
 
3. Read, understand and modify papersite/config.py.
   Do not forget to change SALT1, SALT2 and mail-server's parameters.

4. ./run.sh


AUTHOR(S)
---------

Sergey Kirgizov : https://gratipay.com/kerzol/


LICENSE
-------

To the  extent possible  under law, the  author(s) have  dedicated all
copyright  and  related  and   neighboring  rights  to  this  software
(excluding third-party libraries from static/lib) to the public domain
worldwide.  This software is distributed without any warranty.

You should have received a copy of the CC0 Public Domain Dedication
along    with   this    software.   If    not,   see
<http://creativecommons.org/publicdomain/zero/1.0/>.


