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

drop table if exists events;
create table events (
	id integer primary key autoincrement,
	owner integer not null,
	title text not null,
	description text not null,
	date datetime not null
);

-- For development purposes, prepopulate the database with a user:
insert into users values (1, "admin", "$2a$11$.ovzB8JWma93E5MwbiLX5.H6yZ6NOtLlUv9ZgrqxXb/FDGr.UGJzG ", "luca.masters2@gmail.com");
-- password=secret
