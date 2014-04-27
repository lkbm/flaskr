drop table if exists entries;
create table entries (
	id integer primary key autoincrement,
	title text not null,
	text text not null,
	author id not null
);

drop table if exists users;
create table users (
	id integer primary key autoincrement,
	username text not null,
	email text not null
);

-- For development purposes, prepopulate the database with a user:
insert into users values (1, "Admin", "luca.masters@gmail.com");


