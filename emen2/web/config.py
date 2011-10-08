import emen2.db.config
g = emen2.db.config.g()
inst =lambda x:x()

@inst
class CVars(emen2.db.config.CVars):
	bookmarks = g.claim('bookmarks.BOOKMARKS', {})
	logo = g.claim('customization.EMEN2LOGO', '')
