from __future__ import print_function
import sys
from flask import render_template, request, redirect, make_response, url_for
from klompenflasken import app
import json, random, string
from db import connect
from sqlalchemy.orm import sessionmaker
#from db import Base, User, awardCreator, awardType, award
from db import Base, User, awardCreator, award
from datetime import datetime


# start database session
DB_DB = 'klompen_db'
DB_USER = 'klompen_db_user'
DB_PASSWD = 'BlueDanceMoon42'
con = connect(DB_USER, DB_PASSWD, DB_DB)
Base.metadata.bind = con
dbSession = sessionmaker()
dbSession.bind = con
session = dbSession()


# print to standard error
def errorPrint(string):
	print(string, file=sys.stderr)


# given the email and user from the login screen,
# check tha against the user database
# output: if login succeeds, returns user object.
# if not, returns None
def authUser( email, passwd):
	u = session.query(User).filter_by(email = email).first()
	if u == None:
		errorPrint("User not found...")
		return None
	elif u.passwd != passwd:
		errorPrint("Bad passwd...")
		return None 
	else:
		errorPrint("Good authentication...")
		return u


# generates a 64-byte alpha-numeric string and sets it as the 
# user's cookie in the database
# input: user email
# output: cookie string
def genCookie( email ):
	u = session.query(User).filter_by(email = email).first()
	cookieStr = ""
	for i in range(63):
		cookieStr = cookieStr + random.choice(string.letters +
			string.digits)
	u.cookie = cookieStr
	errorPrint(cookieStr)
	session.commit()	
	return cookieStr


# deletes a cookie; useful for logging out our users
def delCookie( cookie ):
	u = session.query(User).filter_by(cookie = cookie).first()
	u.cookie = None
	session.commit()	



# checks a user supplied cookie to see whether it exists
# in our database
# output: if the cookie matches one in our database, this
# function returns the corresponding user object. if not,
# it returns None
def checkLoggedIn( cookie ):
	u = session.query(User).filter_by(cookie = cookie).first()
	if u is not None:
		return u
	return None


#louise
#get the user currently logged into the system 
#output: return the user object 
def getLoggedInUser():
	cookie = request.cookies.get('session-cookie')
	if cookie is not None:
		errorPrint("cookie found...")
		u = checkLoggedIn(cookie)
		if u is not None:
			return u
		return None	


# checks a user supplied cookie to see whether it exists
# in our database and is an admin
# output: if the cookie matches one in our database, this
# function returns the corresponding user object. if not,
# it returns None
def checkAdmin( cookie ):
	u = session.query(User).filter_by(cookie = cookie).first()
	errorPrint("Checking admin status...")
	if u is not None and u.admin == True:
		errorPrint("Admin found...")
		return u
	else:
		return None


# homepage route
@app.route("/index")
@app.route("/")
def index():
	return render_template('index.html')


# the function factory for creating login-required pages
def requiresLogin(f):
	def decorated_function(*args, **kwargs):
		cookie = request.cookies.get('session-cookie')
		if cookie is not None:
			errorPrint("cookie found...")
			u = checkLoggedIn(cookie)
			if u is not None:
				errorPrint(u.fname + " is still logged in")
				return f(*args, **kwargs)
		return redirect('/login')
	

	return decorated_function


# the function factory for creating login-required pages
def requiresAdmin(f):
	def decorated_function(*args, **kwargs):
		cookie = request.cookies.get('session-cookie')
		if cookie is not None:
			errorPrint("cookie found...")
			u = checkAdmin(cookie)
			if u is not None:
				errorPrint(u.fname + " has admin privileges")
				return f(*args, **kwargs)

		return redirect(url_for('login', next=request.url))
	

	return decorated_function


@app.route('/admin')
@requiresAdmin
@requiresLogin
def admin():
	return render_template('admin.html')



# deletes the cookie so that a user is logged out
@app.route("/logout")
def logout():
	if 'cookie' in request.headers:
		cookie = request.cookies.get('session-cookie')
		if cookie is not None:
			delCookie( cookie )

	return redirect("/", 302)


