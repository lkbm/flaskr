drop table if exists entries;
create table entries (
	id integer primary key autoincrement,
	title text not null,
	text text not null,
	author integer not null,
	score integer,
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

drop table if exists votes;
create table votes (
	id integer primary key autoincrement,
	user_id integer not null,
	event_id integer not null,
	upvote bool
);

-- For development purposes, prepopulate the database with a user:
insert into users values (1, "admin", "$2a$11$KTg9hr8lVvePTxm9GkikV.gNw/6Is0to8S7RPSGo3NH43JbidHQky", "luca.masters2@gmail.com");
-- password=secret
