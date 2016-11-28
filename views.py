from __future__ import print_function
import sys
import os
from flask import render_template, request, redirect, make_response, url_for, send_from_directory
from klompenflasken import app
import json, random, string
from db import connect
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, desc
#from db import Base, User, awardCreator, awardType, award
from db import Base, User, awardCreator, award
from datetime import datetime, timedelta
from functools import wraps
from page import Link, Page, adminPage, homePage, awardPage, queryPage
from werkzeug.utils import secure_filename
import requests
import base64
import passwd as passwdModule
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as pyplot


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


# the main admin page, linking out to various other functions
@app.route('/admin')
@app.route('/admin/')
@requiresAdmin
@requiresLogin
def admin():
	return render_template('admin.html', page=adminPage)


# the main analytics page, which links out to the various reports
# which can be generated by the admin user
@app.route('/admin/analytics')
@app.route('/admin/analytics/')
@requiresAdmin
@requiresLogin
def analyticsMain():
	return render_template('analyticsHome.html', page=queryPage)



# generates a report with accompanying CSV with data organized
# by award creator 
def getAwardCountByCreator():
	awards = []
	query = session.query(awardCreator, User, 
				func.count(award.id).label('count')).\
		join(User).\
		outerjoin(award).\
		group_by(awardCreator.uid, User.id).\
		order_by('count DESC')
	for q in query:
		awards.append( {"fname": q[1].fname,
			"lname": q[1].lname,
			"org": q[0].org,
			"count": str(int(q[2])) } )
	return awards



# generates a report with accompanying CSV with data organized
# by award creator's city
def getAwardCountByCity():
	cities = []
	query = session.query(awardCreator.city, awardCreator.state,
				func.count(award.id).label('count')).\
		outerjoin(award).\
		group_by(awardCreator.city, awardCreator.state).\
		order_by('count DESC')
	for q in query:
		cities.append( {"city": q[0],
			"state": q[1],
			"count": str(int(q[2])) } )
	return cities 


# generates a report with accompanying CSV with data organized
# by award creator's state
def getAwardCountByState():
	states = []
	query = session.query(awardCreator.state, 
		func.count(award.id).label('count')).\
		outerjoin(award).\
		group_by(awardCreator.state).\
		order_by('count DESC')
	for q in query:
		states.append( {"state": q[0],
			"count": str(int(q[1])) } )
	return states



# routes requests for CSV files in the query folder
@app.route('/queries/<filename>')
def query_file(filename):
    return send_from_directory(app.config['QUERY_FOLDER'], filename)


# generates a CSV file for report data generated using
# the query methods above; writes files to .../queries/
# folder and returns filename
def getCSV( data ):
	# pull some unsavory characters out of our urls
	def cleanURL( url ):
		url = url.replace(" ", "_")
		url = url.replace(":", "-")
		return url

	# write csv to file
	filename = "queries/" + str(datetime.now())
	filename = cleanURL( filename )
	filename = filename + ".query.csv"
	errorPrint("new query at: " + filename)
	fd = open(filename, 'w')


	# add the headers
	line = ""
	keys = data[0].keys()
	for q in range( len(keys) ):
		if q == 0:
			line = line + keys[q]
		else:
			line = line + "," + keys[q]
	fd.write(line)
	fd.write("\n")

	# add data
	for e in data:
		line = ""
		for q in range( len(keys) ):
			if q == 0:
				line = line + str(e[keys[q]])
			else:
				line = line + "," + str(e[keys[q]])
		fd.write(line)
		fd.write("\n")

	# close up shop and go home
	fd.close()
	return "/" + filename



