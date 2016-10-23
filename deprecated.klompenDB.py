from datetime import datetime
import sqlalchemy
from sqlalchemy import (
	Table, Column, Integer, String, ForeignKey, DateTime, Boolean )
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
class User(Base):
	__tablename__ = 'user'
	id = Column(Integer, primary_key=True),
	fname = Column(String(64)),
	lname = Column(String(64)),
	email = Column(String(64), unique=True, nullable=False),
	passwd = Column(String(64), nullable=False),
	created = Column(DateTime, 
			default=datetime.utcnow,
			nullable=False),
	admin = Column(Boolean, default=False)

class Cookie(Base):
	__tablename__ = 'cookie'
	id = Column(Integer, primary_key=True),
	uid = Column(Integer, ForeignKey('user.id'), primary_key=True),
	created = Column(DateTime, 
			default=datetime.utcnow,
			nullable=False)

class awardCreator(Base):
	__tablename__ = 'awardCreator'
	uid = Column(Integer, ForeignKey('user.id'), primary_key=True),
	org = Column(String(128), nullable=False),
	city = Column(String(64), nullable=False),
	# Column('signature', String(64), nullable=False)

class awardType(Base):
	__tablename__ = 'awardType'
	id = Column(Integer, primary_key=True),
	name = Column(String(128), nullable=False)

class award(Base):
	__tablename__ = 'award'
	id = Column(Integer, primary_key=True),
	fname = Column(String(64), nullable=False),
	lname = Column(String(64), nullable=False),
	email = Column(String(64), nullable=False),
	creatorId = Column(Integer, ForeignKey('awardCreator.uid')),
	awardTypeId = Column(Integer, ForeignKey('awardType.id')),
	created = Column(DateTime, 
			default=datetime.utcnow,
			nullable=False),

def connect(user, passwd, db, host='localhost', port=5432):
	uri = 'postgresql://' + user + ":" + passwd
	uri = uri + '@' + host + ':' + str(port) + '/' + db
	connection = sqlalchemy.create_engine(uri, client_encoding='utf8')
	Base.metadata.bind = connection
	dbSession = sessionmaker(bind = engine)
	session = dbSession()
	return connection, session

def createTables():
	con, session = connect('klompen_db_user', 'BlueDanceMoon42', 'klompen_db')
	Base.metadata.
	Base.metadata.create_all(con)

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
	createTables(con)
	popTables(con, meta)	
