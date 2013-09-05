#!/usr/bin/env python
import random
import string

PASSWORD = "correcthorsebatterystaple"
NEWPASSWORD = PASSWORD[::-1]

TESTS = [
    'sanity', 
    'time_now',
    'time_difference',
    'user_get',
    'user_setpassword', 
    'user_setemail', 
    'newuser_new', 
    'record_get', 
    'record_new'
]


def randword(length):
    s = string.lowercase + string.digits
    return ''.join(random.sample(s,length))


def sanity(db):
    # Sanity check
    db.user.get('root')
    db.paramdef.get('root')
    db.recorddef.get('root')
    db.group.get('admin')
    db.record.get('root')


######################################

def time_now(db):
    db.time.now()

def time_difference(db):
    db.time.difference('2013-01-01')

def version(db):
    pass

def ping(db):
    pass

######################################
    
def auth_login(db):
    pass

def auth_logout(db):
    pass

def auth_check_context(db):
    pass

def auth_check_admin(db):
    pass

def auth_check_create(db):
    pass
    
######################################
    
def query(db):
    pass

def table(db):
    pass    

def plot(db):
    pass

######################################

def render(db):
    pass    

def view(db):
    pass

######################################

def rel_pclink(db):
    pass

def rel_pcunlink(db):
    pass

def rel_relink(db):
    pass

def rel_siblings(db):
    pass

def rel_parents(db):
    pass

def rel_children(db):
    pass    

def rel_tree(db):
    pass

######################################

def paramdef_get(db):
    pass

def paramdef_new(db):
    pass

def paramdef_put(db):
    pass

def paramdef_filter(db):
    pass

def paramdef_find(db):
    pass

def paramdef_properties(db):
    pass

def paramdef_units(db):
    pass

def paramdef_vartypes(db):
    pass

######################################

def user_new(db):
    pass

def user_put(db):
    pass

def user_filter(db):
    pass

def user_find(db):
    pass

def user_get(db):
    db.user.get('root')
    try:
        db.user.get('fail', filt=False)
    except KeyError:
        pass
    
def user_setpassword(db):
    user = newuser_new(db)
    db.user.setpassword(user.name, NEWPASSWORD, password=PASSWORD)
    db.auth.login(user.name, NEWPASSWORD)

def user_setemail(db):
    user = newuser_new(db)
    email = 'new-%s@example.com'%randword(10)
    db.user.setemail(user.name, email, password=PASSWORD)
    db.auth.login(email, PASSWORD)

def user_resetpassword(db):
    pass
    
def user_expirepassword(db):
    pass
    
def user_setprivacy(db):
    pass
    
def user_setdisable(db):
    pass

######################################

def newuser_new(db):
    # Tests newuser_new, newuser_approve
    # Request user
    email = 'test-%s@example.com'%randword(10)
    user = db.newuser.new(email=email, name_first='Bobby', name_last='Tables', password=PASSWORD)
    user = db.newuser.request(user)
    
    # Approve user
    db.newuser.approve(user.name)

    # Try to login with new user
    db.auth.login(user.name, PASSWORD)
    db.auth.login(email, PASSWORD)
    return user

def newuser_request(db):
    pass
    
def newuser_approve(db):
    pass

def newuser_reject(db):
    pass
    
######################################

def group_(db):
    pass

######################################
        
def recorddef_(db):
    pass

######################################

def record_get(db):
    db.record.get('root')
    try:
        db.record.get('fail', filt=False)
    except KeyError:
        pass

def record_new(db):
    # New record test
    rec = db.record.new(rectype='root')
    rec = db.record.put(rec)

    # Child records
    child = db.record.new(rectype='root', inherit=[rec.name])
    db.record.put(child)
    

def record_hide(db):
    pass
    
def record_update(db):
    pass
    
def record_validate(db):
    pass
    
def record_adduser(db):
    pass
    
def record_removeuser(db):
    pass
    
def record_addgroup(db):
    pass
    
def record_removegroup(db):
    pass
    
def record_setpermissionscompat(db):
    # ugh
    pass
    
def record_addcomment(db):
    pass
    
def record_findcomments(db):
    pass

def record_findorphans(db):
    pass

def record_findbyrectype(db):
    pass
    
def record_findbyvalue(db):
    pass
    
def record_groupbyrectype(db):
    pass
    
def record_renderchildren(db):
    pass

def record_findpaths(db):
    pass
    
######################################

def binary_get(db):
    pass
    
def binary_new(db):
    pass
    
def binary_find(db):
    pass

def binary_filter(db):
    pass

def binary_put(db):
    pass

def binary_upload(db):
    pass
    
def binary_addreference(db):
    pass
    
######################################
        
if __name__ == "__main__":
    import emen2.db
    import emen2.db.config
    opts = emen2.db.config.DBOptions()
    opts.add_argument("--test", help="Test to run. Default is all.", action="append")
    args = opts.parse_args()
    db = emen2.db.opendb(admin=True)

    tests = args.test or TESTS
    for i in tests:
        print "\n\n===== TESTING: %s ====="%i
        with db:
            globals()[i](db)
    