# generates bar graph to go with query reports
def getGraphCreator( data, filename ):
	yAxisData = [] # this will hold award count
	xAxisData = [] # this will hold city, state, or name
	xAxisText = []
		
	# add data
	q = 0
	for e in range( 0, min(len(data), 5) ):
		yAxisData.append(int(data[e]['count']))
		xAxisText.append(data[e]['fname'] + "\n" + data[e]['lname'])	
		xAxisData.append(q)
		q = q + 1

	# plot our data
	graph = pyplot.bar(xAxisData, yAxisData, align="center") 
	pyplot.title("Top five creators")

	# add our x-axis labels
	pyplot.xlim(min(xAxisData) - 1, max(xAxisData) + 1)
	pyplot.xticks( xAxisData, xAxisText)

	# fix padding and intervals for y axis
	pyplot.ylim(0, max(yAxisData) + 0.5)
	pyplot.yticks( range(0,max(yAxisData)+1,1) )

	# generate filename. note: we're starting with the
	# filename from our csv, so remove the csv and /
	# at the end and beginning of the string
	filename = filename[1:]
	filename = filename[:-3]
	filename = filename + "png"

	# save file
	pyplot.savefig(filename, bbox_inches = "tight")
	pyplot.close()

	return "/" + filename


# generates bar graph to go with query reports
def getGraphCities( data, filename ):
	yAxisData = [] # this will hold award count
	xAxisData = [] # this will hold city, state, or name
	xAxisText = []
		
	# add data
	q = 0
	for e in range( 0, min(len(data), 5) ):
		yAxisData.append(int(data[e]['count']))
		xAxisText.append(data[e]['city'])	
		xAxisData.append(q)
		q = q + 1

	# plot our data
	graph = pyplot.bar(xAxisData, yAxisData, align="center") 
	pyplot.title("Top five cities")

	# add our x-axis labels
	pyplot.xlim(min(xAxisData) - 1, max(xAxisData) + 1)
	pyplot.xticks( xAxisData, xAxisText)

	# fix padding and intervals for y axis
	pyplot.ylim(0, max(yAxisData) + 0.5)
	pyplot.yticks( range(0,max(yAxisData)+1,1) )

	# generate filename. note: we're starting with the
	# filename from our csv, so remove the csv and /
	# at the end and beginning of the string
	filename = filename[1:]
	filename = filename[:-3]
	filename = filename + "png"

	# save file
	pyplot.savefig(filename, bbox_inches = "tight")
	pyplot.close()

	return "/" + filename


# generates bar graph to go with query reports
def getGraphStates( data, filename ):
	yAxisData = [] # this will hold award count
	xAxisData = [] # this will hold city, state, or name
	xAxisText = []
		
	# add data
	q = 0
	for e in range( 0, min(len(data), 5) ):
		yAxisData.append(int(data[e]['count']))
		xAxisText.append(data[e]['state'])	
		xAxisData.append(q)
		q = q + 1

	# plot our data
	graph = pyplot.bar(xAxisData, yAxisData, align="center") 
	pyplot.title("Top five states")

	# add our x-axis labels
	pyplot.xlim(min(xAxisData) - 1, max(xAxisData) + 1)
	pyplot.xticks( xAxisData, xAxisText)

	# fix padding and intervals for y axis
	pyplot.ylim(0, max(yAxisData) + 0.5)
	pyplot.yticks( range(0,max(yAxisData)+1,1) )

	# generate filename. note: we're starting with the
	# filename from our csv, so remove the csv and /
	# at the end and beginning of the string
	filename = filename[1:]
	filename = filename[:-3]
	filename = filename + "png"

	# save file
	pyplot.savefig(filename, bbox_inches = "tight")
	pyplot.close()

	return "/" + filename


# routes the admin user to the appropriate report
# page depending on which query is selected in the URL
@app.route('/admin/analytics/agg/<queryType>')
@app.route('/admin/analytics/agg/<queryType>/')
@requiresAdmin
@requiresLogin
def queryAggRun(queryType):
	if queryType == "creator":
		awards = getAwardCountByCreator()
		csv = getCSV( awards )
		graph = getGraphCreator( awards, csv )	
		return render_template('queryCreator.html', 
					page=queryPage, 
					awards=awards,
					csv=csv, 
					graph=graph)
	elif queryType == "city":
		cities = getAwardCountByCity()
		csv = getCSV( cities )
		graph = getGraphCities( cities, csv )	
		return render_template('queryCity.html', 
					page=queryPage, 
					cities=cities,
					csv=csv, graph=graph)
	elif queryType == "state":
		states = getAwardCountByState()
		csv = getCSV( states )
		graph = getGraphStates( states, csv )	
		return render_template('queryState.html', 
					page=queryPage, 
					states=states,
					csv=csv, graph=graph)
	else:
		render_template('error.html', 
				message="Error: No such report", page=queryPage)


