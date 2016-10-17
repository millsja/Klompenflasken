from datetime import datetime
import sqlalchemy
from sqlalchemy import Table, Column, Integer, String, ForeignKey, DateTime, Boolean

def connect(user, passwd, db, host='localhost', port=5432):
	uri = 'postgresql://' + user + ":" + passwd
	uri = uri + '@' + host + ':' + str(port) + '/' + db
	connection = sqlalchemy.create_engine(uri, client_encoding='utf8')
	metaData = sqlalchemy.MetaData(bind=connection, reflect=True)
	return connection, metaData

def createTables(con, meta):
	user = Table('user', meta,
		Column('id', Integer, primary_key=True),
		Column('fname', String(64)),
		Column('lname', String(64)),
		Column('email', String(64), unique=True, nullable=False),
		Column('passwd', String(64), nullable=False),
		Column('created', DateTime, 
					default=datetime.utcnow,
					nullable=False),
		Column('admin', Boolean, default=False)
	)

	cookie = Table('cookie', meta,
		Column('id', Integer, primary_key=True),
		Column('uid', Integer, ForeignKey('user.id'), primary_key=True),
		Column('created', DateTime, 
					default=datetime.utcnow,
					nullable=False)
	)

	awardCreator = Table('awardCreator', meta,
		Column('uid', Integer, ForeignKey('user.id'), primary_key=True),
		Column('org', String(128), nullable=False),
		Column('city', String(64), nullable=False),
		# Column('signature', String(64), nullable=False)
	)

	awardType = Table('awardType', meta,
		Column('id', Integer, primary_key=True),
		Column('name', String(128), nullable=False)
	)

	award = Table('award', meta,
		Column('id', Integer, primary_key=True),
		Column('fname', String(64), nullable=False),
		Column('fname', String(64), nullable=False),
		Column('email', String(64), nullable=False),
		Column('creatorId', Integer, ForeignKey('awardCreator.uid')),
		Column('awardTypeId', Integer, ForeignKey('awardType.id')),
		Column('created', DateTime, 
					default=datetime.utcnow,
					nullable=False),
	)

	meta.create_all(con)


def dropTables(con, meta):
	meta.drop_all(con)

def popTables(con, meta):
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

	awardtypes = [ {"name": "Employee of the month"},
			{"name": "You're fired"},
			{"name": "Most convictions"} ]

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

	# insert admins into user table
	# con.execute(meta.tables['user'].insert(), admins)

	# insert award creators into user table and creator table
	userTable = meta.tables['user']	
	creatorTable = meta.tables['awardCreator']
	for user in creators:
		# insert into user table
		action = userTable.insert().values(
			fname = user['fname'],
			lname = user['lname'],
			email = user['email'],
			passwd = user['passwd']
		)
		result = con.execute(action)

		# get new user id
		lastAdded = result.inserted_primary_key[0]

		# insert user into creator table
		action = creatorTable.insert().values(
			uid = lastAdded,
			org = user['org'],
			city = user['city']
		)
		result = con.execute(action)
			
if __name__ == "__main__":
	con, meta = connect('klompen_db_user', 'BlueDanceMoon42', 'klompen_db')
	dropTables(con, meta)
	createTables(con, meta)
	popTables(con, meta)	
