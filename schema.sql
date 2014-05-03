drop table if exists entries;
create table entries (
	id integer primary key autoincrement,
	title text not null,
	text text not null,
	author id not null,
	timestamp datetime
);

drop table if exists users;
create table users (
	id integer primary key autoincrement,
	username text not null unique,
	password text not null,
	email text not null
);

-- For development purposes, prepopulate the database with a user:
-- insert into users values (1, "admin", "secret", "luca.masters@gmail.com");
insert into users values (1, "admin", "secret", "luca.masters2@gmail.com");

