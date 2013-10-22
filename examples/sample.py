import jsonrpc.proxy
import getpass
import sys


# HOST = sys.argv[1]
HOST = "http://ncmidb.bcm.edu"
USER = raw_input("Username: ")
PW = getpass.getpass("Password: ")
WRITE = False
ADMIN = False

# Example project.
PROJECT = 137




##################
###### Login #####
##################

db = jsonrpc.proxy.JSONRPCProxy(host=HOST)
ctxid = db.login(USER, PW)





####################################
##### Getting Records (simple) #####
####################################

# Get a record
rec = db.record.get(PROJECT)
print "Root record:"
print rec

# db.record.get will return a single item if you ask for a single item;
# or a list of items if you ask for a list of items.
recs = db.record.get([0,1,2,3])
print "Records: ", [i.get('name') for i in recs]





#################################
##### Children and grouping #####
#################################

# Find the children of a record.
children = db.rel.children(PROJECT)

# Get the child records.
children = db.record.get(children)
print "Got %s child records"%(len(children))

# Get the children, recursively. This returns record IDs.
children = db.rel.children(PROJECT, recurse=2)
print "Found %s children (recurse=2)"%len(children)

# Use recurse=-1 to find all children
children = db.rel.children(PROJECT, recurse=-1)
print "Found %s children in project %s (recurse=-1)"%(len(children), PROJECT)

# Group these records by rectype
rectypes = db.record.groupbyrectype(children)
print "... by rectype (sorted):"
for k,v in sorted(rectypes.items(), key=lambda x:len(x[1]), reverse=True):
		print "\t", k, len(v)

# Get all projects you can access.
projects = db.record.findbyrectype("project")
print "I can access %s projects."%len(projects)

# rectype* and [rectypes] also work.
projects = db.record.findbyrectype("project*")
print "... and %s projects* -- includes project, subproject, software_project, etc."%len(projects)





############################
##### Rendered records #####
############################

projects = db.record.findbyrectype("project")[:5]
projnames = db.record.render(projects)
print "Some project"
for k,v in sorted(projnames.items(), key=lambda x:str(x[1] or '').lower()):
	print "\t", k, v

# Use viewname= to render using a particular RecordDef view.
projmainview = db.record.render(PROJECT, viewname="mainview")
projdefaultview = db.record.render(PROJECT, viewname="defaultview")





###########################################
##### New records and writing records #####
###########################################

if WRITE:
    # Create a new record
    newrecord = db.record.new(rectype='folder')

    newrecord = db.putrecord(newrecord)

    # Hide a record
    db.record.hide(newrecord.get('name'))

    # Edit an existing record
    editrec = db.record.get(newrecord.get('name'))
    editrec["comments"] = "This is a new comment."
    editrec["name_first"] = "Funny name"
    # editrec = db.putrecord(editrec)

    # Like most calls, you can also edit multiple items at once.
    # editrecs = db.record.get([0,1,2,3,4])
    # for i in editrecs:
    #	i["name_first"] = "counter: %s"%i
    # db.record.put(editrecs)






#################
##### Users #####
#################

# Get your user profile
user = db.user.get(USER)
# The display name is made from your profile.
print "User name: %s, display name: %s"%(user.get('name'), user.get('displayname'))

# Check privileges.
print "Am I an admin?:", db.auth.check.admin()
print "Can I create records, recorddefs, etc.?: ", bool(db.auth.check.create())

users = db.user.names()
print "There are %s users in the system"%(len(users))

users = db.user.get(users[:10])
print "... and their display names are: %s, ...."%(", ".join([i.get('displayname') for i in users]))

# Find a user..
users = db.user.find("rees")
print "Found %s users for query 'rees'"%len(users)

##### User queue and new users #####
# Get the user approval queue
userqueue = db.newuser.queue()
print "There are %s users in the approval queue."%len(userqueue)

# Create a New User
# newuser = db.newuser.new(name='asd123', password='asd123', email='ian@example.com')

# Add the new user to the approval queue
# user = db.adduser(newuser)

# Approve or reject the new user
# db.approveuser(user.get('name'))
# db.rejectuser(user.get('name'))




######################
##### RecordDefs #####
######################
recorddef = db.recorddef.get('folder')
print "RecordDef:", recorddef




######################
##### ParamDefs #####
######################

# Get a ParamDef
paramdef = db.paramdef.get('name_first')
print "ParamDef:", paramdef

# Find a ParamDef
paramdefs = db.paramdef.find(vartype='user')
print "User ParamDefs:", [i.get('name') for i in paramdefs]

paramdefs = db.paramdef.find('vitrobot')
print "Vitrobot ParamDefs:", [i.get('name') for i in paramdefs]


if WRITE:
    newparamdef = db.paramdef.new(name='test_paramdef', vartype='string')
    # newparamdef = db.putparamdef(newparamdef)
    