# generates a report with accompanying CSV with data organized
# date for a single award creator 
def getAOTByCreator(userId, days):

	# stringify our date into the form "YYYY-MM-DD"
	# because this is the most logical way to look
	# at dates...
	def strDate( date ):
		return str(date.year) + "-" + \
			str(date.month) + "-" +\
			str(date.day)

	# search awards for str date, and set corresponding
	# count to the new count value
	def addAtDate( awards, strDate, count ):
		for q in awards:
			if q['day'] == strDate:
				q['count'] = count
				break	
		return awards
	

	# pull our by-date data from the database
	query = session.query( award.creatorID, 
		award.awardDate,
		func.count(award.id).label('count')).\
		filter( award.creatorID == userId ).\
		group_by( award.creatorID, award.awardDate,
			func.extract('year', award.awardDate), 
			func.extract('month', award.awardDate), 
			func.extract('day', award.awardDate)).\
		order_by( desc(award.awardDate) )

	# now add a date entry for each day from today
	# back to start - days i.e. only go back 7, 30, 90
	# days and make sure that even if there were no
	# awards for a day that there is still an entry
	awards = []
	startDate = datetime.today() - timedelta(days=days)
	endDate = datetime.now()
	while endDate >= startDate:
		awards.append( { "day" : strDate(endDate),
				 "count" : 0 } )
		endDate = endDate - timedelta(days=1)

	for q in query:
		errorPrint(str(q[1]) + " processed...")
		if q[1] < startDate:
			break
		awards = addAtDate( awards, strDate(q[1]), q[2])

	return awards


# generates bar graph to go with query reports
def getAOTGraphCreator( data, days, filename ):
	yAxisData = [] # this will hold award count
	xAxisData = [] 
	xAxisText = [] 
		
	# add data
	i = 0
	for q in data:
		yAxisData.append(q['count'])
		xAxisData.append( matplotlib.dates.datestr2num(q['day']) )
		xAxisText.append("")
		i = i + 1

	# plot our data
	graph = pyplot.plot_date(x=xAxisData, y=yAxisData, fmt="r-") 
	pyplot.title("Last " + str(days) + " days")

	# add our x-axis labels
	pyplot.xlim(min(xAxisData) - 1, max(xAxisData) + 1)
	pyplot.xticks( xAxisData, xAxisText )

	# fix padding and intervals for y axis
	pyplot.ylim(0, max(yAxisData) + 0.5)
	pyplot.yticks( range(0,max(yAxisData)+1,1) )

	# generate filename. note: we're starting with the
	# filename from our csv, so remove the csv and /
	# at the end and beginning of the string
	filename = filename[1:]
	filename = filename[:-3]
	filename = filename + "png"

	# save file
	pyplot.savefig(filename, bbox_inches = "tight")
	pyplot.close()

	return "/" + filename


# routes the admin user to the appropriate report
# page depending on which query is selected in the URL
@app.route('/admin/analytics/time/<query_type>/<date_range>/<user_id>')
@app.route('/admin/analytics/time/<query_type>/<date_range>/<user_id>/')
@requiresAdmin
@requiresLogin
def queryAOTRun(query_type, date_range, user_id):
	def isValidDay( date_range ):
		days = int(date_range)
		if days == 90:
			return 90
		elif days == 30:
			return 30
		elif days == 7:
			return 7
		else:
			return -1

	days = isValidDay( date_range )
	if query_type == "creator" and days != -1:
		awards = getAOTByCreator(user_id, days) # AOT = awards over time
		csv = getCSV( awards )
		graph = getAOTGraphCreator( awards, days, csv )
		return render_template('queryAOTCreator.html', 
					page=queryPage, 
					awards=awards, 
					graph=graph,
					days=days, csv=csv)
	else:
		message = "There was an error generating your" + \
			"report. Please try again."
		return render_template('error.html', 
					message=message)


