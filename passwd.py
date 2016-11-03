from string import ascii_letters, digits
from random import random, choice
import smtplib

SEND_PASS = "BlueDanceMoon42"
PASS_LEN = 8

# generates a pseudo random alpha-numeric password of 
# length number of bytes
def genPasswd( length ):
	newPasswd = ""
	for q in range(length):
		newPasswd = newPasswd + choice( ascii_letters + digits)
	return newPasswd


# takes an email content object and formats it into
# a string using proper smtp
def formEmail( content ):
	try:
		email = "From: " + content['from'] + "\n" + \
			"To: " + content['to'] + "\n" + \
			"Subect: " + content['subject'] + "\n\n" + \
			content['body']
	except:
		email = None

	return email
	

# sends a password to a user's email address
# note: does not generate password and does not store
#	passwd in database
def sendPass( fname, email, passwd ):
	content = {}
	content['subject'] = "Klomp: password recovery"
	content['from'] = "team.klompen@gmail.com"
	content['to'] = email
	content['body'] = "Dear " + fname + ",\n\n" + \
			  "Your new password is: " + passwd + "\n\n" + \
			  "Kind regards,\n\nThe Klompendansen Team"

	# set up gmail connection
	serv = smtplib.SMTP('smtp.gmail.com', 587)

	# say "hello" to our gmail server
	serv.ehlo()

	# start encryption services
	serv.starttls()
	serv.ehlo() # per documentation, we need to helo again

	# log in
	serv.login(content['from'], SEND_PASS)

	# send our stuff
	serv.sendmail(content['from'], content['to'], formEmail(content))
	serv.quit()	


# generates a new password and sends to the user
# note: does not store passwd in database
def resetPasswd( fname, email ):
	newPass = genPasswd( PASS_LEN )
	sendPass( fname, email, newPass )
	return newPass 


# test run to see whether everything works
if __name__ == "__main__":
	print "New passwd: " + resetPasswd( "James", "millsja@oregonstate.edu")
