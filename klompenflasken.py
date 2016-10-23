from flask import Flask
app = Flask(__name__)
app.config.from_object('config')
from views import *
import sqlalchemy
from klompenflasken import app

if __name__ == '__main__':
	app.run(host='0.0.0.0')
