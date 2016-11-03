from __future__ import print_function
import sys
import os
from flask import render_template, request, redirect, make_response, url_for, send_from_directory
from klompenflasken import app
import json, random, string
from db import connect
from sqlalchemy.orm import sessionmaker
#from db import Base, User, awardCreator, awardType, award
from db import Base, User, awardCreator, award
from datetime import datetime
from functools import wraps
from page import Link, Page, adminPage, homePage, awardPage
from werkzeug.utils import secure_filename
import passwd as passwdModule


# start database session
DB_DB = 'klompen_db'
DB_USER = 'klompen_db_user'
DB_PASSWD = 'BlueDanceMoon42'
con = connect(DB_USER, DB_PASSWD, DB_DB)
Base.metadata.bind = con
dbSession = sessionmaker()
dbSession.bind = con
session = dbSession()


#file types allowed
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']


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


# checks a user supplied cookie to see whether it exists
# in our database and is an award creator
# output: if the cookie matches one in our database, this
# function returns the corresponding user object. if not,
# it returns None
def checkAwardCreator( cookie ):
	u = session.query(User).filter_by(cookie = cookie).first()
	errorPrint("Checking admin status...")
	if u is not None and u.admin == False:
		errorPrint("Award Creator found...")
		return u
	else:
		return None


#define file types allowed for upload
#allowed file types: png, jpg, and jpeg 
def allowed_file(filename):
    return '.' in filename and \
    	filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


#define the route for uploaded files to be viewed in the browser
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# homepage route
@app.route("/index")
@app.route("/")
def index():
	return render_template('index.html', page=homePage)


# the function factory for creating login-required pages
def requiresLogin(f):
	@wraps(f)
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


