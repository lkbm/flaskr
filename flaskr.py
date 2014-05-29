"""
	Based on Flaskr by Armin Noacher. BSD license.
"""

# all the imports
import os
import sqlite3
import requests
import json
import re
import dateutil.parser
import bcrypt
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, make_response, flash

# Create the application
app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
	DATABASE=os.path.join(app.root_path, 'flaskr.db'),
	DEBUG=True,
	SECRET_KEY='dev key',
	WORK_FACTOR=11
	# USERNAME='admin',
	# PASSWORD='secret'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def connect_db():
	"""Connects to the specific database."""
	rv = sqlite3.connect(app.config['DATABASE'])
	rv.row_factory = sqlite3.Row
	return rv

def init_db():
	with app.app_context():
		db = get_db()
		with app.open_resource('schema.sql', mode='r') as f:
			db.cursor().executescript(f.read())
		db.commit()

def get_db():
	"""Opens a new database connection if there is none yet for the current application context."""
	if not hasattr(g, 'sqlite_db'):
		g.sqlite_db = connect_db()
	return g.sqlite_db

"""the app context is created before the request comes in and is destroyed (teared down) whenever the request finishes. -- Flaskr tutorial""" 
@app.teardown_appcontext
def close_db(error):
	"""Closes the database again at the end of the request."""
	"""LKBM: I should probably investigate why we do that at the end of a request. I thought we wanted persistence."""
	if hasattr(g, 'sqlite_db'):
		g.sqlite_db.close()

@app.route('/')
def show_entries():
	return render_template('show_entries.html', entries=get_entries(0))

def get_entries(id):
	db = get_db()
	id = int(id)
	try:
		id = int(id)
		db = get_db()
		cur = 0
		if id == 0:
			cur = db.execute('select entries.id as id, entries.title as title, entries.text as text, entries.timestamp, users.username as author, users.id as author_id from entries join users WHERE entries.author=users.id order by id desc')
		else:
			cur = db.execute('select entries.id as id, entries.title as title, entries.text as text, entries.timestamp, users.username as author, users.id as author_id from entries join users WHERE entries.author=users.id AND entries.author=? order by id desc', (str(id),))
		return cur.fetchall()
	except ValueError:
		flash('Not a valid id')
	return []

@app.route('/add', methods=['POST'])
def add_entry():
	if not session.get('logged_in'):
		abort(401)
	db = get_db()
	# HTML isn't blocked in insertion, but the templating engine will scrub it unless epxlicitly told not to via |safe:
	db.execute('insert into entries (title, text, author, timestamp) values (?, ?, ?, datetime())', [request.form['title'], request.form['text'], session.get('id')])
	db.commit()
	flash('New entry was successfully posted')
	return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	if request.method == 'POST':
		db = get_db()
		user_list = db.execute('select id, username, password, email from users where username=?', [request.form['username']])
		users = user_list.fetchall()
		if len(users) == 0:
			error = 'Nonexistent user'
		elif users[0][2] == "":
			error = 'username/password login not configured for account. Try Mozilla Persona login.'
		elif bcrypt.hashpw(request.form['password'], users[0][2]) == users[0][2]:
			session['logged_in'] = True
			session['id'] = users[0][0]
			session['username'] = users[0][1]
			session['email'] = users[0][3]
			session['login_type'] = 'username'
			flash('You are now logged in as ' + session['username'])
			return redirect(url_for('show_entries'))
		else:
			error = 'Incorrect password'
	return render_template('login.html', error=error)

@app.route('/logout')
def logout():
	session.clear()	#session.pop('logged_in', None)
	flash('You were logged out.')
	response = make_response(redirect(url_for('show_entries')))
	response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
	response.headers['pragma'] = 'no-cache'
	response.headers['expires'] = '0'
	return response


@app.route('/del/<id>')
def delete_entry(id):
	if not session.get('logged_in'):
		abort(401)
	try:
		id = int(id)
		db = get_db()
		entries = db.execute('select entries.author as author from entries WHERE id=?', (str(id),))
		entry = entries.fetchall()
		if len(entry) == 0:
			flash('Nonexistent post')
		elif entry[0][0] != session['id']:
			flash('You may only delete your own posts.')
		else:
			db.execute('delete from entries where id=?', (str(id),))
			db.commit()
			flash('Deleted post ' + str(id))
	except ValueError:
		flash('Not a valid id')
	return redirect(url_for('show_entries'))

