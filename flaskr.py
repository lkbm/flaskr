"""
	Based on Flaskr by Armin Noacher. BSD license.
"""

# all the imports
import os
import sqlite3
import requests
import json
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

# Create the application
app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
	DATABASE=os.path.join(app.root_path, 'flaskr.db'),
	DEBUG=True,
	SECRET_KEY='dev key',
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
	db = get_db()
	#cur = db.execute('select id, title, text, author from entries order by id desc')
	cur = db.execute('select entries.id as id, entries.title as title, entries.text as text, entries.timestamp, users.username as author from entries join users WHERE entries.author=users.id order by id desc')
	entries = cur.fetchall()
	return render_template('show_entries.html', entries=entries)

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
		user_list = db.execute('select id, username, password from users where username=?', [request.form['username']])
		users = user_list.fetchall()
		if len(users) == 0:
			error = 'Nonexistent user'
		elif users[0][2] != request.form['password']:
			error = 'Incorrect password'
		elif users[0][2] == "":
			error = 'username/password login not configured for account. Try Mozilla Persona login.'
		else:
			session['logged_in'] = True
			session['id'] = users[0][0]
			session['username'] = users[0][1]
			flash('You are now logged in as ' + session['username'])
			return redirect(url_for('show_entries'))
	return render_template('login.html', error=error)

@app.route('/logout')
def logout():
	session.clear()	#session.pop('logged_in', None)
	flash('You were logged out.')
	return redirect(url_for('show_entries'))

@app.route('/del/<id>')
def delete_entry(id):
	if not session.get('logged_in'):
		abort(401)
	try:
		id = int(id)
		db = get_db()
		db.execute('delete from entries where id=?', str(id))
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
			session['id'] = users[0][0]
			session['username'] = users[0][1]
			session['email'] = verification_data['email']
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
	if not session.get('logged_in'):
			abort(401)
	else:
		flash('User logged out.')
		session.clear()
		return "plo OK"
	return redirect(url_for('show_entries'))

if __name__ == '__main__':
	init_db()
	app.run()

