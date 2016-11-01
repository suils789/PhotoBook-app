CREATE DATABASE photoshare;
USE photoshare;


CREATE TABLE Users (
    user_id int4  AUTO_INCREMENT,
    email varchar(255) UNIQUE,
    password varchar(255),
    first_name varchar(255) NOT NULL,
    last_name varchar(255) NOT NULL,
    date_of_birth date NOT NULL,
    gender char(1) NOT NULL,
    hometown varchar(255) NOT NULL,  
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);
CREATE TABLE Albums(
  user_id integer NOT NULL,
  name varchar(255) NOT NULL,
  album_creationDate date NOT NULL,
  PRIMARY KEY (user_id, name),
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE);

CREATE TABLE Pictures
(
  picture_id int4  AUTO_INCREMENT,
  user_id int4,
  imgdata longblob ,
  belong_to VARCHAR(255) NOT NULL,
  caption VARCHAR(255),
  INDEX upid_idx (user_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id),
  FOREIGN KEY (user_id, belong_to) REFERENCES Albums(user_id, name) ON DELETE CASCADE
);


CREATE TABLE PictureTags
(picture_id integer NOT NULL,
  tag_text varchar(255),
  PRIMARY KEY (picture_id, tag_text),
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);

CREATE TABLE Friendship
(user1 integer NOT NULL,
user2 integer NOT NULL,
PRIMARY KEY (user1,user2),
FOREIGN KEY (user1) REFERENCES Users(user_id) ON DELETE CASCADE,
FOREIGN KEY (user2) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE Comments
(comment_id integer AUTO_INCREMENT,
comment_text varchar(1000) NOT NULL,
owner_id integer,
comment_date date NOT NULL,
picture_id integer NOT NULL,
PRIMARY KEY (comment_id),
FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);
  
CREATE TABLE LikeFunction
(
  user_id integer NOT NULL,
  picture_id integer NOT NULL,
  PRIMARY KEY (user_id, picture_id),
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE ASSERTION commentRule CHECK(NOT EXISTS
(SELECT COUNT(c.owner_id) From Comments c, Pictures p WHERE c.picture_id = p.picture_id AND c.owner_id = p.user_id) 
) ;