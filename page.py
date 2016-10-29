# class of objects passed along with the page object to
# our templates, which are then displayed on the navigatoin
# panel at the top
class Link(object):
	def __init__(self, url, name):
		self.url = url
		self.name = name

# Page objects contain data that can be passed to the base
# including title and links, which are displayed on the
# navigation panel
class Page(object):
	def __init__(self, inTitle, inLinks):
		self.links = []
		self.title = inTitle
		for l in inLinks:
			self.links.append(l)


# default admin page info
adminLinks = [ Link("/admin/user", "Users"),
		Link("/admin/analytics", "Analytics"),
		Link("/admin/user/create", "Create user"),
		Link("/logout", "Log out") ]
adminPage = Page("Admin section", adminLinks)


# default admin page info
homeLinks = [ Link("/admin", "Admin"),
		Link("/create_award", "Create award") ]
homePage = Page("Klompendansen", homeLinks)

if __name__ == "__main__":
	print "---Pages---:"
	print "admin page: " + adminPage.title
	print "links: ", 
	for l in adminPage.links:
		print l.name,

	print "" + "" 
	print "home page: " + homePage.title
	print "links: ", 
	for l in homePage.links:
		print l.name, 
