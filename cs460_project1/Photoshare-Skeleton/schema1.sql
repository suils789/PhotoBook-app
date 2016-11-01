CREATE DATABASE photoshare;
USE photoshare;
DROP TABLE Pictures CASCADE;
DROP TABLE Users CASCADE;

CREATE TABLE Users (
    user_id integer  AUTO_INCREMENT,
    email varchar(255) UNIQUE,
    password varchar(255) NOT NULL,
    first_name varchar(255) NOT NULL,
    last_name varchar(255) NOT NULL,
    date_of_birth date NOT NULL,
    gender char(1) NOT NULL,
    hometown varchar(255) NOT NULL,  
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);


INSERT INTO Users VALUES (1,'test@bu.edu', 'test','test','test','2014-08-03','M','testtest');
INSERT INTO Users VALUES (2,'test1@bu.edu', 'test', 'test','test','2015-09-01','F','testtest');

CREATE TABLE Pictures
(
  picture_id integer  AUTO_INCREMENT,
  user_id integer NOT NULL,
  imgdata longblob NOT NULL,
  captions varchar(255),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id)
  );

CREATE TABLE Albums(
  album_id integer AUTO_INCREMENT,
  owner_id integer NOT NULL,
  name varchar(255) NOT NULL,
  album_creationDate date NOT NULL,
  PRIMARY KEY (album_id),
  FOREIGN KEY (owner_id) REFERENCES Users(user_id));

CREATE TABLE Tags
(tag_id integer AUTO_INCREMENT,
tag_text varchar(255) NOT NULL,
PRIMARY KEY (tag_id));

CREATE TABLE Comments
(comment_id integer AUTO_INCREMENT,
comment_text varchar(1000) NOT NULL,
owner_id integer NOT NULL,
comment_date date NOT NULL,
picture_id integer NOT NULL,
PRIMARY KEY (comment_id),
FOREIGN KEY (owner_id) REFERENCES Users(user_id),
FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id)
);

CREATE TABLE Friendship
(user1 integer NOT NULL,
user2 integer NOT NULL,
PRIMARY KEY (user1,user2),
FOREIGN KEY (user1) REFERENCES Users(user_id),
FOREIGN KEY (user2) REFERENCES Users(user_id));

CREATE TABLE PictureTags
(picture_id integer NOT NULL,
  tag_id integer NOT NULL,
  PRIMARY KEY (picture_id, tag_id),
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id),
  FOREIGN KEY (tag_id) REFERENCES Tags(tag_id)
);

CREATE TABLE AlbumPhoto(
album_id integer NOT NULL,
picture_id integer NOT NULL,
PRIMARY KEY (album_id, picture_id),
FOREIGN KEY (album_id) REFERENCES Albums(album_id),
FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id)
);


