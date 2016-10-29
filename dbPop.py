from datetime import datetime
from sqlalchemy.orm import sessionmaker
#from db import ( Base, User, awardCreator, awardType, award)
from db import ( Base, User, awardCreator, award)
from db import connect

# make connection / session
con = connect('klompen_db_user', 'BlueDanceMoon42', 'klompen_db')
Base.metadata.bind = con
dbSession = sessionmaker(bind=con)
session = dbSession()


admins = [ {"fname": "James",
		"lname": "Mills",
		"email": "millsja@oregonstate.edu",
		"passwd": "orange",
		"admin": True } ]
		
creators = [ {"fname": "Jean",
		"lname": "Valjean",
		"email": "jean.valjean@example.com",
		"passwd": "24601",
		"org": "Nike Manufacturing, Inc.",
		"city": "St-Denis",
		"admin": False },

		{"fname": "Inspector",
		"lname": "Javert",
		"email": "javert@example.com",
		"passwd": "stars",
		"org": "City of Paris",
		"city": "Paris",
		"admin": False },

		{"fname": "Bernard",
		"lname": "Thenardier",
		"email": "masterofthehouse@example.com",
		"passwd": "raiseaglass",
		"org": "Sargeant de Waterloo",
		"city": "Montfermeil",
		"admin": False } ]

# awardtypes = [ {"name": "Employee of the month"},
# 		{"name": "You're fired"},
# 		{"name": "Most convictions"} ]

awards = [ {"fname": "Mademoiselle",
		"lname": "Cosette",
		"email": "castleonacloud@example.com",
		"creatorEmail": "jean.valjean@example.com",
		"awardName": "Employee of the month"},
		
		{"fname": "Fantine",
		"lname": "Dubois",
		"email": "fdubois@example.com",
		"creatorEmail": "jean.valjean@example.com",
		"awardName": "Employee of the month"},

		{"fname": "Madame",
		"lname": "Thenardier",
		"email": "foodbeyondbelief@example.com",
		"creatorEmail": "masterofthehouse@example.com",
		"awardName": "You're fired"},

		{"fname": "Hercule",
		"lname": "Poirot",
		"email": "therealsorbo@example.com",
		"creatorEmail": "javert@example.com",
		"awardName": "The award for most convictions"} ]

# clear our user table to start from scratch
session.query(awardCreator).delete()
session.query(User).delete()
session.commit()


# insert admins into user table
for a in admins:
        print "Adding " + a['email'] + "..."

	newAdmin = User(fname = a['fname'],
			lname = a['lname'],
			passwd = a['passwd'],
			email = a['email'],
			admin = a['admin'])

	session.add(newAdmin)

session.commit()


# add some regular users
for a in creators:
        print "Adding " + a['email'] + "..."

	# create the user entry in the database
	newUser = User(fname = a['fname'],
			lname = a['lname'],
			passwd = a['passwd'],
			email = a['email'],
			admin = a['admin'])
	session.add(newUser)

	# create the award creator entry
	u = session.query(User).filter_by( email = a['email'] ).first()
	newCreator = awardCreator(uid = u.id,
				city = a['city'],
				org = a['org'])	
	session.add(newCreator)

session.commit()