# routes the admin user to the appropriate report
# page depending on which query is selected in the URL
@app.route('/admin/analytics/time/<query_type>')
@app.route('/admin/analytics/time/<query_type>/')
@requiresAdmin
@requiresLogin
def queryAOTSetup(query_type):
	if query_type == "creator":
		users = session.query(User).all()
		return render_template('queryAOTCreatorSetup.html', 
			users=users, page=queryPage) 

# === DEPRECATED ===
#
# @app.route('/admin/analytics/time/<queryType>')
# @app.route('/admin/analytics/time/<queryType>/')
# @requiresAdmin
# @requiresLogin
# def queryRun(queryType):
# 	if queryType == "creator":
# 		awards = getAwardCountByCreator()
# 		csv = getCSV( awards )
# 		return render_template('queryCreator.html', 
# 					page=queryPage, 
# 					awards=awards,
# 					csv=csv)
# 	else:
# 		render_template('error.html', 
# 				message="Error: No such report", page=queryPage)



# user management dashboard for admin users. from here you can
# view, edit, delete, and create new users--both admin and
# award creators
@app.route('/admin/user')
@app.route('/admin/user/')
@requiresAdmin
@requiresLogin
def adminUser():
	users = session.query(User).all()
	return render_template('admin-user.html', users=users, page=adminPage) 


# pulls up a user's information by his/her id
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


# allows the admin user to edit a user with a given id
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
				creator.state = request.form.get('state', None)
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


# allows an admin to create a new user. the new user can either
# be an admin or award creator, i.e. these privileges are
# mutually exclusive
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
		state = request.form.get('state', None)
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
				newCreator = awardCreator(user.id, org, city, state, "blank")
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



# deletes a user of a given id
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


