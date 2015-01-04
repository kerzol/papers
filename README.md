Papersᵞ — Discussing board for scientific papers 
================================================

Install python3, flask, sqlite3, ghostscript


Installation
------------

0. run 'git submodule init && git sumbodule update' to fetch required librarires (MathJax and marked)

1. ./clear.sh will initialize sqlite database, pdf's storage and log directory

2. Copy papersite/config.py.example to papersite/config.py
 
3. Read, understand and modify papersite/config.py.
   Do not forget to change SALT1, SALT2 and mail-server's parameters.

4. ./run.sh
