create table users (
  userid   INTEGER PRIMARY KEY,
  username TEXT UNIQUE,
  openid   TEXT,
  email    TEXT UNIQUE,
  password TEXT,
  about    TEXT,
  valid    INTEGER, -- 1 means valid, 0 means need a confirmation
  key      TEXT UNIQUE,
  chpasstime  TIMESTAMP,
  createtime  TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);


create table papers (
  paperid     INTEGER PRIMARY KEY,
  getlink     TEXT,
  title       TEXT,
  userid      INTEGER,
  lastcommentat       TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
  createtime          TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
  FOREIGN KEY(userid) REFERENCES users(userid)
);

create index p_index on papers(userid);
create index p_index1 on papers(lastcommentat);


create table likes (
  paperid     INTEGER,
  userid      INTEGER,
  liketime    TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
  FOREIGN KEY(paperid) REFERENCES papers(paperid),
  FOREIGN KEY(userid) REFERENCES users(userid)
);

create index l_index1 on likes (paperid);
create index l_index2 on likes (userid);
create UNIQUE index l_index3 on likes (paperid,userid);
create index l_index4 on likes (liketime);

create table domains (
  domainid    INTEGER PRIMARY KEY,
  domainname  TEXT UNIQUE
);

create table papers_domains (
  paperid   INTEGER,
  domainid  INTEGER,
  FOREIGN KEY(paperid) REFERENCES papers(paperid),
  FOREIGN KEY(domainid) REFERENCES domains(domainid)
);

create index pd_index1 on papers_domains (paperid);
create index pd_index2 on papers_domains (domainid);
create UNIQUE index pd_index3 on papers_domains (paperid,domainid);


create table keywords (
  keywordid INTEGER PRIMARY KEY,
  keyword   TEXT UNIQUE
);

create table papers_keywords (
  paperid   INTEGER,
  keywordid INTEGER,
  FOREIGN KEY(paperid) REFERENCES papers(paperid),
  FOREIGN KEY(keywordid) REFERENCES authors(keywordid)
);

create index pk_index1 on papers_keywords (paperid);
create index pk_index2 on papers_keywords (keywordid);
create UNIQUE index pk_index3 on papers_keywords (paperid, keywordid);


create table authors (
  authorid   INTEGER PRIMARY KEY,
  fullname   TEXT UNIQUE
);

create table papers_authors (
  paperid INTEGER,
  authorid INTEGER,
  FOREIGN KEY(paperid) REFERENCES papers(paperid),
  FOREIGN KEY(authorid) REFERENCES authors(authorid)
);

create index pa_index1 on papers_authors (paperid);
create index pa_index2 on papers_authors (authorid);
create unique index pa_index3 on papers_authors (paperid, authorid);

create table comments (
  commentid  INTEGER PRIMARY KEY,
  comment    TEXT,
  userid     INTEGER,
  paperid    INTEGER,
  createtime  TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
  FOREIGN KEY(userid) REFERENCES users(userid),
  FOREIGN KEY(paperid) REFERENCES papers(paperid)
);

create index c_index1 on comments (userid);
create index c_index2 on comments (paperid);

create table friends (
  userid INTEGER NOT NULL,
  friendid INTEGER NOT NULL,
  FOREIGN KEY(userid) REFERENCES users(userid),
  FOREIGN KEY(friendid) REFERENCES users(userid)
);

create index friends_index1 on friends (userid);
create index friends_index2 on friends (friendid);
create unique index friends_index3 on friends (userid, friendid);


-- Anonyomous is a user with id = 1.
-- Anonymous is a stranger.
INSERT INTO users(userid, username, valid) VALUES(1,'Stranger', 0);

-- add mute params for notifs
ALTER TABLE users
  ADD notifs_muted BOOLEAN default 0;


-- notifs
create table notifs (
  userid      INTEGER,
  text        TEXT,
  createtime  TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
  seenat      TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
  FOREIGN KEY(userid) REFERENCES users(userid)
);

create index n_user on notifs(userid);
create index n_index1 on notifs(createtime);
create index n_index2 on notifs(seenat);


-- modifications/edits

ALTER TABLE users
  ADD super_admin BOOLEAN default 0;

ALTER TABLE comments
  ADD deleted_at TIMESTAMP DEFAULT NULL;

ALTER TABLE papers
  ADD deleted_at TIMESTAMP DEFAULT NULL;

CREATE INDEX c_index_createtime on comments (createtime);

ALTER TABLE papers
  ADD edited_at TIMESTAMP DEFAULT NULL;
ALTER TABLE papers
  ADD edited_by INTEGER REFERENCES user(userid);
CREATE INDEX p_edited_by ON papers(edited_by);

ALTER TABLE comments
  ADD edited_at TIMESTAMP DEFAULT NULL;
ALTER TABLE comments
  ADD edited_by INTEGER REFERENCES user(userid);
 CREATE INDEX c_edited_by ON comments(edited_by);


create table papers_history (
  paperid INTEGER,
  old_getlink TEXT,
  old_title TEXT,
  old_authors TEXT, -- separated by ,
  old_domains TEXT, -- separated by ,
  old_tags TEXT, -- separated by ,
  old_edited_by INTEGER, -- edited before
  old_edited_at TIMESTAMP,
  history_entry_createdat   TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
  FOREIGN KEY(paperid) REFERENCES papers(paperid),
  FOREIGN KEY(old_edited_by) REFERENCES users(userid)
);

create index ph_index1 on papers_history(paperid);

.quit