@app.route('/persona_login', methods=['POST'])
def persona_login():
	# The request has to have an assertion for us to verify
	if 'assertion' not in request.form:
		abort(400)

	# Send the assertion to Mozilla's verifier service.
	data = {'assertion': request.form['assertion'], 'audience': 'http://127.0.0.1:5000'}
	resp = requests.post('https://verifier.login.persona.org/verify', data=data, verify=True)

	# Did the verifier respond?
	if resp.ok:
		# Parse the response
		verification_data = json.loads(resp.content)
		
		# Check if the assertion was valid
		#flash(verification_data['status'])
		#return redirect(url_for('show_entries'))
		if verification_data['status'] == 'okay':
			db = get_db()
			user_list = db.execute('select id, username, email from users where email=?', [verification_data['email']])
			users = user_list.fetchall()
			if len(users) == 0:
				# Create account:
				db.execute('insert into users (username, password, email) values (?, ?, ?)', [verification_data['email'], "", verification_data['email']])
				db.commit()
				flash('New account created. You can change your username (and password, if you wish to set one) in your profile settings.')
                # Try selecting account again:
				user_list = db.execute('select id, username, email from users where email=?', [verification_data['email']])
				users = user_list.fetchall()
			else:
				flash('You are now logged in as ' + session['email'])
			session['logged_in'] = True
			session['persona_login'] = True
			session['id'] = users[0][0]
			session['username'] = users[0][1]
			session['email'] = verification_data['email']
			session['login_type'] = 'Persona'
			#session.update({'email': verification_data['email']})
			return redirect(url_for('show_entries'))
		else:
			abort(401)
		error = 'verification status not okay.'
		return render_template('login.html', error=error)

	# Oops, no response. Abort.
	abort(500)

@app.route('/persona_logout', methods=['POST'])
def persona_logout():
	if not session.get('logged_in') or not session.get('persona_login'):
			abort(401)
	else:
		flash('User logged out.')
		session.clear()
		return "plo OK"
	return redirect(url_for('show_entries'))

@app.route('/process_edit_user', methods=['POST'])
def process_edit_user():
	if not session.get('logged_in'):
		abort(401)
	db = get_db()
	# HTML isn't blocked in insertion, but the templating engine will scrub it unless epxlicitly told not to via |safe:
	db.execute('update users set username=? WHERE email=?', [request.form['username'], session['email']])
	if len(request.form['password']) > 0:
		db.execute('update users set password=? WHERE email=?', [request.form['password'], session['email']])
	db.commit()
	session['username'] = request.form['username']
	# TODO: If password defined, also set password.
	#flash('User successfully updated')
	return redirect(url_for('edit_user'))

@app.route('/edit_user')
def edit_user():
	db = get_db()
	return render_template('edit_user.html')

@app.route('/cal')
def show_events():
	db = get_db()
	cur = db.execute('select events.id as id, events.title as title, events.description as text, events.date, users.username as owner from events join users WHERE events.owner=users.id order by id desc')
	events = cur.fetchall()
	return render_template('show_events.html', events=events)

@app.route('/add_event', methods=['POST'])
def add_event():
	if not session.get('logged_in'):
		abort(401)
	# HTML isn't blocked in insertion, but the templating engine will scrub it unless epxlicitly told not to via |safe:
	event_date = validate_date(request.form['date'])
	if(event_date):
		db = get_db()
		db.execute('insert into events (title, description, owner, date) values (?, ?, ?, ?)', [request.form['title'], request.form['description'], session.get('id'), event_date])
		db.commit()
		flash('New event was successfully posted')
	else:
		flash('Invalid date')
	return redirect(url_for('show_events'))

@app.route('/del_event/<id>')
def delete_event(id):
	if not session.get('logged_in'):
		abort(401)
	try:
		id = int(id)
		db = get_db()
		events = db.execute('select events.owner as owner from events WHERE id=?', (str(id),))
		event = events.fetchall()
		if len(event) == 0:
			flash('Nonexistent event')
		elif event[0][0] != session['id']:
			flash('You may only delete your own events.')
		else:
			db.execute('delete from events where id=?', (str(id),))
			db.commit()
			flash('Deleted event ' + str(id))
	except ValueError:
		flash('Not a valid id')
	return redirect(url_for('show_events'))

@app.route('/user/<id>')
def show_user(id):
	try:
		id = int(id)
		db = get_db()
		user_list = db.execute('select id, username, email from users where id=?', (str(id),))
		user = user_list.fetchall()
		if len(user) == 0:
			flash('Nonexistent user')
		else:
			return render_template('show_user.html', users=user, id=id, entries=get_entries(id))
	except ValueError:
		flash('Not a valid id')
	return redirect(url_for('show_entries'))

def validate_date(date):
	try:
		return dateutil.parser.parse(date).date().strftime("%Y-%m-%d")
	except ValueError:
		return False

@app.route('/register')
def register_user():
	return render_template('new_user.html')

@app.route('/add_user', methods=['POST'])
def add_user():
	db = get_db()
	user_list = db.execute('select id, username, email from users where email=?', [request.form['email']])
	user = user_list.fetchall()
	if len(user) == 0:
		password = bcrypt.hashpw(request.form['password'], bcrypt.gensalt(app.config['WORK_FACTOR']))
		flash(password)
		db.execute('insert into users (username, email, password) values (?, ?, ?)', [request.form['username'], request.form['email'], password])
		db.commit()
		flash('password')
		flash('User added')
		login();
	else:
		flash('User already registered with that email address.')
	return redirect(url_for('show_entries'))

if __name__ == '__main__':
	init_db()
	app.run()