# the login handler
# GET - checks the request headers for a cookie. if it exists,
# it checks this against our database and logs the user in 
# automatically. if not, then it directs the user to the login
# form
# POST - handles login form, validates email and password. on
# success it supplies the client with a cookie and redirects
# to the homepage
@app.route("/login", methods=['GET', 'POST'])
def login():
	# if GET, then serve login page
	if request.method == 'GET':
		cookie = request.cookies.get('session-cookie')
		if cookie is not None:
			errorPrint("cookie found...")
			u = checkLoggedIn(cookie)
			if u is not None:
				errorPrint(u.fname + " is still logged in")
				return redirect("/", 302)
			else: 
				errorPrint("cookie not found...")
		else:
			errorPrint("no cookie supplied...")

		if 'next' in request.args:
			next = request.args['next']
		else:
			next = "/"

		return render_template('login.html', next=next)
		

	# if POST, then process login request
	if request.method == 'POST':
		email = request.form['email']
		passwd = request.form['passwd']
		next = request.form['next']
		errorString = "Authenticating " + email + "|" + passwd
		errorPrint(errorString)
		user = authUser(email, passwd)
		if user != None:
			response = make_response(redirect(next, 302))
			response.set_cookie('session-cookie', 
				value=genCookie(email))
			return response
		else:
			return "Invalid username/password..."


#louise
#register a new award creator user
@app.route('/register', methods=['GET', 'POST'])	
def register():
	message=None
	if request.method == 'POST':
		register = request.form
	
		#Create a generic user
		new_user = User(register['user-first-name'], register['user-last-name'], register['user-email'], register['user-password'])
		session.add(new_user)
		session.commit()

		#Create an award creator
		new_award_creator = awardCreator(new_user.id, register['user-org'], register['user-city'])	
		session.add(new_award_creator)
		session.commit()

		message = True
	else: 
		return render_template('register.html')	

	return render_template('register.html', message=message)


#louise
#edit profile - award creator user must be logged in
@app.route('/edit_profile', methods=['GET', 'POST']) 
def edit_profile():
	message=None
	editProfile =True
	
	if request.method == 'GET':
		user = getLoggedInUser()
		awardUser = session.query(awardCreator).filter_by(uid = user.id).first()
		return render_template('register.html', editProfile=editProfile, user=user, awardUser=awardUser)
	
	if request.method == 'POST':
		user = getLoggedInUser()
		awardUser = session.query(awardCreator).filter_by(uid = user.id).first()
		update = request.form
		user.fname = update['user-first-name']
		user.lname = update['user-last-name']
		user.email = update['user-email']
		user.passwd = update['user-password']
		awardUser.org = update['user-org']
		awardUser.city = update['user-city']	
		session.commit()

		message="User profile updated."

		return render_template('register.html', editProfile=editProfile, user=user, awardUser=awardUser, message=message)


#louise
#create an award - award creator user must be logged in 
@app.route('/create_award', methods=['GET', 'POST'])	
def create_award():
	message=None
	if request.method == 'POST':
		create_award = request.form
		fname = create_award['recipient-first-name']
		lname = create_award['recipient-last-name']
		email = create_award['recipient-email']
		awardType = create_award['award-type']
		award_date = create_award['award-date']
		award_time = create_award['award-time']

		#Convert date and time to datetime format
		date_time = award_date + ' ' + award_time
		award_dt = datetime.strptime(date_time, '%Y-%m-%d %I:%M')

		#Get Logged in User ID
		user = getLoggedInUser()
		if user is not None:
			creatorID = user.id
		else:
			user.id = 0	
	
		new_award = award(fname, lname, email, awardType, award_dt, creatorID)
		session.add(new_award)
		session.commit()

		message = "New award added to the database."
	else:
		return render_template('create_award.html')	

	return render_template('create_award.html', message=message)


#louise
#delete awards - award creator user must be logged
@app.route('/delete_awards', methods=['GET', 'POST'])	
def delete_awards(methods=['GET', 'POST']):
	if request.method == 'GET':

		#Get Logged in User ID
		user = getLoggedInUser()
		user_awards = session.query(award).filter_by(creatorID = user.id)

		return render_template('delete_awards.html', user_awards=user_awards)

	if request.method == 'POST':
		award_form = request.form
		award_id = award_form['award-id']
		errorPrint(award_id)
		award_to_delete = session.query(award).filter_by(id = award_id).first()
		errorPrint(award_to_delete)
		session.delete(award_to_delete)
		session.commit()

		message="Award deleted."

		#Get Logged in User ID
		user = getLoggedInUser()
		user_awards = session.query(award).filter_by(creatorID = user.id)

		return render_template('delete_awards.html', user_awards=user_awards, message=message)
	
	return render_template('delete_awards.html')


# catch all to route bad URIs
@app.route("/<path:path>")
def notFound(path):
	message = "404: page \"" + path + "\" not found"
	return render_template('error.html', message=message)