# the function factory for creating admin-required pages
def requiresAdmin(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		cookie = request.cookies.get('session-cookie', None)
		if cookie is not None:
			errorPrint("cookie found...")
			u = checkAdmin(cookie)
			if u is not None:
				errorPrint(u.fname + " has admin privileges")
				return f(*args, **kwargs)

			# what happens when user doesn't have admin privileges
			else:
				message = "Access denied: " + request.url + \
					" requires admin privileges"
				return render_template('error.html', message=message)

		return redirect(url_for('login', next=request.url))
	

	return decorated_function


#the function factory for creating pages for award creators
def requiresAwardCreator(f):
	@wraps(f)
	def decorated_award_function(*args, **kwargs):
		cookie = request.cookies.get('session-cookie', None)
		errorPrint(request.url + " request URL")
		if cookie is not None:
			errorPrint("cookie found...")
			u = checkAwardCreator(cookie)
			if u is not None:
				errorPrint(u.fname + " has award creation privileges")
				return f(*args, **kwargs)

			# what happens when user doesn't have admin privileges
			else:
				message = "Access denied: " + request.url + \
					" requires award creation privileges"
				return render_template('error.html', message=message)

		return redirect(url_for('login', next=request.url))
	
	return decorated_award_function	


@app.route('/admin')
@app.route('/admin/')
@requiresAdmin
@requiresLogin
def admin():
	return render_template('admin.html', page=adminPage)


@app.route('/admin/user')
@app.route('/admin/user/')
@requiresAdmin
@requiresLogin
def adminUser():
	users = session.query(User).all()
	return render_template('admin-user.html', users=users, page=adminPage) 


@app.route('/admin/user/view/<user_id>')
@requiresAdmin
@requiresLogin
def adminUserView(user_id):
	user = session.query(User).filter_by( id=user_id ).first()
	if user:
		creator = session.query(awardCreator).filter_by( 
			uid=user_id ).first()
		return render_template('admin-user-view.html', user=user, 
					creator=creator, page=adminPage) 
	else:
		render_template('error.html', 
				message="User not found", page=adminPage)


@app.route('/admin/user/edit/<user_id>', methods=['GET', 'POST'])
@requiresAdmin
@requiresLogin
def adminUserEdit(user_id):
	# serve the form for editing our user...
	# don't forget, we need to pass not just user info but
	# award creator info as well if it's available
	if request.method == 'GET':
		user = session.query(User).filter_by( id=user_id ).first()
		if user:
			creator = session.query(awardCreator).filter_by( 
				uid=user_id ).first()
			return render_template('admin-user-edit.html', user=user, 
						creator=creator, page=adminPage) 
		else:
			render_template('error.html', 
					message="User not found", page=adminPage)

	# process edit POST request
	elif request.method == 'POST':
		user = session.query(User).filter_by( id=user_id ).first()
		creator = session.query(awardCreator).filter_by( 
			uid=user_id ).first()
		if user:
			if creator:
				creator.org = request.form.get('org', None)
				creator.city = request.form.get('city', None)
			user.fname = request.form.get('fname', None)
			user.lname = request.form.get('lname', None)
			user.email = request.form.get('email', None)
			user.admin = request.form.get('admin', False)

			# in case of erroneous data, let's error handle
			try:
				session.commit()
			except:
				message = "Error editing user. \
					  Please try again."
				session.rollback()
				return render_template('error.html', 
					message = message,
					page = adminPage) 
				
			return redirect('/admin/user/view/' + str(user_id)) 

		else:
			render_template('error.html', 
					message="User not found", 
					page=adminPage)


@app.route('/admin/user/create', methods=['GET', 'POST'])
@requiresAdmin
@requiresLogin
def adminUserCreate():
	# serve the form for create our user...
	if request.method == 'GET':
		return render_template('admin-user-create.html', page=adminPage)

	# process edit POST request
	elif request.method == 'POST':
		org = request.form.get('org', None)
		city = request.form.get('city', None)
		fname = request.form.get('fname', None)
		lname = request.form.get('lname', None)
		email = request.form.get('email', None)
		admin = request.form.get('admin', False)
		passwd = passwdModule.resetPasswd( fname = fname, email = email )

		# in case of erroneous data, let's error handle
		try:
			newUser = User(fname, lname, email, passwd, admin)
			session.add(newUser)
			session.commit()
		except:
			message = "Error creating user. \
				  Please try again."
			session.rollback()
			return render_template('error.html', 
				message = message, page = adminPage) 
	
		if admin == False:	
			try:
				user = session.query(User).filter_by(
					email=email).first()
				newCreator = awardCreator(user.id, org, city)
				session.add(newCreator)
				session.commit()
			except:
				message = "Error creating user. \
					  Please try again."
				session.rollback()
				user = session.query(User).filter_by(
					email=email).first()
				session.delete(user)
				session.commit()
				return render_template('error.html', 
					message = message, page = adminPage) 
			
		user = session.query(User).filter_by(email=email).first()
		return redirect('/admin/user/view/' + str(user.id)) 



@app.route('/admin/user/delete/<user_id>')
@requiresAdmin
@requiresLogin
def adminUserDelete(user_id):
	user = session.query(User).filter_by( id=user_id ).first()
	cookie = request.cookies.get('session-cookie')
	current = session.query(User).filter_by( cookie=cookie).first()
	if user and current.id != user.id:
		# check to see if this user has a row in the
		# creator table (if so, delete)
		creator = session.query(awardCreator).filter_by( 
			uid=user_id ).first()
		if creator:
			errorPrint("Deleted creator record" + user_id)
			session.delete(creator)
			session.commit()

		# perform deletion and commit	
		message = "User deleted successfully"
		session.delete(user)
		session.commit()

		# redirect user table
		return redirect('admin/user') 

	elif user and current.id == user.id:
		# redirect to error page
		message = "Error: you can't delete yourself!"
		return render_template('error.html', message=message, 
					page=adminPage) 
	else:
		# redirect to error page
		message = "Error: couldn't delete user #" + user_id
		return render_template('error.html', message=message, 
					page=adminPage) 


# deletes the cookie so that a user is logged out
@app.route("/logout")
def logout():
	if 'cookie' in request.headers:
		cookie = request.cookies.get('session-cookie')
		if cookie is not None:
			delCookie( cookie )

	response = make_response(redirect("/", 302))
	response.set_cookie('session-cookie', 
		value='', expires=0)
	return response


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
			message = "Error: Invalid username/password"
			return render_template('error.html', message=message)


#register a new award creator user
@app.route('/register', methods=['GET', 'POST'])	
def register():
	message=None
	if request.method == 'POST':
		register = request.form

		#Save the signature file to the uploads folder
		filename = ''
		file = request.files['user-signature']
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
        	file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        	user_signature = request.url_root + os.path.join(app.config['UPLOAD_FOLDER'], file.filename) 
 
		#Create a generic user
		new_user = User(register['user-first-name'], register['user-last-name'], register['user-email'], register['user-password'])
		session.add(new_user)
		session.commit()

		#Create an award creator
		new_award_creator = awardCreator(new_user.id, register['user-org'], register['user-city'], user_signature)	
		session.add(new_award_creator)
		session.commit()

		message = True
	else: 
		return render_template('register.html', page=homePage, editProfile=False)	

	return render_template('register.html', message=message, page=homePage, editProfile=False)


@app.route('/awards')
@app.route('/awards/')
@requiresAwardCreator
@requiresLogin
def awards():
	return render_template('awards.html', page=awardPage)	


#edit profile - award creator user must be logged in
@app.route('/awards/edit_profile', methods=['GET', 'POST']) 
@requiresAwardCreator
@requiresLogin
def edit_profile():
	message=None
	editProfile =True
	
	if request.method == 'GET':
		user = getLoggedInUser()
		awardUser = session.query(awardCreator).filter_by(uid = user.id).first()
		sig_url = awardUser.signature
		errorPrint("The signature: " + awardUser.signature)

		# [james]: I modified this. it "works" now in the sense
		# that it doesn't crash. but it probably doesn't function
		# as intended. original version in comments below:
		#
		# sig_filename = sig_url.split("uploads/",1)[1]

		sig_filename = sig_url.split("/uploads/",1)[0]
		return render_template('register.html', editProfile=editProfile, user=user, awardUser=awardUser, sig_filename=sig_filename, page=awardPage)
	
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

		return render_template('register.html', editProfile=editProfile, user=user, awardUser=awardUser, message=message, page=awardPage)


#create an award - award creator user must be logged in 
@app.route('/awards/create_award', methods=['GET', 'POST'])	
@requiresAwardCreator
@requiresLogin
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
		return render_template('create_award.html', page=awardPage)	

	return render_template('create_award.html', message=message, page=awardPage)


#delete awards - award creator user must be logged
@app.route('/awards/delete_awards', methods=['GET', 'POST'])
@requiresAwardCreator
@requiresLogin	
def delete_awards(methods=['GET', 'POST']):
	if request.method == 'GET':

		#Get Logged in User ID
		user = getLoggedInUser()
		user_awards = session.query(award).filter_by(creatorID = user.id)

		return render_template('delete_awards.html', user_awards=user_awards, page=awardPage)

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

		return render_template('delete_awards.html', user_awards=user_awards, message=message, page=awardPage)
	
	return render_template('delete_awards.html', page=awardPage)


@app.route("/reset-password", methods=['GET', 'POST'])
def resetPasswd():
        if request.method == "GET":
                return render_template('reset-password.html')

        if request.method == "POST":
                try:
                        email = request.form.get("email")
                        user = session.query(User).filter_by(email=email).first()
                        errorPrint("Reseting passwd: " + user.fname +
                                " | " + user.email)
                        user.passwd = passwdModule.resetPasswd( 
				fname = user.fname,
                                email = user.email )
                        session.commit()
                        message = "Password successfully reset. " + \
                                "Please check your email."
                        return render_template('success.html', message=message)

                except:
                        session.rollback()
                        message = sys.exc_info()
                        # message = "Failed to reset password."
                        return render_template('error.html', message=message)


# catch all to route bad URIs
@app.route("/<path:path>")
def notFound(path):
	message = "404: page \"" + path + "\" not found"
	return render_template('error.html', message=message)