# deletes the user's cookie, both in his/her browser as well as
# our database, in effect logging the user out
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
    error=False
    error_list=[]
    fieldValues = {}
    if request.method == 'GET':
        return render_template('register.html', page=homePage, editProfile=False)	

    elif request.method == 'POST':
        register = request.form
        first_name = register['user-first-name']
        last_name = register['user-last-name']
        email = register['user-email']
        password = register['user-password']
        organization = register['user-org']
        city = register['user-city']
        state = register['user-state']

        #Input Validation	
        #First Name - Field is completed
        if not first_name:
            error = True
            error_list.append("First name is a required field.")
        else:
            fieldValues['firstName'] = first_name		

        #Last Name - Field is completed
        if not last_name:
       	    error = True
       	    error_list.append("Last name is a required field.")	
        else:
       	    fieldValues['lastName'] = last_name	

        #Email - Field is completed, field is valid, field is not duplicate
        if not email:
       	    error = True
       	    error_list.append("Email is a required field.")	
        else:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                error = True
                error_list.append("Please enter a valid email address.")
            elif re.match(r"[^@]+@[^@]+\.[^@]+", email):
                u = session.query(User).filter_by(email = email).first()
                if u != None:
                    error = True
                    error_list.append("Email address already registered. Please enter a new email address or login.")	
                else:
                    fieldValues['email'] = email	

        #Password - Field is completed
        if not password:
            error = True
            error_list.append("Password is a required field.")	
        else:
            fieldValues['password'] = organization	

        #Organization - Field is completed
        if not organization:
            error = True
            error_list.append("Organization is a required field.")	
        else:
            fieldValues['org'] = organization	

        #City - Field is completed
    	if not city:
            error = True
            error_list.append("City is a required field.")	
        else:
            fieldValues['city'] = city

    	#State - Field is completed and field is valid
    	if not state:
            error = True
            error_list.append("State is a required field.")
    	elif state:
            if not state.isalpha() or len(state) != 2:
                error = True
                error_list.append("Please enter a valid state code with 2 letters.")
            else:
                fieldValues['state'] = state

		#Image file - field is compelted and file type is valid
		#Save the signature file to the uploads folder
        filename = ''
        file_error = False
        file = request.files['user-signature']
        if not file or not allowed_file(file.filename):
           error = True
           file_error = True
           error_list.append("Please upload a valid Signature file (jpg, jpeg, png).")
        elif not file_error:	
           filename = secure_filename(file.filename)
           file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
           file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
           encoded_string = ""
           with open(file_path, "rb") as image_file:
              encoded_string = base64.b64encode(image_file.read())

        if not error:
            #Create a generic user
            new_user = User(first_name, last_name, email, password)
            session.add(new_user)
            session.commit()

            #Create an award creator
            new_award_creator = awardCreator(new_user.id, organization, city, state, encoded_string)
            session.add(new_award_creator)
            session.commit()

            message = True

    return render_template('register.html', message=message, page=homePage, editProfile=False, error=error, error_list=error_list, fieldValues=fieldValues)




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
    error=False
    error_list=[]
    fieldValues = {}
    if request.method == 'GET':
        return render_template('create_award.html', page=awardPage)	

    if request.method == 'POST':
        create_award = request.form
        fname = create_award['recipient-first-name']
        lname = create_award['recipient-last-name']
        email = create_award['recipient-email']
        award_type = create_award['award-type']
        award_date = create_award['award-date']
        award_time = create_award['award-time']

        #Input Validation	
        #First Name - Field is completed
        if not fname:
            error = True
            error_list.append("Recipient first name is a required field.")
        else:
            fieldValues['firstName'] = fname		

        #Last Name - Field is completed
        if not lname:
            error = True
            error_list.append("Recipient last name is a required field.")	
        else:
            fieldValues['lastName'] = lname	

        #Email - Field is completed, field is valid, field is not duplicate
        if not email:
            error = True
            error_list.append("Recipient email address is a required field.")	
        else:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                error = True
                error_list.append("Please enter a valid email address.")
            else:
                fieldValues['email'] = email

        #Award Date
        if not award_date:
            error = True
            error_list.append("Award date is a required field.")
        else:
            fieldValues['awardDate'] = award_date


        if not error:
            #Convert date and time to datetime format
            date_time = award_date + ' ' + award_time
            award_dt = datetime.strptime(date_time, '%Y-%m-%d %I:%M')

            #Get Logged in User ID
            user = getLoggedInUser()
            if user is not None:
                creatorID = user.id
            else:
                user.id = 0

            new_award = award(fname, lname, email, award_type, award_dt, creatorID)
            session.add(new_award)
            session.commit()

            award_user = session.query(awardCreator).filter_by(uid = user.id).first()
            signature = award_user.signature

            # Build the post params the service expects
            post_params = {
                'recipient_first_name': fname,
                'recipient_last_name': lname,
                'recipient_email': email,
                'award_date': str(award_date),
                'award_type': award_type,
                'awarder_first_name': user.fname,
                'awarder_last_name': user.lname,
                'awarder_signature': signature
            }

            r = requests.post('https://stormy-shelf-63646.herokuapp.com/generate', json=post_params)
            if r.status_code == 200:
                message = "Successfully sent email, please check your email soon!"
            else:
                error = True
                error_list.append("Problem connecting to email generation service, please try again later")

    return render_template('create_award.html', message=message, page=awardPage, error=error, error_list=error_list, fieldValues=fieldValues)


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
                        # message = sys.exc_info()
                        # message = "Failed to reset password."
			message = "There was an error trying to reset " + \
				"your password. Please check your " + \
				"email address and try again. "
                        return render_template('error.html', message=message)


# catch all to route bad URIs
@app.route("/<path:path>")
def notFound(path):
	message = "404: page \"" + path + "\" not found"
	return render_template('error.html', message=message)
