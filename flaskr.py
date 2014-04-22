"""
	Based on Flaskr by Armin Noacher. BSD license.
"""

# all the imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

# create our little application :)
app = Flask(__name__)

app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
	DATABASE=os.path.join(app.root_path, 'flaskr.db'),
	DEBUG=True,
	SECRET_KEY='dev key',
	USERNAME='admin',
    PASSWORD='secret'
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

if __name__ == '__main__':
	app.run()

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


