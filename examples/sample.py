import jsonrpc.proxy
import getpass

# HOST = sys.argv[1]
HOST = "http://ncmidb.bcm.edu"
USER = raw_input("Username: ")
PW = getpass.getpass("Password: ")

# Root record and an example project
ROOT = 0
PROJECT = 137


###### Login #####

db = jsonrpc.proxy.JSONRPCProxy(host=HOST)
ctxid = db.login(USER, PW)


##### Getting Records (simple) #####

# Get a record
rec = db.getrecord(ROOT)
print "Root record:"
print rec

# getrecord will return a single item if you ask for a single item;
# or a list of items if you ask for a list of items.
recs = db.getrecord([0,1,2,3])
print "Records: ", [i.get('name') for i in recs]






##### Children and grouping #####

# Children and parents of a record can be accessed in the 'children' and 'parents' keys.
children = rec.get('children')

# Get the child records.
children = db.getrecord(children)
print "Got %s child records"%(len(children))

# Get the children, recursively. This returns record IDs.
children = db.getchildren(ROOT, recurse=2)
print "Found %s children with recurse=2"%len(children)

# Or get a dictionary containing the children of each item.
childtree = db.getchildtree(ROOT, recurse=2)
# Key is the record ID, value is the direct children for that record.

# Use recurse=-1 to find all children
children = db.getchildren(PROJECT, recurse=-1)
print "Found %s children in project %s"%(len(children), PROJECT)

# Group these records by rectype
rectypes = db.groupbyrectype(children)
print "... by rectype (sorted):"
for k,v in sorted(rectypes.items(), key=lambda x:len(x[1])):
		print "\t", k, len(v)

# Get all projects you can access. This may include hidden records.
projects = db.getindexbyrectype("project")
print "I can access %s projects"%len(projects)

# rectype* and [rectypes] also work.
projects = db.getindexbyrectype("project*")
print "... and %s projects*"%len(projects)








##### Rendered records #####

projects = db.getindexbyrectype("project")[:5]
projnames = db.renderview(projects)
print "Some project names (sorted):"
for k,v in sorted(projnames.items(), key=lambda x:str(x[1] or '').lower()):
	print "\t", k, v

# Use viewname= to render using a particular RecordDef view.
projmainview = db.renderview(PROJECT, viewname="mainview")
projdefaultview = db.renderview(PROJECT, viewname="defaultview")









##### New records and writing records #####

# Create a new record
newrecord = db.newrecord('folder')

# Commit
# newrecord = db.putrecord(newrecord)

# Hide a record
# db.hiderecord(newrecord.get('name'))

# Edit an existing record
editrec = db.getrecord(PROJECT)
editrec["comments"] = "This is a new comment."
editrec["name_first"] = "Funny name"
# editrec = db.putrecord(editrec)

# Like most calls, you can also edit multiple items at once.
editrecs = db.getrecord([0,1,2,3,4])
for i in editrecs:
	i["name_first"] = "counter: %s"%i
# db.putrecord(editrecs)








##### Users #####

# Get your user profile
user = db.getuser(USER)
# The display name is made from your profile record.
print "User name: %s, display name: %s"%(user.get('name'), user.get('displayname'))

# Check privileges.
print "Am I an admin?:", db.checkadmin()
print "Can I create records, recorddefs, etc.?: ", bool(db.checkcreate())

users = db.getusernames()
print "There are %s users in the system"%(len(users))

users = db.getuser(users)
print "... and their display names are: %s, ...."%(", ".join([i.get('displayname') for i in users[:10]]))

# Find a user..
users = db.finduser("rees")
print "Found %s users for query 'rees'"%len(users)





##### User queue and new users #####
# Get the user approval queue
userqueue = db.getuserqueue()
print "There are %s users in the approval queue."%len(userqueue)

# Create a New User
# newuser = db.newuser(name='asd123', password='asd123', email='ian@example.com')

# Add the new user to the approval queue
# user = db.adduser(newuser)

# Approve or reject the new user
# db.approveuser(user.get('name'))
# db.rejectuser(user.get('name'))



##### RecordDefs #####
recorddef = db.getrecorddef('folder')
print "RecordDef:", recorddef


##### ParamDefs #####

# Get a ParamDef
paramdef = db.getparamdef('name_first')
print "ParamDef:", paramdef

newparamdef = db.newparamdef(name='test_paramdef', vartype='string')
# newparamdef = db.putparamdef(newparamdef)

# Find a ParamDef
paramdefs = db.findparamdef(vartype='user')
print "User paramDefs:", [i.get('name') for i in paramdefs]
