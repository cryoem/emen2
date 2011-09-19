# import emen2.db
# db = emen2.db.opendb()
# 
# import emen2.db.database
# tmpl = emen2.db.database.g.templates.get_template('/raw')

# print emen2.db.database.g.templates
# print tmpl.render(content='test')

# import mako.lookup
# import time
# 
# class MyLookup(mako.lookup.TemplateLookup):
#     def get_template(self, uri):
# 		return super(MyLookup, self).get_template(uri+".mako")
# 		
# 		
# c = MyLookup()
# c.directories.append('test1')
# c.directories.append('test2')
# print c.directories
# 
# while True:
# 	tmpl = c.get_template('/test')
# 	print tmpl.render(**{'content':'OK','title':'Test'})
# 	time.sleep(1)