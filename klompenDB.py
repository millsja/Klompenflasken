from datetime import datetime
import sqlalchemy
from sqlalchemy import Table, Column, Integer, String, ForeignKey, DateTime, Boolean

def connect(user, passwd, db, host='localhost', port=5432):
	uri = 'postgresql://' + user + ":" + passwd
	uri = uri + '@' + host + ':' + str(port) + '/' + db
	connection = sqlalchemy.create_engine(uri, client_encoding='utf8')
	metaData = sqlalchemy.MetaData(bind=connection, reflect=True)
	return connection, metaData

def createTables(connection):
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

	awardCreator = Table('awardCreator', meta,
		Column('uid', Integer, ForeignKey('user.id'), primary_key=True),
		Column('org', String(128), nullable=False),
		Column('city', String(64), nullable=False),
		Column('signature', String(64), nullable=False)
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

	meta.create_all(connection)

if __name__ == "__main__":
	con, meta = connect('klompen_db_user', 'BlueDanceMoon42', 'klompen_db')
	createTables(con)	
