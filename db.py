from datetime import datetime
from sqlalchemy import (
	Table, Column, Integer, String, ForeignKey, DateTime, Boolean )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()
class User(Base):
	__tablename__ = 'user'
	id = Column(Integer, primary_key=True)
	fname = Column(String(64))
	lname = Column(String(64))
	email = Column(String(64), unique=True, nullable=False)
	passwd = Column(String(64), nullable=False)
	created = Column(DateTime, 
			default=datetime.utcnow,
			nullable=False)
	admin = Column(Boolean, default=False)
	cookie = Column(String(64), unique=True)

	#louise
	def __init__(self, fname, lname, email, passwd, admin=False):
		self.fname = fname
		self.lname = lname
		self.email = email
		self.passwd = passwd
		self.admin = admin 
	

# class Cookie(Base):
# 	__tablename__ = 'cookie'
# 	id = Column(Integer, primary_key=True)
# 	uid = Column(Integer, ForeignKey('user.id'), primary_key=True)
# 	created = Column(DateTime, 
# 			default=datetime.utcnow,
# 			nullable=False)

class awardCreator(Base):
	__tablename__ = 'awardCreator'
	uid = Column(Integer, ForeignKey('user.id'), primary_key=True)
	org = Column(String(128), nullable=False)
	city = Column(String(64), nullable=False)
	signature = Column(String(128), nullable=False)
	# Column('signature', String(64), nullable=False)

	#louise
	def __init__(self, uid, org, city, signature):
		self.uid = uid
		self.org = org
		self.city = city
		self.signature = signature


# class awardType(Base):
# 	__tablename__ = 'awardType'
# 	id = Column(Integer, primary_key=True)
# 	name = Column(String(128), nullable=False)

# class award(Base):
# 	__tablename__ = 'award'
# 	id = Column(Integer, primary_key=True)
# 	fname = Column(String(64), nullable=False)
# 	lname = Column(String(64), nullable=False)
# 	email = Column(String(64), nullable=False)
# 	creatorId = Column(Integer, ForeignKey('awardCreator.uid'))
# 	awardTypeId = Column(Integer, ForeignKey('awardType.id'))
# 	created = Column(DateTime, 
# 			default=datetime.utcnow,
# 			nullable=False)

class award(Base):
	__tablename__ = 'award'
	id = Column(Integer, primary_key=True)
	fname = Column(String(64), nullable=False)
	lname = Column(String(64), nullable=False)
	email = Column(String(64), nullable=False)
	awardType = Column(String(64), nullable=False)
	awardDate = Column(DateTime, nullable=False)
	creatorID = Column(Integer, ForeignKey('awardCreator.uid'))

	def __init__(self, fname, lname, email, awardType, awardDate, creatorID):
		self.fname = fname
		self.lname = lname
		self.email = email
		self.awardType = awardType
		self.awardDate = awardDate
		self.creatorID = creatorID


def connect(user, passwd, db, host='localhost', port=5432):
	uri = 'postgresql://' + user + ":" + passwd
	uri = uri + '@' + host + ':' + str(port) + '/' + db
	connection = create_engine(uri, client_encoding='utf8')
	return connection

con = connect('klompen_db_user', 'BlueDanceMoon42', 'klompen_db')
Base.metadata.create_all(con)
