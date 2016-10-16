from __future__ import print_function
import sys
from flask import render_template
from klompenflasken import app

@app.route("/index")
@app.route("/")
def index():
	return render_template('index.html')
