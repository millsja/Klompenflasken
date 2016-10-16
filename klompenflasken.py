from flask import Flask
app = Flask(__name__)
app.config.from_object('config')
from views import *
from flask.ext.sqlalchemy import SQLAlchemy
from klompenflasken import app
from klompenDB import connect

DB_DB = 'klompen_db'
DB_USER = 'klompen_db_user'
DB_PASSWD = 'BlueDanceMoon42'
con, meta = connect(DB_USER, DB_PASSWD, DB_DB)

if __name__ == '__main__':
	app.run(host='0.0.0.0')
