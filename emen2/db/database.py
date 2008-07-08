from bsddb3 import db
from emen2.Database.exceptions import *
import sys
import traceback
import os
import hashlib
import time
from emen2.subsystems import macro
from user import *
from btrees import *
from datastorage import *

regex_pattern =  u"(?P<var>(\$\$(?P<var1>\w*)(?:=\"(?P<var2>[\w\s]+)\")?))(?P<varsep>[\s<]?)"    \
"|(?P<macro>(\$\@(?P<macro1>\w*)(?:\((?P<macro2>[\w\s]+)\))?))(?P<macrosep>[\s<]?)" \
                "|(?P<name>(\$\#(?P<name1>\w*)(?P<namesep>[\s<:]?)))"
regex = re.compile(regex_pattern, re.UNICODE) # re.UNICODE

regex_pattern2 =  u"(\$\$(?P<var>(?P<var1>\w*)(?:=\"(?P<var2>[\w\s]+)\")?))(?P<varsep>[\s<]?)"    \
                "|(\$\@(?P<macro>(?P<macro1>\w*)(?:\((?P<macro2>[\w\s]+)\))?))(?P<macrosep>[\s<]?)" \
                "|(\$\#(?P<name>(?P<name1>\w*)))(?P<namesep>[\s<:]?)"
regex2 = re.compile(regex_pattern2, re.UNICODE) # re.UNICODE

recommentsregex = "\n"
pcomments = re.compile(recommentsregex) # re.UNICODE

TIMESTR="%Y/%m/%d %H:%M:%S"

class DBProxy2:
    def __init__(self,db,ctxid,host):
        self.db=db
        self.ctxid=ctxid
        self.host=host
    def __getattr__(self,name):
        return lambda *x: self(name,*x)        
    def __call__(self,*args, **kwargs):
        kwargs["ctxid"]=self.ctxid
        kwargs["host"]=self.host
        print args
        print kwargs
        return getattr(self.db,args[0])(*args[1:], **kwargs)

usetxn=False
envopenflags=db.DB_CREATE|db.DB_INIT_MPOOL|db.DB_INIT_LOCK|db.DB_INIT_LOG|db.DB_THREAD
LOGSTRINGS = ["SECURITY", "CRITICAL","ERROR   ","WARNING ","INFO    ","VERBOSE ","DEBUG   "]
DEBUG = 0 #TODO consolidate debug flag

def DB_syncall():
    """This 'syncs' all open databases"""
    if DEBUG>2: print "sync %d BDB databases"%(len(BTree.alltrees)+len(IntBTree.alltrees)+len(FieldBTree.alltrees))
    t=time.time()
    for i in BTree.alltrees.keys(): i.sync()
    for i in IntBTree.alltrees.keys(): i.sync()
    for i in FieldBTree.alltrees.keys(): i.sync()
#    print "%f sec to sync"%(time.time()-t)


#keys(), values(), items(), has_key(), get(), clear(), setdefault(), iterkeys(), itervalues(), iteritems(), pop(), popitem(), copy(), and update()    
class Database(object):
    """This class represents the database as a whole. There are 3 primary identifiers used in the database:
    dbid - Database id, a unique identifier for this database server
    recid - Record id, a unique (32 bit int) identifier for a particular record
    ctxid - A key for a database 'context' (also called a session), allows access for pre-authenticated user
    
    TODO : Probably should make more of the member variables private for slightly better security"""
    def __init__(self,path=".",cachesize=32000000,logfile="db.log",importmode=0,rootpw=None,recover=0,allowclose=True):
        """path - The path to the database files, this is the root of a tree of directories for the database
cachesize - default is 64M, in bytes
logfile - defualt "db.log"
importmode - DANGEROUS, makes certain changes to allow bulk data import. Should be opened by only a single thread in importmode.
recover - Only one thread should call this. Will run recovery on the environment before opening."""
        global envopenflags,usetxn
                
        if usetxn: self.newtxn=self.newtxn1
        else: self.newtxn=self.newtxn2

        self.path=path
        self.logfile=path+"/"+logfile
        self.lastctxclean=time.time()
        self.__importmode=importmode
    
        self.maxrecurse=50
    
        xtraflags=0
        if recover: xtraflags=db.DB_RECOVER
        
        # This sets up a DB environment, which allows multithreaded access, transactions, etc.
        if not os.access(path+"/home",os.F_OK) : os.makedirs(path+"/home")
        self.LOG(4,"Database initialization started")
        self.__allowclose = bool(allowclose)
        self.__dbenv=db.DBEnv()
        self.__dbenv.set_cachesize(0,cachesize,4)        # gbytes, bytes, ncache (splits into groups)
        self.__dbenv.set_data_dir(path)
        self.__dbenv.set_lk_detect(db.DB_LOCK_DEFAULT)    # internal deadlock detection

        # ian: lockers
        self.__dbenv.set_lk_max_locks(5000)
        self.__dbenv.set_lk_max_lockers(5000)
        
        #if self.__dbenv.DBfailchk(flags=0) :
            #self.LOG(1,"Database recovery required")
            #sys.exit(1)
            
        self.__dbenv.open(path+"/home",envopenflags|xtraflags)
        global globalenv
        globalenv = self.__dbenv


        if not os.access(path+"/security",os.F_OK) : os.makedirs(path+"/security")
        if not os.access(path+"/index",os.F_OK) : os.makedirs(path+"/index")

        # Users
        self.__users=BTree("users",path+"/security/users.bdb",dbenv=self.__dbenv)                        # active database users
        self.__newuserqueue=BTree("newusers",path+"/security/newusers.bdb",dbenv=self.__dbenv)            # new users pending approval
        self.__contexts_p=BTree("contexts",path+"/security/contexts.bdb",dbenv=self.__dbenv)            # multisession persistent contexts
        self.__contexts={}            # local cache dictionary of valid contexts
        
        txn=self.newtxn()
        
        # Create an initial administrative user for the database
        if (not self.__users.has_key("root")):
            self.LOG(0,"Warning, root user recreated")
            u=User()
            u.username="root"
            if rootpw : p=hashlib.sha1(rootpw)
            else: p=hashlib.sha1(ROOTPW)
            u.password=p.hexdigest()
            u.groups=[-1]
            u.creationtime=time.strftime("%Y/%m/%d %H:%M:%S")
            u.name=('Database','','Administrator')
            self.__users.set("root",u,txn)

        # Binary data names indexed by date
        self.__bdocounter=BTree("BinNames",path+"/BinNames.bdb",dbenv=self.__dbenv,relate=0)
        
        # Defined ParamDefs
        self.__paramdefs=BTree("ParamDefs",path+"/ParamDefs.bdb",dbenv=self.__dbenv,relate=1)                        # ParamDef objects indexed by name

        # Defined RecordDefs
        self.__recorddefs=BTree("RecordDefs",path+"/RecordDefs.bdb",dbenv=self.__dbenv,relate=1)                    # RecordDef objects indexed by name
        # The actual database, keyed by recid, a positive integer unique in this DB instance
        # 2 special keys exist, the record counter is stored with key -1
        # and database information is stored with key=0
        self.__records=IntBTree("database",path+"/database.bdb",dbenv=self.__dbenv,relate=1)                        # The actual database, containing id referenced Records
        try:
            maxr=self.__records.get(-1,txn)
        except:
            self.__records.set(-1,0,txn)
            self.LOG(3,"New database created")
            
        # Indices
        if self.__importmode :
            self.__secrindex=MemBTree("secrindex",path+"/security/roindex.bdb","s",dbenv=self.__dbenv)                # index of records each user can read
            self.__recorddefindex=MemBTree("RecordDefindex",path+"/RecordDefindex.bdb","s",dbenv=self.__dbenv)        # index of records belonging to each RecordDef
        else:
            self.__secrindex=FieldBTree("secrindex",path+"/security/roindex.bdb","s",dbenv=self.__dbenv)                # index of records each user can read
            self.__recorddefindex=FieldBTree("RecordDefindex",path+"/RecordDefindex.bdb","s",dbenv=self.__dbenv)        # index of records belonging to each RecordDef
        self.__timeindex=BTree("TimeChangedindex",path+"/TimeChangedindex.bdb",dbenv=self.__dbenv)                    # key=record id, value=last time record was changed
        self.__recorddefbyrec=IntBTree("RecordDefByRec",path+"/RecordDefByRec.bdb",dbenv=self.__dbenv,relate=0)
        self.__fieldindex={}                # dictionary of FieldBTrees, 1 per ParamDef, not opened until needed
        
        # USE OF SEQUENCES DISABLED DUE TO DATABASE LOCKUPS
        #db sequence
#        self.__dbseq = self.__records.create_sequence()


        # The mirror database for storing offsite records
        self.__mirrorrecords=BTree("mirrordatabase",path+"/mirrordatabase.bdb",dbenv=self.__dbenv)

        # Workflow database, user indexed btree of lists of things to do
        # again, key -1 is used to store the wfid counter
        self.__workflow=BTree("workflow",path+"/workflow.bdb",dbenv=self.__dbenv)
        try:
            max=self.__workflow[-1]
        except:
            self.__workflow[-1]=1
            self.LOG(3,"New workflow database created")
                    
    
        # This sets up a few standard ParamDefs common to all records
        if not self.__paramdefs.has_key("owner"):
            self.__paramdefs.set_txn(txn)
            pd=ParamDef("owner","string","Record Owner","This is the user-id of the 'owner' of the record")
            self.__paramdefs["owner"]=pd
            pd=ParamDef("creator","string","Record Creator","The user-id that initially created the record")
            self.__paramdefs["creator"]=pd
            pd=ParamDef("modifyuser","string","Modified by","The user-id that last changed the record")
            self.__paramdefs["modifyuser"]=pd
            pd=ParamDef("creationtime","datetime","Creation time","The date/time the record was originally created")
            self.__paramdefs["creationtime"]=pd
            pd=ParamDef("modifytime","datetime","Modification time","The date/time the record was last modified")
            self.__paramdefs["modifytime"]=pd
            pd=ParamDef("comments","text","Record comments","Record comments")
            self.__paramdefs["comments"]=pd
            pd=ParamDef("rectype","text","Record type","Record type (RecordDef)")
            self.__paramdefs["rectype"]=pd
            pd=ParamDef("permissions","list","Permissions","Permissions")
            self.__paramdefs["permissions"]=pd
            self.__paramdefs.set_txn(None)
    
        if txn : txn.commit()
        elif not self.__importmode : DB_syncall()
        self.LOG(4,"Database initialized")



    # one of these 2 methods is mapped to self.newtxn()
    def newtxn1(self):
        return self.__dbenv.txn_begin(flags=db.DB_READ_UNCOMMITTED)
    
    
    # ian: why?
    def newtxn2(self):
        return None
    
    
    
    def LOG(self,level,message):
        """level is an integer describing the seriousness of the error:
        0 - security, security-related messages
        1 - critical, likely to cause a crash
        2 - serious, user will experience problems
        3 - minor, likely to cause minor annoyances
        4 - info, informational only
        5 - verbose, verbose logging 
        6 - debug only"""
        global LOGSTRINGS
        if (level<0 or level>6) : level=0
        try:
            o=file(self.logfile,"a")
            o.write("%s: (%s)  %s\n"%(time.strftime("%Y/%m/%d %H:%M:%S"),LOGSTRINGS[level],message))
            o.close()
            if level<4 : print "%s: (%s)  %s"%(time.strftime("%Y/%m/%d %H:%M:%S"),LOGSTRINGS[level],message)
        except:
            traceback.print_exc(file=sys.stdout)
            print("Critical error!!! Cannot write log message to '%s'\n"%self.logfile)



    def __str__(self):
        """try to print something useful"""
        return "Database %d records\n( %s )"%(int(self.__records[-1]),format_string_obj(self.__dict__,["path","logfile","lastctxclean"]))
    
    def checkpassword(self, username, password):
        s=hashlib.sha1(password)
        try:
            user=self.__users[username]
        except TypeError:
            raise AuthenticationError, AuthenticationError.__doc__
        if user.disabled : raise DisabledUserError, DisabledUserError.__doc__ % username
        return s.hexdigest()==user.password

    #@write,all
    def login(self,username="anonymous",password="",host=None,maxidle=14400):
        """Logs a given user in to the database and returns a ctxid, which can then be used for
        subsequent access. Returns ctxid, Fails on bad input with AuthenticationError"""
        ctx=None
                
        username=str(username)        
                
        # anonymous user
        if (username=="anonymous" or username=="") :
            # ian: fix anon login
            #ctx=Context(None,self,None,(),host,maxidle)
            #def __init__(self,ctxid=None,db=None,user=None,groups=None,host=None,maxidle=14400):
            ctx=Context(None,self,None,[-4],host,maxidle)
        # check password, hashed with sha-1 encryption
        else :
            try:
                user=self.__users[username]
            except TypeError:
                raise AuthenticationError, AuthenticationError.__doc__
            if user.disabled : raise DisabledUserError, DisabledUserError.__doc__ % username
            if (self.checkpassword(username, password)) : ctx=Context(None,self,username,user.groups,host,maxidle)
            else:
                self.LOG(0,"Invalid password: %s (%s)"%(username,host))
                raise AuthenticationError, "Invalid Password"
        
        # This shouldn't happen
        if ctx==None :
            self.LOG(1,"System ERROR, login(): %s (%s)"%(username,host))
            raise Exception,"System ERROR, login()"
        
        # we use sha to make a key for the context as well
        s=hashlib.sha1(username+str(host)+str(time.time()))
        ctx.ctxid=s.hexdigest()
        self.__contexts[ctx.ctxid]=ctx        # local context cache
        ctx.db=None
        txn=self.newtxn()
        self.__contexts_p.set(ctx.ctxid,ctx,txn)    # persistent context database
        ctx.db=self
        if txn : txn.commit()
        elif not self.__importmode : DB_syncall()
        self.LOG(4,"Login succeeded %s (%s)"%(username,ctx.ctxid))
        
        return ctx.ctxid
        
        
        
    #@write,private
    def deletecontext(self,ctxid,host=None):
        """Delete a context. Returns None."""

        # check we have access to this context
        ctx=self.__getcontext(ctxid,host)
        
        txn=self.newtxn()
        self.__contexts_p.set_txn(txn)
        for k in self.__contexts_p.items():
            if k[0] == ctxid:
                try: del self.__contexts[k[0]]
                except: pass
                try: del self.__contexts_p[k[0]]
                except: pass
                self.__contexts_p.set_txn(None)
        if txn: txn.commit()
        elif not self.__importmode : DB_syncall()        
    logout = deletecontext
    # ian: rpc export? probably not, for now.
    #@write
    def newbinary(self,date,name,recid,ctxid,host=None):
        """Get a storage path for a new binary object. Must have a
        recordid that references this binary, used for permissions. Returns a tuple
        with the identifier for later retrieval and the absolute path"""
        
        if name==None or str(name)=="": raise ValueError,"BDO name may not be 'None'"
        
        # ian: check for permissions because actual operations are performed.
        print 'ctxid: %s, host: %s' % (ctxid, host)
        rec=self.getrecord(recid,ctxid, host=host)
        if not rec.writable():
            raise SecurityError,"Write permission needed on referenced record."
        
        year=int(date[:4])
        mon=int(date[5:7])
        day=int(date[8:10])
    
        # figure out where this file goes in the filesystem
        key="%04d%02d%02d"%(year,mon,day)
        for i in BINARYPATH:
            if key>=i[0] and key<i[1] :
                # actual storage path
                path="%s/%04d/%02d/%02d"%(i[2],year,mon,day)
                break
        else:
            raise KeyError,"No storage specified for date %s"%key
    
        # try to make sure the directory exists
        try: os.makedirs(path)
        except: pass
    
        # Now we need a filespec within the directory
        # dictionary keyed by date, 1 directory per day
    
        if usetxn : txn=self.__dbenv.txn_begin(flags=db.DB_READ_UNCOMMITTED)
        else: txn=None
        # if exists, increase counter
        try:
            itm=self.__bdocounter.get(key,txn)
            newid=max(itm.keys())+1
            itm[newid]=(name,recid)
            self.__bdocounter.set(key,itm,txn)
        # otherwise make a new dict
        except:
            itm={0:(name,recid)}
            self.__bdocounter.set(key,itm,txn)
            newid=0
        if txn: txn.commit()
        elif not self.__importmode : DB_syncall()
    
        #todo: ian: raise exception if overwriting existing file (but this should never happen unless the file was pre-existing?)
        if os.access(path+"/%05X"%newid,os.F_OK) : self.LOG(2,"Binary data storage: overwriting existing file '%s'"%(path+"/%05X"%newid))
        
        return (key+"%05X"%newid,path+"/%05X"%newid)


    # ian: changed from cleanupcontexts to __cleanupcontexts
    #@write,private
    def __cleanupcontexts(self):
        """This should be run periodically to clean up sessions that have been idle too long. Returns None."""
        self.lastctxclean=time.time()
        txn=self.newtxn()
        self.__contexts_p.set_txn(txn)
        for k in self.__contexts_p.items():
            if not isinstance(k[0],str) : 
                self.LOG(6,"Inverted context detected "+str(k[0].ctxid))
                pass
#                del(self._Database__contexts_p[k[0]])
            
            # use the cached time if available
            try :
                c=self.__contexts[k[0]]
                k[1].time=c.time
            except: pass
            
            if k[1].time+k[1].maxidle<time.time() : 
                self.LOG(4,"Expire context (%s) %d"%(k[1].ctxid,time.time()-k[1].time))
                try: del self.__contexts[k[0]]
                except: pass
                try: del self.__contexts_p[k[0]]
                except: pass
        self.__contexts_p.set_txn(None)
        if txn: txn.commit()
        elif not self.__importmode : DB_syncall()
    # ian: host required here.
    def __getcontext(self,key,host):
        """Takes a ctxid key and returns a context (for internal use only)
        Note that both key and host must match. Returns context instance."""
        if (time.time()>self.lastctxclean+30):
            self.__cleanupcontexts()        # maybe not the perfect place to do this, but it will have to do
            pass
        try:
            ctx=self.__contexts[key]
        except:
            try:
                ctx=self.__contexts_p[key]
                ctx.db=self
                self.__contexts[key]=ctx    # cache result from database
            except:
                self.LOG(4,"Session expired %s"%key)
                raise SessionError,"Session expired"
            
        if host and host!=ctx.host :
            self.LOG(0,"Hacker alert! Attempt to spoof context (%s != %s)"%(host,ctx.host))
            raise Exception,"Bad address match, login sessions cannot be shared"
        
        ctx.time=time.time()
        # ian. 11.30.07. Add -3 to the ctx groups of all logged in users.
        # ian todo: this causes severe performance issues. need to see where __getcontext/__secrindex[-3] is used. for now, just place ctx.groups+=[-3] where appropriate.
        #print "---getcontext---"
        #if ctx.user!=None: ctx.groups.append(-3)
        
        return ctx            

    # ian: removed to help prevent DoS attack.
    # ian todo: need to check other time.sleep operations.
    
    
    #def test(self,ctxid,host=None):
    #    print "Database test."
    #    print ctxid
    #    print host
    #    return {"test":"asd"}
    
    #def sleep(self):
    #    """Sleep db for 5 seconds. Debug."""
    #    import time
    #    time.sleep(5)



    # ian: changed from isManager to checkadmin
    # ian todo: these should be moved to Context methods since user never has direct access to Context instance
    def getbinary(self,ident,ctxid,host=None):
        """Get a storage path for an existing binary object. Returns the
        object name and the absolute path"""
        
        year=int(ident[:4])
        mon =int(ident[4:6])
        day =int(ident[6:8])
        bid =int(ident[8:],16)

        key="%04d%02d%02d"%(year,mon,day)
        for i in BINARYPATH:
            if key>=i[0] and key<i[1] :
                # actual storage path
                path="%s/%04d/%02d/%02d"%(i[2],year,mon,day)
                break
        else:
            raise KeyError,"No storage specified for date %s"%key

        try:
            name,recid=self.__bdocounter[key][bid]
        except:
            raise KeyError,"Unknown identifier %s"%ident

        if self.trygetrecord(recid,ctxid,host=host) : return (name,path+"/%05X"%bid,recid)

        raise SecurityError,"Not authorized to access %s(%0d)"%(ident,recid)
    def checkcontext(self,ctxid,host=None):
        """This allows a client to test the validity of a context, and
        get basic information on the authorized user and his/her permissions"""
        a=self.__getcontext(ctxid,host)
        #if a.user==None: return(-4,-4)
        return(a.user,a.groups)
    def getindexbycontext(self,ctxid,host=None):
        """This will return the ids of all records a context has permission to access as a set. Does include groups.""" 
        ctx=self.__getcontext(ctxid,host)
        
        # todo: this needs to be moved back to __getcontext once performance issues are fixed
        # ian todo: actually, does this need to exist at all?... need to think about -3 user approach.
        # ian todo: use this to method union sets in several places.
        
        # if ctx.user!=None: ctx.groups+=[-3]
        
        # ian todo: move this to db.checkadmincontext or user.checkadmin or similar
        #if [-1] in ctx.groups or [-2] in ctx.groups:
        if self.checkreadadmin(ctx):
            return set(range(self.__records[-1]))#+1)) ###Ed: Fixed an off by one error

        ret=set(self.__secrindex[ctx.user or -4])
        if ctx.user!=None:
            ret|=set(self.__secrindex[-3] or [])

        return ret
    def getindexbyrecorddef(self,recdefname,ctxid,host=None):
        """Uses the recdefname keyed index to return all
        records belonging to a particular RecordDef as a set. Currently this
        is unsecured, but actual records cannot be retrieved, so it
        shouldn't pose a security threat."""
        return set(self.__recorddefindex[str(recdefname).lower()])

    def checkadmin(self,ctx,host=None):
        """Checks if the user has global write access. Returns 0 or 1."""
        if not isinstance(ctx,Context):
            ctx=self.__getcontext(ctx,host)
        if (-1 in ctx.groups):
            return 1
        
        return 0
    def checkreadadmin(self,ctx,host=None):
        """Checks if the user has global read access. Returns 0 or 1."""
        if not isinstance(ctx,Context):
            ctx=self.__getcontext(ctx,host)
        if (-1 in ctx.groups) or (-2 in ctx.groups):
            return 1
        
        return 0        
    def checkcreate(self,ctx,host=None):
        if not isinstance(ctx,Context):
            ctx=self.__getcontext(ctx,host)
        if 0 in ctx.groups or -1 in ctx.groups:
            return 1

        return 0
    def loginuser(self, ctxid, host=None):
      ctx=self.__getcontext(ctxid,host)
      return ctx.user
      
    
    # ian: not sure the need for this. doesn't work anyway.
    #def isMe (self, ctxid, username, host=None):
    #        ctx=self.__getcontext(ctxid,host)
    #        if (-1 in ctx.groups) or (-2 in ctx.groups) or (ctx.user==username) : return 1
    #        else: return 0

    # ian todo: define other useful ctx checks here, similar to above.    
        
                
    # ian todo: should restrict this to logged in users for security (file counts, brute force attempts)
    # ian: made ctxid required argument.
    def getbinarynames(self,ctxid,host=None):
        """Returns a list of tuples which can produce all binary object
        keys in the database. Each 2-tuple has the date key and the nubmer
        of objects under that key. A somewhat slow operation."""
        ctx=self.__getcontext(ctxid,host)
        if ctx.user==None:
            raise SecurityError,"getbinarynames not available to anonymous users"

        ret=self.__bdocounter.keys()
        ret=[(i,len(self.__bdocounter[i])) for i in ret]
        return ret        
        
    # ian todo: eventually let's move query stuff to end of file for neatness, or separate module...
    querykeywords=["find","plot","histogram","timeline","by","vs","sort","group","and","or","child","parent","cousin","><",">","<",">=","<=","=","!=",","]
    querycommands=["find","plot","histogram","timeline"]
    
    
    # ian todo: fix
    def query(self,query,ctxid,host=None,retindex=False):
        """This performs a general database query.
! - exclude protocol name
@ - protocol name
$ - parameter name
% - username
parentheses grouping not supported yet"""

        query=str(query)

        tm0=time.time()
        query2=self.querypreprocess(query,ctxid,host=host)
        if isinstance(query2,tuple) : return query2        # preprocessing returns a tuple on failure and a list on success
#        print query2
        
        # Make sure there is only one command in the query
        command=[i for i in Database.querycommands if (i in query2)]
        
        if len(command)==0 : command="find"
        elif len(command)==1 : command=command[0]
        else : return (-2,"Too many commands in query",command)
        
        # start by querying for specified record type
        # each record can only have one type, so intersection combined with
        # multiple record types would always yield nothing, so we assume
        # the intent is union, not intersection
        byrecdef=set()
        excludeset=set()
        for n,i in enumerate(query2):
            if isinstance(i,str) and i[0]=="@" and (query[n-1] not in ("by","group")):
                byrecdef|=self.getindexbyrecorddef(i[1:],ctxid)
            if isinstance(i,str) and i[0]=="!":
                excludeset|=self.getindexbyrecorddef(i[1:],ctxid)

        # We go through the query word by word and perform each operation
        byparamval=set()
        groupby=None
        n=0
        while (n<len(query2)):
            i=query2[n]
            if i=="plot" :
                if not query2[n+2] in (",","vs","vs.") : return (-1,"plot <y param> vs <x param>","")
                comops=(query2[n+1],query2[n+3])
                n+=4
                
                # We make sure that any record containing either parameter is included
                # in the results by default, and cache the values for later use in plotting
                ibvx=self.getindexdictbyvalue(comops[1][1:],None,ctxid,host=host)
                ibvy=self.getindexdictbyvalue(comops[0][1:],None,ctxid,host=host)
                
                if len(byparamval)>0 : byparamval.intersection_update(ibvx.keys())
                else: byparamval=set(ibvx.keys())
                byparamval.intersection_update(ibvy.keys())
                continue
            elif i=="histogram" :
                if not query2[n+1][0]=="$" : return (-1,"histogram <parametername>","")
                comops=(query2[n+1],)
                n+=2
                
                # We make sure that any record containing the parameter is included
                ibvh=self.getindexdictbyvalue(comops[0][1:],None,ctxid,host=host)
                if len(byparamval)>0 : byparamval.intersection_update(ibvh.keys())
                else: byparamval=set(ibvh.keys())
                continue
            elif i=="group" :
                if query2[n+1]=="by" :
                    groupby=query2[n+2]
                    n+=3
                    continue
                groupby=query2[n+1]
                n+=2
                continue
            elif i=="child" :
                chl=self.getchildren(query2[n+1],"record",recurse=20,ctxid=ctxid,host=host)
#                chl=set([i[0] for i in chl])  # children no longer suppport names 
                if len(byparamval)>0 : byparamval&=chl
                else: byparamval=chl
                n+=2
                continue
            elif i=="parent" :
                if len(byparamval)>0 : byparamval&=self.getparents(query2[n+1],"record",recurse=20,ctxid=ctxid,host=host)
                else: byparamval=self.getparents(query2[n+1],"record",recurse=20,ctxid=ctxid,host=host)
                n+=2
                continue
            elif i=="cousin" :
                if len(byparamval)>0 : byparamval&=self.getcousins(query2[n+1],"record",recurse=20,ctxid=ctxid,host=host)
                else: byparamval=self.getcousins(query2[n+1],"record",recurse=20,ctxid=ctxid,host=host)
                n+=2
                continue
            elif i[0]=="@" or i[0]=="!" or i in ("find","timeline") :
                n+=1
                continue
            elif i[0]=="%" :
                if len(byparamval)>0 : byparamval&=self.getindexbyuser(i[1:],ctxid,host=host)
                else: byparamval=self.getindexbyuser(i[1:],ctxid,host=host)
            elif i[0]=="$" :
                vrange=[None,None]
                op=query2[n+1]
                if op==">" or op==">=" : 
                    vrange[0]=query2[n+2]    # indexing mechanism doesn't support > or < yet
                    n+=2
                elif op=="<" or op=="<=" : 
                    vrange[1]=query2[n+2]    # so we treat them the same for now
                    n+=2
                elif op=="=" : 
                    vrange=query2[n+2]
                    n+=2
                elif op=="><" : 
                    if not query2[n+3] in (",","and") : raise Exception, "between X and Y (%s)"%query2[n+3]
                    vrange=[query2[n+2],query2[n+4]]
                    n+=4
                if len(byparamval)>0 : byparamval&=self.getindexbyvalue(i[1:],vrange,ctxid,host=host)
                else: byparamval=self.getindexbyvalue(i[1:],vrange,ctxid,host=host)
            elif i=="and" : pass
            
            else :
                return (-1,"Unknown word",i)

            n+=1
        
        if len(byrecdef)==0: byrecdef=byparamval
        elif len(byparamval)!=0: byrecdef&=byparamval 
        
        if len(excludeset)>0 : byrecdef-=excludeset
            
        
        # Complicated block of code to handle 'groupby' queries
        # this splits the set of located records (byrecdef) into
        # a dictionary keyed by whatever the 'groupby' request wants
        # For splits based on a parameter ($something), it will recurse
        # into the parent records up to 3 levels to try to find the
        # referenced parameter. If a protocol name is supplied, it will
        # look for a parent record of that class.
        if groupby:
            dct={}
            if groupby[0]=='$':
                gbi=self.getindexdictbyvalue(groupby[1:],None,ctxid,None)
                for i in byrecdef:
                    if gbi.has_key(i) :
                        try: dct[gbi[i]].append(i)
                        except: dct[gbi[i]]=[i]
                    else :
                        p=self.__getparentssafe(i,'record',4,ctxid)
                        for j in p:
                            if gbi.has_key(j) :
                                try: dct[gbi[j]].append(i)
                                except: dct[gbi[j]]=[i]
            elif groupby[0]=="@":
                alloftype=self.getindexbyrecorddef(groupby[1:],ctxid)
                for i in byrecdef:
                    p=self.__getparentssafe(i,'record',10,ctxid)
                    p&=alloftype
                    for j in p:
                        try: dct[j].append(i)
                        except: dct[j]=[i]
#                    else: print p,alloftype,self.getparents(i,'record',10,ctxid)
            elif groupby in ("class","protocol","recorddef") :
#                for i in byrecdef:
#                    r=self.getrecord(i,ctxid)
#                    try: dct[r.rectype].append(i)
#                    except: dct[r.rectype]=[i]
                for i in self.getrecorddefnames():
                    s=self.getindexbyrecorddef(i,ctxid,host=host)
                    ss=s&byrecdef
                    if len(ss)>0 : dct[i]=tuple(ss)
            ret=dct
        else: ret=byrecdef

        if command=="find" :
            # Simple find request, no further processing required
            if isinstance(ret, dict):
                return { 'type':'find', 'querytime':time.time()-tm0, 'data':ret}
            else:
                return { 'type':'find', 'querytime':time.time()-tm0, 'data':tuple(ret) }
        elif command=="plot" :
            # This deals with 'plot' requests, which are currently 2D scatter plots
            # It will return a sorted list of (x,y) pairs, or if a groupby request,
            # a dictionary of such lists. Note that currently output is also
            # written to plot*txt text files
            if isinstance(ret,dict) :
                multi = {}
                # this means we had a 'groupby' request    
                x0,x1,y0,y1=1e38,-1e38,1e38,-1e38
                for j in ret.keys():
                    ret2x=[]
                    ret2y=[]
                    ret2i=[]
                    for i in ret[j]:
                        ret2x.append(ibvx[i])
                        ret2y.append(ibvy[i])
                        ret2i.append(i)
                        x0=min(x0,ibvx[i])
                        y0=min(y0,ibvy[i])
                        x1=max(x1,ibvx[i])
                        y1=max(y1,ibvy[i])
                    
                    if retindex:
                        multi[j]={ 'x':ret2x,'y':ret2y,'i':ret2i }
                    else:
                        multi[j]={ 'x':ret2x,'y':ret2y }
                return {'type': 'multiplot', 'data': multi, 'xrange': (x0,x1), 'yrange': (y0,y1), 'xlabel': comops[1][1:], 'ylabel': comops[0][1:], 'groupby': groupby, 'querytime':time.time()-tm0, 'query':query2}
    
            else:
                # no 'groupby', just a single query
                x0,x1,y0,y1=1e38,-1e38,1e38,-1e38
                ret2x=[]
                ret2y=[]
                ret2i=[]
                for i in byrecdef:
                    ret2x.append(ibvx[i])
                    ret2y.append(ibvy[i])
                    ret2i.append(i)
                    x0=min(x0,ibvx[i])
                    y0=min(y0,ibvy[i])
                    x1=max(x1,ibvx[i])
                    y1=max(y1,ibvy[i])

                if retindex :
                    return {'type': 'plot', 'data': {'x':ret2x,'y':ret2y,'i':ret2i}, 'xlabel': comops[1][1:], 'ylabel': comops[0][1:], 'xrange': (x0,x1), 'yrange': (y0,y1), 'querytime':time.time()-tm0,'query':query2}
                else:
                    return {'type': 'plot', 'data': {'x':ret2x,'y':ret2y}, 'xlabel': comops[1][1:], 'ylabel': comops[0][1:], 'xrange': (x0,x1), 'yrange': (y0,y1), 'querytime':time.time()-tm0,'query':query2}
        elif command=="histogram" :
            # This deals with 'histogram' requests
            # This is much more complicated than the plot query, since a wide variety
            # of datatypes must be handled sensibly
            if len(byrecdef)==0 : return (-1,"no records found","")
            
            if not isinstance(ret,dict) :        # we make non groupby requests look like a groupby with one null category
                ret={"":ret}
                
            if 1:
                ret2={}
                tmp=[]
                pd=self.getparamdef(comops[0][1:])
                
                if (pd.vartype in ("int","longint","float","longfloat")) :
                    # get all of the values for the histogrammed field
                    # and associated numbers, (value, record #, split key)
                    for k,j in ret.items(): 
                        for i in j: tmp.append((ibvh[i],i,k))
                    tmp.sort()
                    
                    # Find limits and make a decent range for the histogram
                    m0,m1=float(tmp[0][0]),float(tmp[-1][0])
                    n=min(len(tmp)/10,50)
                    step=setdigits((m1-m0)/(n-1),2)        # round the step to 2 digits
                    m0=step*(floor(m0/step)-.5)                # round the min val to match step size
                    n=int(ceil((m1-m0)/step))+1
#                    if m0+step*n<=m1 : n+=1
                    digits=max(0,1-floor(log10(step)))
                    fmt="%%1.%df"%digits
                    
                    # now we build the actual histogram. Result is ret2 = { 'keys':keylist,'x':xvalues,1:first hist,2:2nd hist,... }
                    ret2={}
                    ret2['keys']=[]
                    for i in tmp:
                        if not i[2] in ret2['keys']: 
                            ret2['keys'].append(i[2])
                            kn=ret2['keys'].index(i[2])
                            ret2[kn]=[0]*n
                        else: kn=ret2['keys'].index(i[2])
                        ret2[kn][int(floor((i[0]-m0)/step))]+=1
                    
                    # These are the x values
                    ret2['x']=[fmt%((m0+step*(i+0.5))) for i in range(n)]
                elif (pd.vartype in ("date","datetime")) :
                    # get all of the values for the histogrammed field
                    # and associated numbers
                    # This could be rewritten MUCH more concisely
                    for k,j in ret.items(): 
                        for i in j: tmp.append((ibvh[i],i,k))
                    tmp.sort()
                    
                    # Work out x-axis values. This is complicated for dates
                    t0=int(timetosec(tmp[0][0]))
                    t1=int(timetosec(tmp[-1][0]))
                    totaltime=t1-t0        # total time span in seconds
                    
                    # now we build the actual histogram. Result is ret2 = { 'keys':keylist,'x':xvalues,1:first hist,2:2nd hist,... }
                    ret2={}
                    ret2['keys']=[]
                    ret2['x']=[]
                    
                    if totaltime<72*3600:    # by hour, less than 3 days
                        for i in range(t0,t1+3599,3600):
                            t=time.localtime(i)
                            ret2['x'].append("%04d/%02d/%02d %02d"%(t[0],t[1],t[2],t[3]))
                        n=len(ret2['x'])
                        for i in tmp:
                            if not i[2] in ret2['keys']: 
                                ret2['keys'].append(i[2])
                                kn=ret2['keys'].index(i[2])
                                ret2[kn]=[0]*n
                            else: kn=ret2['keys'].index(i[2])
                            try: ret2[kn][ret2['x'].index(i[0][:13])]+=1
                            except: print "Index error on ",i[0]
                        
                    elif totaltime<31*24*3600:    # by day, less than ~1 month
                        for i in range(t0,t1+3600*24-1,3600*24):
                            t=time.localtime(i)
                            ret2['x'].append("%04d/%02d/%02d"%(t[0],t[1],t[2]))
                        n=len(ret2['x'])
                        for i in tmp:
                            if not i[2] in ret2['keys']: 
                                ret2['keys'].append(i[2])
                                kn=ret2['keys'].index(i[2])
                                ret2[kn]=[0]*n
                            else: kn=ret2['keys'].index(i[2])
                            try: ret2[kn][ret2['x'].index(i[0][:10])]+=1
                            except: print "Index error on ",i[0]
                        
                    elif totaltime<52*7*24*3600: # by week, less than ~1 year
                        for i in range(int(t0),int(t1)+3600*24*7-1,3600*24*7):
                            t=time.localtime(i)
                            ret2['x'].append(timetoweekstr("%04d/%02d/%02d"%(t[0],t[1],t[2])))
                        n=len(ret2['x'])
                        for i in tmp:
                            if not i[2] in ret2['keys']: 
                                ret2['keys'].append(i[2])
                                kn=ret2['keys'].index(i[2])
                                ret2[kn]=[0]*n
                            else: kn=ret2['keys'].index(i[2])
                            try: ret2[kn][ret2['x'].index(timetoweekstr(i[0]))]+=1
                            except: print "Index error on ",i[0]
                            
                    elif totaltime<4*365*24*3600: # by month, less than ~4 years
                        m0=int(tmp[0][0][:4])*12 +int(tmp[0][0][5:7])-1
                        m1=int(tmp[-1][0][:4])*12+int(tmp[-1][0][5:7])-1
                        for i in range(m0,m1+1):
                            ret2['x'].append("%04d/%02d"%(i/12,(i%12)+1))
                        n=len(ret2['x'])
                        for i in tmp:
                            if not i[2] in ret2['keys']: 
                                ret2['keys'].append(i[2])
                                kn=ret2['keys'].index(i[2])
                                ret2[kn]=[0]*n
                            else: kn=ret2['keys'].index(i[2])
                            try: ret2[kn][ret2['x'].index(i[0][:7])]+=1
                            except: print "Index error on ",i[0]
                    else :    # by year
                        for i in range(int(tmp[0][0][:4]),int(tmp[-1][0][:4])+1):
                            ret2['x'].append("%04d"%i)
                        n=len(ret2['x'])
                        for i in tmp:
                            if not i[2] in ret2['keys']: 
                                ret2['keys'].append(i[2])
                                kn=ret2['keys'].index(i[2])
                                ret2[kn]=[0]*n
                            else: kn=ret2['keys'].index(i[2])
                            ret2[kn][ret2['x'].index(i[0][:4])]+=1
                    
                elif (pd.vartype in ("choice","string")):
                    # get all of the values for the histogrammed field
                    # and associated record ids. Note that for string/choice
                    # this may be a list of values rather than a single value
                    gkeys=set()        # group key list
                    vkeys=set()        # item key list
                    for k,j in ret.items(): 
                        gkeys.add(k)
                        for i in j: 
                            v=ibvh[i]
                            vkeys.add(v)
                            if isinstance(v,str) : tmp.append((v,i,k))
                            else:
                                for l in v: tmp.append((l,i,k))
                    
                    gkeys=list(gkeys)
                    gkeys.sort()
                    vkeys=list(vkeys)
                    vkeys.sort()

                    # a string field
                    tmp2=[[0]*len(vkeys) for i in range(len(gkeys))]
                    for i in tmp:
                        tmp2[gkeys.index(i[2])][vkeys.index(i[0])]+=1
                    
                    ret2={ 'keys':gkeys,'x':vkeys}
                    for i,j in enumerate(tmp2): ret2[i]=tmp2[i]
                    
#                ret2.sort()
                return {'type': 'histogram', 'data': ret2, 'xlabel': comops[0][1:], 'ylabel': "Counts", 'querytime':time.time()-tm0,'query':query2}
            
        elif command=="timeline" :
            pass
    def querypreprocess(self,query,ctxid,host=None):
        """This performs preprocessing on a database query string.
preprocessing involves remapping synonymous keywords/symbols and
identification of parameter and recorddef names, it is normally
called by query()

! - exclude protocol
@ - protocol name
$ - parameter name
% - username
parentheses not supported yet. Upon failure returns a tuple:
(code, message, bad element)"""
        
        # Words get replaced with their normalized equivalents
        replacetable={
        "less":"<","before":"<","lower":"<","under":"<","older":"<","shorter":"<",
        "greater":">","after":">","more":">","over":">","newer":">","taller":">",
        "between":"><","&":"and","|":"or","$$":"$","==":"=","equal":"=","equals":"=",
        "locate":"find","split":"group","children":"child","parents":"parent","cousins":"cousin",
        "than":None,"is":None,"where":None,"of":None}
        
        
        # parses the strings into discrete units to process (words and operators)
        e=[i for i in re.split("\s|(<=|>=|><|!=|<|>|==|=|,)",query) if i!=None and len(i)>0]

        # this little mess rejoins quoted strings into a single element
        elements=[]
        i=0
        while i<len(e) :
            if e[i][0]=='"' or e[i][0]=="'" :
                q=e[i][0]
                e[i]=e[i][1:]
                s=""
                while(i<len(e)):
                    if e[i][-1]==q :
                        s+=e[i][:-1]
                        elements.append(s)
                        i+=1
                        break
                    s+=e[i]+" "
                    i+=1
            else: 
                elements.append(e[i])
                i+=1
        
        # Now we clean up the list of terms and check for errors
        for n,e in enumerate(elements):
            # replace descriptive words with standard symbols
            if replacetable.has_key(e) : 
                elements[n]=replacetable[e]
                e=replacetable[e]
                
            if e==None or len(e)==0 : continue
            
            # if it's a keyword, we don't need to do anything else to it
            if e in Database.querykeywords : continue
            
            # this checks to see if the element is simply a number, in which case we need to keep it!
            try: elements[n]=int(e)
            except: pass
            else: continue
            
            try: elements[n]=float(e)
            except: pass
            else: continue
            
            if e[0]=="@" :
                a=self.findrecorddefname(e[1:])
                if a==None : return (-1,"Invalid protocol",e)
                elements[n]="@"+a
                continue
            if e[0]=='!':
                a=self.findrecorddefname(e[1:])
                if a==None : return (-1,"Invalid protocol",e)
                elements[n]="!"+a
                continue
            elif e[0]=="$" :
                a=self.findparamdefname(e[1:])
                if a==None : return (-1,"Invalid parameter",e)
                elements[n]="$"+a
                continue
            elif e[0]=="%" :
                a=self.findusername(e[1:],ctxid)
                if a==None : return (-1,"Username does not exist",e)
                if isinstance(a,str) :
                    elements[n]="%"+a
                    continue
                if len(a)>0 : return (-1,"Ambiguous username",e,a)
            else:
                a=self.findrecorddefname(e)
                if a!=None : 
                    elements[n]="@"+a
                    continue
                a=self.findparamdefname(e)
                if a!=None : 
                    elements[n]="$"+a
                    continue
                
                # Ok, if we don't recognize the word, we just ignore it
                # if it's in a critical spot we can raise an error later
        
        return [i for i in elements if i!=None]

#        """This will use a context to return
#        a list of records the user can access"""
#        u,g=self.checkcontext(ctxid,host)
#        
#        ret=set(self.__secrindex[u])
#        for i in g: ret|=set(self.__secrindex[i])
#        return ret
    
    def getindexbyuser(self,username,ctxid,host=None):
        """This will use the user keyed record read-access index to return
        a list of records the user can access. DOES NOT include that user's groups.
        Use getindexbycontext if you want to see all recs you can read."""

        # todo: add group support
        #u,g=self.checkcontext(ctxid,host)
        ctx=self.__getcontext(ctxid,host)
        # ian: why is this done? username should be explicit in args.
        if username==None:
            username=ctx.user
        if ctx.user!=username and not self.checkreadadmin(ctx):
            raise SecurityError,"Not authorized to get record access for %s"%username 

        return set(self.__secrindex[username])
    
    
    


    # ian: made ctxid req'd. todo: fix
    # ian: disabled for security reasons (it returns all values with no security check...)
    def getindexkeys(self,paramname,ctxid,valrange=None,host=None):
        return None
    #    """For numerical & simple string parameters, this will locate all 
    #    parameter values in the specified range.
    #    valrange may be a None (matches all), a single value, or a (min,max) tuple/list."""
    #    ind=self.__getparamindex(paramname,create=0)
    #    
    #    if valrange==None : return ind.keys()
    #    elif isinstance(valrange,tuple) or isinstance(valrange,list) : return ind.keys(valrange[0],valrange[1])
    #    elif ind.has_key(valrange): return valrange
    #    return None
        

    # ian todo: add unit support.        
    def getindexbyvalue(self,paramname,valrange,ctxid,host=None):
        """For numerical & simple string parameters, this will locate all records
        with the specified paramdef in the specified range.
        valrange may be a None (matches all), a single value, or a (min,max) tuple/list."""

        paramname=str(paramname).lower()
        
        ind=self.__getparamindex(paramname,create=0)        
        
        if valrange==None : ret=set(ind.values())
        elif isinstance(valrange,tuple) or isinstance(valrange,list) : ret=set(ind.values(valrange[0],valrange[1]))
        else: ret=set(ind[valrange] or [])
        
        #u,g=self.checkcontext(ctxid,host)
        #ctx=self.__getcontext(ctxid,host)
        if self.checkreadadmin(ctxid):
            return ret
        
        secure=set(self.getindexbycontext(ctxid,host=host))        # all records the user can access
        
        return ret & secure        # intersection of the two search results
    
    
    
    def fulltextsearch(self,q,ctxid,host=None,rectype=None,indexsearch=1,params=set(),recparams=0,builtinparam=0,ignorecase=1,subset=[],tokenize=0,single=0):
        """
        q: query
        rectype: use all of rectype as subset
        indexsearch: use indexes; otherwise interrogate each record
        params: set of params to search, can be used instead of subset
        recparams: include in-line param values
        builtinparam: include creator, creationtime, modifyuser, modifytime, permissions, and comments
        subset: provide a subset of records to search (useful)
        tokenize: boolean AND for multiple space-separated search terms
        """
                
        subset=set(subset)
        params=set(params)

        if tokenize:
            t=q.split(" ")
            rt={}
            rt[t[0]]=self.fulltextsearch(t[0],ctxid,host,rectype,indexsearch,params,recparams,builtinparam,ignorecase,subset,0,single)
            subset=set(rt[t[0]].keys())
            #print "initial search: key %s, %s results"%(t[0],len(subset))

            for i in t[1:]:
                rt[i]=self.fulltextsearch(i,ctxid,host,rectype,indexsearch,params,recparams,builtinparam,ignorecase,subset,0,single)
                subset=set(rt[i].keys())
                #print "search: key %s, %s results"%(i,subset)
            
            #print "final subset: %s"%subset
            ret={}
            for word in rt:
                for i in subset:
                    if not ret.has_key(i): ret[i]={}
                    ret[i].update(rt[word][i])
            return ret


        builtin = set(["creator","creationtime","modifyuser","modifytime","permissions","comments"])

        oq=unicode(q)
        q=oq.lower()

        if rectype and not subset:
            subset=self.getindexbyrecorddef(rectype,ctxid)

        if rectype and not params:
            pd=self.getrecorddef(rectype,ctxid)
            params=set(pd.paramsK)

        if builtinparam:
            params |= builtin
        else:
            params -= builtin

        ret={}
        urec=set(self.getindexbycontext(ctxid))
        
        #if (fast or recparams) and not ignorecase and len(subset) < 1000 and not params:
        if not indexsearch or recparams: # and not params and ... and len(subset) < 1000
            #print "rec search: %s, subset %s"%(q,len(subset))
            for recid in subset&urec:
                rec=self.getrecord(recid,ctxid)
                
                q=unicode(q)
                
                if recparams: params |= rec.getparamkeys()

                for k in params:
                    if ignorecase and q in unicode(rec[k]).lower():
                            if not ret.has_key(recid): ret[recid]={}
                            ret[recid][k]=rec[k]
                    elif oq in unicode(rec[k]):
                            if not ret.has_key(recid): ret[recid]={}
                            ret[recid][k]=rec[k]
                                    
        else:
            #if len(subset) > 1000 and ignorecase:
            #    print "Warning: case-sensitive searches limited to queries of 1000 records or less."

            #print "index search: %s, subset %s"%(q,len(subset))

            for param in params:
                #print "searching %s"%param
                #try: 
                r=self.__getparamindex(str(param).lower())

                for key in r.keys():
                    if q in str(key):
                        recs=r[key]
                        if single: recs=recs[:1]
                        for recid in recs:

                            if recid not in urec: continue
                            if not ret.has_key(recid): ret[recid]={}
                            
                            # return case sensitive values; simply setting to param key is faster but less useful
                            key2=self.getrecord(recid,ctxid)[param]
                            #print oq,key2,ignorecase
                            if not ignorecase and oq in key2:
                                ret[recid][param]=key2
                            else:
                                ret[recid][param]=key2
                                    
                #except Exception, inst:
                #    print "error in search"
                #    print inst

            # security check required
            #urec=set(self.getindexbycontext(ctxid))    
            #for key in set(ret.keys())&subset-urec:
            #    del ret[key]

        return ret
            
    
    # ian: moved host after subset
    # ian todo: unit support.
    def getindexdictbyvalue(self,paramname,valrange,ctxid,subset=None,host=None):
        """For numerical & simple string parameters, this will locate all records
        with the specified paramdef in the specified range.
        valrange may be a None (matches all), a single value, or a (min,max) tuple/list.
        This method returns a dictionary of all matching recid/value pairs
        if subset is provided, will only return values for specified recids"""

        paramname=str(paramname).lower()

        ind=self.__getparamindex(paramname,create=1)
                
        if valrange==None:
            r=dict(ind.items())
        elif isinstance(valrange,tuple) or isinstance(valrange,list):
            r=dict(ind.items(valrange[0],valrange[1]))
        else:
            r={valrange:ind[valrange]}

        # This takes the returned dictionary of value/list of recids
        # and makes a dictionary of recid/value pairs
        ret={}
        all = {}
        for i,j in r.items():
             for k in j:
                all[k]=i
        if subset:
            for i in subset:
                ret[i]=all[i]
        else:
            ret=all

        ctx=self.__getcontext(ctxid,host)
        #if (-1 in ctx.groups) or (-2 in ctx.groups) : return ret
        if self.checkreadadmin(ctx):
            return ret
        
        # getindexbycontext includes groups
        secure=self.getindexbycontext(ctxid,host=host)        # all records the user can access
        # remove any recids the user cannot access        
        for i in set(ret.keys())-secure:
            del ret[i]
                    
        return ret



    # ian: made ctxid required.
    def groupbyrecorddef(self,all,ctxid,host=None):
        """This will take a set/list of record ids and return a dictionary of ids keyed
        by their recorddef"""
        all=set(all)
        all&=set(self.getindexbycontext(ctxid,host=host))
        ret={}
        while len(all)>0:
            rid=all.pop()                            # get a random record id
            try: r=self.getrecord(rid,ctxid,host=host)    # get the record
            except:
#                db.LOG(3,"Could not group by on record %d"%rid)
                continue                        # if we can't, just skip it, pop already removed it
            ind=self.getindexbyrecorddef(r.rectype,ctxid,host=host)        # get the set of all records with this recorddef
            ret[r.rectype]=all&ind                    # intersect our list with this recdef
            all-=ret[r.rectype]                        # remove the results from our list since we have now classified them
            ret[r.rectype].add(rid)                    # add back the initial record to the set
            
        return ret



    # ian: made ctxid required
    def groupbyrecorddeffast(self,records,ctxid,host=None):
        """quick version"""
        r = {}
        for i in records:
            if not self.trygetrecord(i,ctxid): continue
            print i
            j = self.__recorddefbyrec[i]    # security checked above
            if r.has_key(j):
                r[j].append(i)
            else:
                r[j]=[i]
        return r



    # ian todo: change to ctxid req'd
    def getindexdictbyvaluefast(self,subset,param,ctxid,valrange=None,host=None):
        """quick version for records that are already in cache; e.g. table views. requires subset."""        

        v = {}
        records = self.getrecordsafe(list(subset),ctxid)
        for i in records:
            if not valrange:
                v[i.recid] = i[param]
            else:
                if i[param] > valrange[0] and i[param] < valrange[1]:
                    v[i.recid] = i[param]
        return v                
    

    
    # ian: made ctxid req'd
    def groupby(self,records,param,ctxid,host=None):
        """This will group a list of record numbers based on the value of 'param' in each record.
        Records with no defined value will be grouped under the special key None. It would be a bad idea
        to, for example, groupby 500,000 records by a float parameter with a different value for each
        record. It will do it, but you may regret asking.
        
        We really need 2 implementations here (as above), one using indices for large numbers of records and
        another using record retrieval for small numbers of records"""
        r = {}
        for i in records:
            try: j = self.getrecord(i,ctxid=ctxid)
            except: continue
            #try:
            k=j[param]
            #except: k=None
            if r.has_key(k):
                r[k].append(i)
            else:
                r[k]=[i]
        return r
    
    
    
    # ian: made ctxid req'd. moved it before recurse.
    def groupbyparentoftype(self,records,parenttype,ctxid,recurse=3,host=None):
        """This will group a list of record numbers based on the recordid of any parents of
        type 'parenttype'. within the specified recursion depth. If records have multiple parents
        of a particular type, they may be multiply classified. Note that due to large numbers of
        recursive calls, this function may be quite slow in some cases. There may also be a
        None category if the record has no appropriate parents. The default recursion level is 3."""
        
        r = {}
        for i in records:
            try: p = self.getparents(i,recurse=recurse,ctxid=ctxid,host=host)
            except: continue
            try: k=[ii for ii in p if self.getrecord(ii,ctxid).rectype==parenttype]
            except: k=[None]
            if len(k)==0 : k=[None]
            
            for j in k:
                if r.has_key(j) : r[j].append(i)
                else : r[j]=[i]
        
        return r


    
    # ian: made ctxid required argument, moved recurse after ctxid
    def countchildren(self,key,ctxid,recurse=0,host=None):
        """Unlike getchildren, this works only for 'records'. Returns a count of children
        of the specified record classified by recorddef as a dictionary. The special 'all'
        key contains the sum of all different recorddefs"""
        
        c=self.getchildren(key,"record",recurse,ctxid,host=host)
        r=self.groupbyrecorddeffast(c,ctxid,host=host)
        for k in r.keys(): r[k]=len(r[k])
        r["all"]=len(c)
        return r
    

    
    # ian todo: make ctxid mandatory, but will require alot of code changes.
    def getchildren(self,key,keytype="record",recurse=0,ctxid=None,host=None):
        """This will get the keys of the children of the referenced object
        keytype is 'record', 'recorddef', or 'paramdef'. User must have read permission
        on the parent object or an empty set will be returned. For recursive lookups
        the tree will appropriately pruned during recursion."""
        
        if (recurse<0): return set()
        if keytype=="record" : 
            trg=self.__records
            if not self.trygetrecord(key,ctxid,host=host) : return set()
        elif keytype=="recorddef" : 
            key=str(key).lower()
            trg=self.__recorddefs
            try: a=self.getrecorddef(key,ctxid)
            except: return set()
        elif keytype=="paramdef":
            key=str(key).lower()
            trg=self.__paramdefs
        else:
            raise Exception,"getchildren keytype must be 'record', 'recorddef' or 'paramdef'"

        ret=trg.children(key)
        out = []
        for x in xrange(recurse):
            for k in ret.copy():
                out.append(k)
                out.extend(trg.children(k))
        return (set(out) if out != [] else ret) 
        
#
#        if recurse==0 : return ret
#        else:
#            r2 = set()
#            for key in ret:
#                r2.update(self.getchildren(key, keytype, recurse-1, ctxid, host))
#            ret.update(r2)
#            return ret
                      

# ian
#        new = 0
#         r = {}
#         r[recurse] = set(ret)
#         while recurse:
#             r[recurse-1] = set()
#             for i in r[recurse]:
#                 if self.trygetrecord(i,ctxid,host):    r[recurse-1] |= set(trg.children(i))
#             recurse = recurse - 1
# 
#         ret = set()
#         for i in r.values():
#             ret |= i
#         return ret


        
    # ian todo: make ctxid req'd
    def getparents(self,key,keytype="record",recurse=0,ctxid=None,host=None):
        """This will get the keys of the parents of the referenced object
        keytype is 'record', 'recorddef', or 'paramdef'. User must have
        read permission on the keyed record to get a list of parents
        or an empty set will be returned."""
        if (recurse<0): return set()
        if keytype=="record" : 
            trg=self.__records
            if not self.trygetrecord(key,ctxid,host=host) : return set()
#            try: a=self.getrecord(key,ctxid)
#            except: return set()
        elif keytype=="recorddef" : 
            key=str(key).lower()
            trg=self.__recorddefs
            try: a=self.getrecorddef(key,ctxid)
            except: return set()
        elif keytype=="paramdef":
            key=str(key).lower()
            trg=self.__paramdefs
        else:
            raise Exception,"getparents keytype must be 'record', 'recorddef' or 'paramdef'"
        
        ret=trg.parents(key)
        
        if recurse==0: return set(ret)
        
        r2=[]
        for i in ret:
            r2+=self.getparents(i,keytype,recurse-1,ctxid,host=host)
        return set(ret+r2)



    # ian todo: make ctxid mandatory
    def getcousins(self,key,keytype="record",ctxid=None,host=None):
        """This will get the keys of the cousins of the referenced object
        keytype is 'record', 'recorddef', or 'paramdef'"""
        
        if keytype=="record" : 
            if not self.trygetrecord(key,ctxid,host=host) : return set()
            return set(self.__records.cousins(key))
        if keytype=="recorddef":
            return set(self.__recorddefs.cousins(str(key).lower()))
        if keytype=="paramdef":
            return set(self.__paramdefs.cousins(str(key).lower()))
        
        raise Exception,"getcousins keytype must be 'record', 'recorddef' or 'paramdef'"



    # need similar fast versions for internal use; can check later.
    # ian todo: make ctxid mandatory
    def __getparentssafe(self,key,keytype="record",recurse=0,ctxid=None,host=None):
        """Version of getparents with no security checks"""
        
        if (recurse<0): return set()
        if keytype=="record" : 
            trg=self.__records
        elif keytype=="recorddef" : 
            trg=self.__recorddefs
        elif keytype=="paramdef" : 
            trg=self.__paramdefs
        else: raise Exception,"getparents keytype must be 'record', 'recorddef' or 'paramdef'"
        
        ret=trg.parents(key)
        
        if recurse==0 : return set(ret)
        
        r2=[]
        for i in ret:
            r2+=self.__getparentssafe(i,keytype,recurse-1,ctxid,host=host)
        return set(ret+r2)
        
        
    # ian: added for consistency
    # need similar fast versions for internal use; can check later.
    # ian todo: make ctxid mandatory
    def __getchildrensafe(self,key,keytype="record",recurse=0,ctxid=None,host=None):
        if (recurse<0): return set()
        if keytype=="record": 
            trg=self.__records
        elif keytype=="recorddef": 
            key=str(key).lower()
            trg=self.__recorddefs
        elif keytype=="paramdef":
            key=str(key).lower()            
            trg=self.__paramdefs
        else:
            raise Exception,"getchildren keytype must be 'record', 'recorddef' or 'paramdef'"

        ret=trg.children(key)
        
        if recurse==0 : return set(ret)

        r2=[]
        for i in ret:
            r2+=self.__getchildrensafe(i,keytype,recurse-1,ctxid,host=host)
        return set(ret+r2)



    # ian: made ctxid required
    #@write,user
    def pclink(self,pkey,ckey,ctxid,keytype="record",host=None,txn=None):
        """Establish a parent-child relationship between two keys.
        A context is required for record links, and the user must
        have write permission on at least one of the two."""
        
        ctx=self.__getcontext(ctxid, host)
        if not self.checkcreate(ctx):
            raise SecurityError,"pclink requires record creation priveleges"
        if keytype not in ["record","recorddef","paramdef"]:
            raise Exception,"pclink keytype must be 'record', 'recorddef' or 'paramdef'"
                
        # ian: circular reference detection. 
        # is an upstream item also downstream?
        # ian todo: change to use non-secure methods if quicker; we're not returning this to user.
        #                        and needed because user may not be able to see a potential circular reference.
        if not self.__importmode:
            p=self.__getparentssafe(pkey,keytype=keytype,recurse=self.maxrecurse,ctxid=ctxid,host=host)
            c=self.__getchildrensafe(pkey,keytype=keytype,recurse=self.maxrecurse,ctxid=ctxid,host=host)
            if pkey in c or ckey in p or pkey == ckey:
                raise Exception,"Circular references are not allowed."
        
        if keytype=="record" : 
            a=self.getrecord(pkey,ctxid)
            b=self.getrecord(ckey,ctxid)
            #print a.writable(),b.writable()
            if (not a.writable()) and (not b.writable()):
                raise SecurityError,"pclink requires partial write permission"
            r=self.__records.pclink(pkey,ckey,txn=txn)
        if keytype=="recorddef":
            r=self.__recorddefs.pclink(str(pkey).lower(),str(ckey).lower(),txn=txn)
        if keytype=="paramdef":
            r=self.__paramdefs.pclink(str(pkey).lower(),str(ckey).lower(),txn=txn)

        self.LOG(0,"pclink %s: %s <-> %s by user %s"%(keytype,pkey,ckey,ctx.user))
        return r
            
    
    
    # ian: made ctxid required
    #@write,user
    def pcunlink(self,pkey,ckey,ctxid,keytype="record",host=None,txn=None):
        """Remove a parent-child relationship between two keys. Simply returns if link doesn't exist."""

        ctx=self.__getcontext(ctxid, host)
        if not self.checkcreate(ctx):
            raise SecurityError,"pcunlink requires record creation priveleges"
        if keytype not in ["record","recorddef","paramdef"]:
            raise Exception,"pclink keytype must be 'record', 'recorddef' or 'paramdef'"
                    
        if keytype=="record" : 
            a=self.getrecord(pkey,ctxid)
            b=self.getrecord(ckey,ctxid)
            if (not a.writable()) and (not b.writable()):
                raise SecurityError,"pcunlink requires partial write permission"
            r=self.__records.pcunlink(str(pkey).lower(),str(ckey).lower(),txn)
        if keytype=="recorddef":
            r=self.__recorddefs.pcunlink(str(pkey).lower(),str(ckey).lower(),txn)
        if keytype=="paramdef":
            r=self.__paramdefs.pcunlink(str(pkey).lower(),str(ckey).lower(),txn)
        
        self.LOG(0,"pcunlink %s: %s <-> %s by user %s"%(keytype,pkey,ckey,ctx.user))
        return r
        
    
    
    # ian: made ctxid required
    #@write,user
    def link(self,key1,key2,ctxid,keytype="record",host=None,txn=None):
        """Establish a 'cousin' relationship between two keys. For Records
        the context is required and the user must have read permission
        for both records."""
        # ian todo: check for circular references.

        ctx=self.__getcontext(ctxid)
        if not self.checkcreate(ctx):
            raise SecurityError,"link requires record creation priveleges"
        if keytype not in ["record","recorddef","paramdef"]:
            raise Exception,"pclink keytype must be 'record', 'recorddef' or 'paramdef'"

        if keytype=="record": 
            a=self.getrecord(key1,ctxid)
            b=self.getrecord(key2,ctxid)
            r=self.__records.link(key1,key2)
        if keytype=="recorddef":
            r=self.__recorddefs.link(str(key1).lower(),str(key2).lower(),txn)
        if keytype=="paramdef":
            r=self.__paramdefs.link(str(key1).lower(),str(key2).lower(),txn)

        self.LOG(0,"link %s: %s <-> %s by user %s"%(keytype,key1,key2,ctx.user))
        return r
    
    
    
    # ian: made ctxid req'd
    #@write,user
    def unlink(self,key1,key2,ctxid,keytype="record",host=None,txn=None):
        """Remove a 'cousin' relationship between two keys."""

        ctx=self.__getcontext(ctxid)
        if not self.checkcreate(ctx):
            raise SecurityError,"unlink requires record creation priveleges"
        if keytype not in ["record","recorddef","paramdef"]:
            raise Exception,"pclink keytype must be 'record', 'recorddef' or 'paramdef'"
                    
        if keytype=="record":
            a=self.getrecord(key1,ctxid)
            b=self.getrecord(key2,ctxid)
            r=self.__records.unlink(key1,key2)
        if keytype=="recorddef":
            r=self.__recorddefs.unlink(str(key1).lower(),str(key2).lower(),txn)
        if keytype=="paramdef":
            r=self.__paramdefs.unlink(str(key1).lower(),str(key2).lower(),txn)
        
        # ian todo: add loggging
        self.LOG(0,"unlink %s: %s <-> %s by user %s"%(keytype,key1,key2,ctx.user))
        return r
        

    #@write,admin
    def disableuser(self,username,ctxid,host=None):
        """This will disable a user so they cannot login. Note that users are NEVER deleted, so
        a complete historical record is maintained. Only an administrator can do this."""

        username=str(username)

        ctx=self.__getcontext(ctxid,host)
        #if not -1 in ctx.groups :
        if not self.checkadmin(ctx):
            raise SecurityError,"Only administrators can disable users"

        if username==ctx.user : raise SecurityError,"Even administrators cannot disable themselves"
            
        user=self.__users[username]
        user.disabled=1
        self.__users[username]=user
        self.LOG(0,"User %s disabled by %s"%(username,ctx.user))


    #@write,admin
    def approveuser(self,username,ctxid,host=None):
        """Only an administrator can do this, and the user must be in the queue for approval"""

        username=str(username)

        ctx=self.__getcontext(ctxid,host)
        #if not -1 in ctx.groups :
        if not self.checkadmin(ctx):
            raise SecurityError,"Only administrators can approve new users"
                
        if not username in self.__newuserqueue :
            raise KeyError,"User %s is not pending approval"%username
            
        if username in self.__users :
            self.__newuserqueue[username]=None
            raise KeyError,"User %s already exists, deleted pending record"%username

        # ian: create record for user.
        user=self.__newuserqueue[username]

        if user.record==None:
            try:
                userrec=self.newrecord("person",ctxid,init=1)
                userrec["username"]=username
                userrec["name_first"]=user.name[0]
                userrec["name_middle"]=user.name[1]
                userrec["name_last"]=user.name[2]
                userrec["email"]=user.email
                recid = self.putrecord(userrec,ctxid)
                user.record = recid
            except:
                raise Exception,"Unable to create record for user %s"%username

        user.validate()

        txn=self.newtxn()
        self.__users.set(username,user,txn)
        self.__newuserqueue.set(username,None,txn)
        if txn: txn.commit()
        elif not self.__importmode : DB_syncall()



    def getuserqueue(self,ctxid,host=None):
        """Returns a list of names of unapproved users"""
        return self.__newuserqueue.keys()



    #@write,admin
    def rejectuser(self,username,ctxid,host=None):
        """Remove a user from the pending new user queue - only an administrator can do this"""
        
        username=str(username)

        ctx=self.__getcontext(ctxid,host)

        # ian todo: move to general permission level check rather than hardcode -1 at each instance. several places.
        #if not -1 in ctx.groups :
        if not self.checkadmin(ctx):
            raise SecurityError,"Only administrators can approve new users"
        
        if not username in self.__newuserqueue :
            raise KeyError,"User %s is not pending approval"%username

        self.__newuserqueue[username]=None


    #@write,admin
    # ian todo: allow users to change privacy setting
    def putuser(self,user,ctxid,host=None):
        """Updates user. Takes User object (w/ validation.) Deprecated for non-administrators."""

        if not isinstance(user,User):
            try: user=User(user)
            except: raise ValueError,"User instance or dict required"
        #user=User(user.__dict__.copy())
        #user.validate()

        try:
            ouser=self.__users[user.username]
        except:
            raise KeyError,"Putuser may only be used to update existing users"
        
        ctx=self.__getcontext(ctxid,host)
        
        #if not (-1 in ctx.groups): user.groups=ouser.groups
        #if user.record!=ouser.creator and not (-1 in ctx.groups):
        #    raise SecurityError,"Only administrators may change a user's record pointer"        
        #if ctx.user!=ouser.username and not(-1 in ctx.groups) :
        
        #if -1 not in (ctx.groups):
        if not self.checkadmin(ctx):
            raise SecurityError,"Only administrators may update a user with this method"
        
        if user.password!=ouser.password:
            raise SecurityError,"Passwords may not be changed with this method"
        
        if user.creator!=ouser.creator or user.creationtime!=ouser.creationtime:
            raise SecurityError,"Creation information may not be changed"        
        
        user.validate()        
        
        txn=self.newtxn()
        self.__users.set(user.username,user,txn)
        if txn: txn.commit()
        elif not self.__importmode : DB_syncall()
        return user

    
#        ian 03.30.08: old method no longer necessary
#    
#     def putuserdict(self,username,userdict,ctxid,host=None):
#         #use to only update user information listed in allowKeys
#         denyKeys = ["username","password","creator","creationtime"]
#         allowKeys = ["firstname","lastname", "midname","email","phone","fax","cellphone","webpage","institution","department","address","city","state","zipcode","country","groups","privacy", "disabled"]
#         try:
#             ouser=self.__users[username]
#         except:
#             raise KeyError,"Putuser may only be used to update existing users"
#         
#         ctx=self.__getcontext(ctxid,host)
#         if ctx.user!=ouser.username and not(-1 in ctx.groups) :
#             raise SecurityError,"Only administrators and the actual user may update a user record"
# 
#         for thekey in denyKeys:
#             if userdict.has_key(thekey):
#                  del userdict[thekey]
#                  
#         userdict['name'] = []
#         for thekey in ['firstname', 'midname', 'lastname']:
#             if userdict.has_key(thekey):
#               userdict['name'].append(userdict[thekey])
#             else:
#                   userdict['name'].append("")
#             
#         if not (-1 in ctx.groups) :
#             userdict['groups']=ouser.groups
#             if userdict.has_key('disabled'):
#                      del userdict['disabled']
# 
#         else:
#             if isinstance(userdict['groups'], list):
#                 thegroups = [int(i) for i in userdict['groups']]
#             else:
#                 thegroups = [int(userdict['groups'])]
#             userdict['groups'] = thegroups
#                 
#         ouser.__dict__.update(userdict)
#         txn=self.newtxn()
#         self.__users.set(username,ouser,txn)
#         if txn: txn.commit()
#         elif not self.__importmode : DB_syncall()
#         return userdict
    
    
    
    #@write,user
    def setpassword(self,username,oldpassword,newpassword,ctxid,host=None):

        username=str(username)

        ctx=self.__getcontext(ctxid,host)
        user=self.getuser(username,ctxid)
        
        s=sha.new(oldpassword)
        #if not (-1 in ctx.groups) and s.hexdigest()!=user.password :
        if s.hexdigest() != user.password and not self.checkadmin(ctx):
            time.sleep(2)
            raise SecurityError,"Original password incorrect"
        
        # we disallow bad passwords here, right now we just make sure that it 
        # is at least 6 characters long
        if (len(newpassword)<6) : raise SecurityError,"Passwords must be at least 6 characters long" 
        t=sha.new(newpassword)
        user.password=t.hexdigest()
        
        txn=self.newtxn()
        self.__users.set(user.username,user,txn)
        if txn: txn.commit()
        elif not self.__importmode : DB_syncall()
        return 1
    
    
    
    # does not require ctxid
    #@write,all
    def adduser(self,user,host=None):
        """adds a new user record. However, note that this only adds the record to the
        new user queue, which must be processed by an administrator before the record
        becomes active. This system prevents problems with securely assigning passwords
        and errors with data entry. Anyone can create one of these"""

        if not isinstance(user,User):
            try: user=User(user)
            except: raise ValueError,"User instance or dict required"
        #user=User(user.__dict__.copy())
        #user.validate()        

        if user.username==None or len(user.username)<3:
            if self.__importmode:
                pass
            else:
                raise KeyError,"Attempt to add user with invalid name"
        
        if user.username in self.__users:
            if not self.__importmode:
                raise KeyError,"User with username %s already exists"%user.username
            else:
                pass

        if user.username in self.__newuserqueue:
            raise KeyError,"User with username %s already pending approval"%user.username
        
        # 40 = lenght of hex digest
        # we disallow bad passwords here, right now we just make sure that it 
        # is at least 6 characters long
        if len(user.password)<6 :
            raise SecurityError,"Passwords must be at least 6 characters long"

        s=sha.new(user.password)
        user.password=s.hexdigest()

        if not self.__importmode:
            user.creationtime=time.strftime("%Y/%m/%d %H:%M:%S")
            user.modifytime=time.strftime("%Y/%m/%d %H:%M:%S")
        
        user.validate()
        
        txn=self.newtxn()
        self.__newuserqueue.set(user.username,user,txn)
        if txn: txn.commit()
        elif not self.__importmode : DB_syncall()
        
        return user
        
        
        
    def getqueueduser(self,username,ctxid,host=None):
        """retrieves a user's information. Information may be limited to name and id if the user
        requested privacy. Administrators will get the full record"""
        
        username=str(username)
        
        ctx=self.__getcontext(ctxid,host)
        if not self.checkreadadmin(ctx):
            raise SecurityError,"Only administrators can access pending users"
            
        return self.__newuserqueue[username]
        
                
                
                
    def getuser(self,username,ctxid,host=None):
        """retrieves a user's information. Information may be limited to name and id if the user
        requested privacy. Administrators will get the full record"""
        
        username=str(username)
        
        ctx=self.__getcontext(ctxid,host)
        ret=self.__users[username]
        
        # The user him/herself or administrator can get all info
        #if (-1 in ctx.groups) or (-2 in ctx.groups) or (ctx.user==username) : return ret
        if self.checkreadadmin(ctx) or ctx.user==username: return ret

        ret.password=None        # the hashed password has limited access
        
        # if the user has requested privacy, we return only basic info
        if (ret.privacy==1 and ctx.user==None) or ret.privacy>=2 :
            ret2=User()
            ret2.username=ret.username
            ret2.privacy=ret.privacy
            # ian
            ret2.name=ret.name
            return ret2

        
        # Anonymous users cannot use this to extract email addresses
        if ctx.user==None : 
            ret.groups=None
            ret.email=None
            #ret.altemail=None
        
        return ret
        
        
        
    def getusernames(self,ctxid,host=None):
        """Not clear if this is a security risk, but anyone can get a list of usernames
            This is likely needed for inter-database communications"""
        return self.__users.keys()



    # ian todo: update. the find* functions need to be fast and good at fulltext searches for autocomplete functionality.
    def findusername(self,name,ctxid,host=None):
        """This will look for a username matching the provided name in a loose way"""

        name=str(name)
        if self.__users.has_key(name) : return name
        
        possible=filter(lambda x: name in x,self.__users.keys())
        if len(possible)==1 : return possible[0]
        if len(possible)>1 : return possible
        
        possible=[]
        for i in self.getusernames(ctxid,host=host):
            try: u=self.getuser(name,ctxid,host=host)
            except: continue
            
            for j in u.__dict__:
                if isinstance(j,str) and name in j :
                    possible.append(i)
                    break

        if len(possible)==1 : return possible[0]
        if len(possible)>1 : return possible
                    
        return None
    
    
    
    def getworkflow(self,ctxid,host=None):
        """This will return an (ordered) list of workflow objects for the given context (user).
        it is an exceptionally bad idea to change a WorkFlow object's wfid."""
        
        ctx=self.__getcontext(ctxid,host)
        if ctx.user==None: raise SecurityError,"Anonymous users have no workflow"
        
        try:
            return self.__workflow[ctx.user]
        except:
            return []



    def getworkflowitem(self,wfid,ctxid,host=None):
        """Return a workflow from wfid."""
        ret = None
        wflist = self.getworkflow(ctxid)
        if len(wflist) == 0:
             return None
        else:
             for thewf in wflist:
                 if thewf.wfid == wfid:
                     ret = thewf.items_dict()
        return ret
        
        
        
    def newworkflow(self, vals, host=None):
        """Return an initialized workflow instance."""
        return WorkFlow(vals)
        
        
        
    #@write,user
    def addworkflowitem(self,work,ctxid,host=None):
        """This appends a new workflow object to the user's list. wfid will be assigned by this function and returned"""
        
        ctx=self.__getcontext(ctxid,host)

        if ctx.user==None:
            raise SecurityError,"Anonymous users have no workflow"

        if not isinstance(work,WorkFlow):
            try: work=WorkFlow(work)
            except: raise ValueError,"WorkFlow instance or dict required"
        #work=WorkFlow(work.__dict__.copy())
        work.validate()

        #if not isinstance(work,WorkFlow):
        #    raise TypeError,"Only WorkFlow objects can be added to a user's workflow"
        
        txn=self.newtxn()
        self.__workflow.set_txn(txn)
        work.wfid=self.__workflow[-1]
        self.__workflow[-1]=work.wfid+1

        if self.__workflow.has_key(ctx.user) :
                wf=self.__workflow[ctx.user]
        else:
            wf = []
            
        wf.append(work)
        self.__workflow[ctx.user]=wf
        self.__workflow.set_txn(None)
        if txn: txn.commit()
        elif not self.__importmode : DB_syncall()
        return work.wfid
    
    
    
    #@write,user
    def delworkflowitem(self,wfid,ctxid,host=None):
        """This will remove a single workflow object based on wfid"""
        
        ctx=self.__getcontext(ctxid,host)
        if ctx.user==None: raise SecurityError,"Anonymous users have no workflow"
        
        wf=self.__workflow[ctx.user]
        for i,w in enumerate(wf):
            if w.wfid==wfid :
                del wf[i]
                break
        else: raise KeyError,"Unknown workflow id"
        
        txn=self.newtxn()
        self.__workflow.set(ctx.user,wf,txn)
        if txn: txn.commit()
        elif not self.__importmode : DB_syncall()
        
        
        
    #@write,user
    def setworkflow(self,wflist,ctxid,host=None):
        """This allows an authorized user to directly modify or clear his/her workflow. Note that
        the external application should NEVER modify the wfid of the individual WorkFlow records.
        Any wfid's that are None will be assigned new values in this call."""
        
        ctx=self.__getcontext(ctxid,host)
        if ctx.user==None: raise SecurityError,"Anonymous users have no workflow"
        
        if wflist==None : wflist=[]
        wflist=list(wflist)                # this will (properly) raise an exception if wflist cannot be converted to a list
        
        txn=self.newtxn()
        for w in wflist:
            
            if not self.__importmode:
                #w=WorkFlow(w.__dict__.copy())
                w.validate()
            
            if not isinstance(w,WorkFlow): 
                txn.abort()
                raise TypeError,"Only WorkFlow objects may be in the user's workflow"
            if w.wfid==None: 
                w.wfid=self.__workflow[-1]
                self.__workflow.set(-1,w.wfid+1,txn)
        
        self.__workflow.set(ctx.user,wflist,txn)
        if txn: txn.commit()
        elif not self.__importmode : DB_syncall()
    
    
    
    def getvartypenames(self, host=None):
        """This returns a list of all valid variable types in the database. This is currently a
        fixed list"""
        return valid_vartypes.keys()



    def getvartype(self, thekey, host=None):
        """This returns a list of all valid variable types in the database. This is currently a
        fixed list"""
        return valid_vartypes[thekey][1]



    def getpropertynames(self, host=None):
        """This returns a list of all valid property types in the database. This is currently a
        fixed list"""
        return valid_properties.keys()
            
            
            
    def getpropertyunits(self,propname, host=None):
        """Returns a list of known units for a particular property"""
        return valid_properties[propname][1].keys()
            
            
            
    # ian: moved host after parent        
    #@write, user
    def addparamdef(self,paramdef,ctxid,parent=None,host=None):
        """adds a new ParamDef object, group 0 permission is required
        a p->c relationship will be added if parent is specified"""

        if not isinstance(paramdef,ParamDef):
            try: paramdef=ParamDef(paramdef)
            except: raise ValueError,"ParamDef instance or dict required"
        #paramdef=ParamDef(paramdef.__dict__.copy())
        # paramdef.validate()
    
        #if not isinstance(paramdef,ParamDef):    raise TypeError,"addparamdef requires a ParamDef object"
        
        ctx=self.__getcontext(ctxid,host)
        #if (not 0 in ctx.groups) and (not -1 in ctx.groups):
        if not self.checkcreate(ctx):
            raise SecurityError,"No permission to create new paramdefs (need record creation permission)"

        paramdef.name=str(paramdef.name).lower()
        
        if self.__paramdefs.has_key(paramdef.name) : 
            # Root is permitted to force changes in parameters, though they are supposed to be static
            # This permits correcting typos, etc., but should not be used routinely
            if not self.checkadmin(ctx): raise KeyError,"paramdef %s already exists"%paramdef.name
        else :
            # force these values
            paramdef.creator=ctx.user
            paramdef.creationtime=time.strftime("%Y/%m/%d %H:%M:%S")
        
        if isinstance(paramdef.choices,list) or isinstance(paramdef.choices,tuple):
            paramdef.choices=tuple([str(i).title() for i in paramdef.choices])

        if not self.__importmode:
            #paramdef=ParamDef(paramdef.__dict__.copy())
            paramdef.validate()
        
        # this actually stores in the database
        txn=self.newtxn()
        self.__paramdefs.set(paramdef.name,paramdef,txn)
        if (parent): self.pclink(parent,paramdef.name,"paramdef",txn=txn)
        if txn: txn.commit()
        elif not self.__importmode : DB_syncall()
        
        
    # ian: made ctxid required argument.
    #@write,user
    def addparamchoice(self,paramdefname,choice,ctxid,host=None):
        """This will add a new choice to records of vartype=string. This is
        the only modification permitted to a ParamDef record after creation"""

        paramdefname=str(paramdefname).lower()
        
        # ian: change to only allow logged in users to add param choices. silent return on failure.
        ctx=self.__getcontext(ctxid,host)
        if not self.checkcreate(ctx):
            return

        d=self.__paramdefs[paramdefname]
        if d.vartype!="string":
            raise SecurityError,"choices may only be modified for 'string' parameters"
        
        d.choices=d.choices+(str(choice).title(),)
        txn=self.newtxn()
        self.__paramdefs.set(paramdefname,d,txn)
        if txn: txn.commit()
        elif not self.__importmode : DB_syncall()




    def getparamdef(self,key,ctxid=None, host=None):
        """gets an existing ParamDef object, anyone can get any field definition
    
    NOTE: ctxid is unused"""
        #debug(__file__, ',', 'paramdefname = ', paramdefname)
        key=str(key).lower()
        try:
            return self.__paramdefs[key]
        except:
            raise KeyError,"Unknown ParamDef: %s"%key
        
        
    def getparamdefnames(self,host=None):
        """Returns a list of all ParamDef names"""
        return self.__paramdefs.keys()
    
    
    
    def findparamdefname(self,name,host=None):
        """Find a paramdef similar to the passed 'name'. Returns the actual ParamDef, 
or None if no match is found."""
        name=str(name).lower()
        if self.__paramdefs.has_key(name) : return name
        if name[-1]=="s" :
            if self.__paramdefs.has_key(name[:-1]) : return name[:-1]
            if name[-2]=="e" and self.__paramdefs.has_key(name[:-2]): return name[:-2]
        if name[-3:]=="ing" and self.__paramdefs.has_key(name[:-3]): return name[:-3]
        return None
    
    
    
    def getparamdefs(self,recs,ctxid=None,host=None):
        """Returns a list of ParamDef records.
        recs may be a single record, a list of records, or a list
        of paramdef names. This routine will 
        retrieve the parameter definitions for all parameters with
        defined values in recs. The results are returned as a dictionary.
        It is much more efficient to use this on a list of records than to
        call it individually for each of a set of records."""

        ret={}
        if not hasattr(recs,"__iter__"): recs=(recs,)

        for i in recs:
            if isinstance(i,str):
                if not ret.has_key(i):
                    ret[i]=self.getparamdef(i)
            elif isinstance(i,int):
                j=self.getrecord(i,ctxid,host)
                for k in j.getparamkeys():
                    if not ret.has_key(k):
                        ret[k]=self.getparamdef(k)                
            elif isinstance(i,Record):
                for k in i.getparamkeys():
                    if not ret.has_key(k):
                        ret[k]=self.getparamdef(k)
            else:
                continue
                    
#         if isinstance(recs[0],str) :
#             for p in recs:
#                 if ret.has_key(p) or p in ("comments","creationtime","permissions","creator","owner") : continue
#                 try: 
#                     ret[p]=self.__paramdefs[p]
#                 except: 
#                     raise KeyError,"Request for unknown ParamDef %s"%p #self.LOG(2,"Request for unknown ParamDef %s"%(p))
#         else:    
#             for r in recs:
#                 for p in r.keys():
#                     if ret.has_key(p) or p in ("comments","creationtime","permissions","creator","owner") : continue
#                     try:
#                         ret[p]=self.__paramdefs[p]
#                     except:
#                         raise KeyError,"Request for unknown paramdef %s in %s"%(p,r.rectype) #self.LOG(2,"Request for unknown ParamDef %s in %s"%(p,r.rectype))

        return ret
        
        
    # ian: moved host after parent
    #@write,user
    def addrecorddef(self,recdef,ctxid,parent=None,host=None):
        """adds a new RecordDef object. The user must be an administrator or a member of group 0"""

        if not isinstance(recdef,RecordDef):
            try: recdef=RecordDef(recdef)
            except: raise ValueError,"RecordDef instance or dict required"
        # recdef=RecordDef(recdef.__dict__.copy())
        # paramdef.validate()

        ctx=self.__getcontext(ctxid,host)

        #if (not 0 in ctx.groups) and (not -1 in ctx.groups):
        if not self.checkcreate(ctx):
            raise SecurityError,"No permission to create new RecordDefs"
            
        if self.__recorddefs.has_key(str(recdef.name).lower()):
            raise KeyError,"RecordDef %s already exists"%str(recdef.name).lower()

        recdef.findparams()
        pdn=self.getparamdefnames()
        for i in recdef.params:
            if i not in pdn: raise KeyError,"No such parameter %s"%i

        # force these values
        if (recdef.owner==None) : recdef.owner=ctx.user
        recdef.name=str(recdef.name).lower()
        recdef.creator=ctx.user
        recdef.creationtime=time.strftime("%Y/%m/%d %H:%M:%S")

        if not self.__importmode:
            #recdef=RecordDef(recdef.__dict__.copy())
            recdef.validate()
        
        # commit
        txn=self.newtxn()
        self.__recorddefs.set(recdef.name,recdef,txn)
        if (parent): self.pclink(parent,recdef.name,"recorddef",txn=txn)
        if txn: txn.commit()
        elif not self.__importmode : DB_syncall()
        return recdef.name



    #@write,user partial
    def putrecorddef(self,recdef,ctxid,host=None):
        """This modifies an existing RecordDef. The mainview should
        never be changed once used, since this will change the meaning of
        data already in the database, but sometimes changes of appearance
        are necessary, so this method is available."""

        if not isinstance(recdef,RecordDef):
            try: recdef=RecordDef(recdef)
            except: raise ValueError,"RecordDef instance or dict required"
        # recdef=RecordDef(recdef.__dict__.copy())
        # paramdef.validate()
        
        ctx=self.__getcontext(ctxid,host)
        # name doesnt have to be forced str/lower because it checks for existing recdef
        rd=self.__recorddefs[recdef.name]

        #if (not -1 in ctx.groups) and (ctx.user!=rd.owner) : 
        if ctx.user!=rd.owner and not self.checkadmin(ctx):
            raise SecurityError,"Only the owner or administrator can modify RecordDefs"

        if recdef.mainview != rd.mainview and not self.checkadmin(ctx):
            raise SecurityError,"Only the administrator can modify the mainview of a RecordDef"

        recdef.findparams()
        pdn=self.getparamdefnames()
        for i in recdef.params:
            if i not in pdn: raise KeyError,"No such parameter %s"%i

        # reset
        recdef.creator=rd.creator
        recdef.creationtime=rd.creationtime
        #recdef.mainview=rd.mainview    #temp. change to allow mainview changes

        if not self.__importmode:
            recdef=RecordDef(recdef.__dict__.copy())
            recdef.validate()

        # commit
        txn=self.newtxn()
        self.__recorddefs.set(recdef.name,recdef,txn)
        if txn: txn.commit()
        elif not self.__importmode : DB_syncall()
        
        
    # ian todo: move host to end
    def getrecorddef(self,rectypename,ctxid,host=None,recid=None):
        """Retrieves a RecordDef object. This will fail if the RecordDef is
        private, unless the user is an owner or  in the context of a recid the
        user has permission to access"""
        
        rectypename=str(rectypename).lower()
        if not self.__recorddefs.has_key(rectypename) : raise KeyError,"No such RecordDef %s"%rectypename
        
        ret=self.__recorddefs[rectypename]    # get the record
        
        if not ret.private : return ret
        
        # if the RecordDef isn't private or if the owner is asking, just return it now
        ctx=self.__getcontext(ctxid,host)
        # ian: why would ret.owner be in ctx.groups?
        if (ret.private and (ret.owner==ctx.user or ret.owner in ctx.groups)) : return ret

        # ok, now we need to do a little more work. 
        if recid==None: raise SecurityError,"User doesn't have permission to access private RecordDef '%s'"%rectypename
        
        rec=self.getrecord(recid)        # try to get the record, may (and should sometimes) raise an exception

        if rec.rectype!=rectypename: raise SecurityError,"Record %d doesn't belong to RecordDef %s"%(recid,rectypename)

        # success, the user has permission
        return ret
    
    
    
    def getrecorddefnames(self,host=None):
        """This will retrieve a list of all existing RecordDef names, 
        even those the user cannot access the contents of"""
        return self.__recorddefs.keys()



    def findrecorddefname(self,name,host=None):
        """Find a recorddef similar to the passed 'name'. Returns the actual RecordDef, 
        or None if no match is found."""

        name=str(name).lower()
        
        if self.__recorddefs.has_key(name) : return name
        if name[-1]=="s" :
            if self.__recorddefs.has_key(name[:-1]) : return name[:-1]
            if name[-2]=="e" and self.__recorddefs.has_key(name[:-2]): return name[:-2]
        if name[-3:]=="ing" and self.__recorddefs.has_key(name[:-3]): return name[:-3]
        return None
    
    
    # ian: deprecated
    #def commitindices(self):
    #    self.__commitindices()
        
        
        
    #@write,private
    def __commitindices(self):
        """This is used in 'importmode' after many records have been imported using
        memory indices to dump the indices to the persistent files"""
        
        if not self.__importmode:
            print "commitindices may only be used in importmode"
            sys.exit(1)
        
        for k,v in self.__fieldindex.items():
            if k == 'parent':
                  continue
            print "commit index %s (%d)\t%d\t%d"%(k,len(v),len(BTree.alltrees),len(FieldBTree.alltrees))
            i=FieldBTree(v.bdbname,v.bdbfile,v.keytype,v.bdbenv)
            txn=self.newtxn()
            i.set_txn(txn)
            for k2,v2 in v.items():
                i.addrefs(k2,v2)
            i.set_txn(None)
            if txn: txn.commit()
            i=None

        print "commit security"
        si=FieldBTree("secrindex",self.path+"/security/roindex.bdb","s",dbenv=self.__dbenv)
        txn=self.newtxn()
        si.set_txn(txn)
        for k,v in self.__secrindex.items():
            si.addrefs(k,v)
        si.set_txn(None)
        if txn: txn.commit()
        
        print "commit recorddefs"
        rdi=FieldBTree("RecordDefindex",self.path+"/RecordDefindex.bdb","s",dbenv=self.__dbenv)
        txn=self.newtxn()
        rdi.set_txn(txn)
        for k,v in self.__recorddefindex.items():
            rdi.addrefs(k,v)
        rdi.set_txn(None)
        if txn: 
            txn.commit()
            self.LOG(4, "Index merge complete. Checkpointing")
            self.__dbenv.txn_checkpoint()
            self.LOG(4,"Checkpointing complete")
        else:
            print "Index merge complete Syncing"
            DB_syncall()

        DB_cleanup()
        self.__dbenv.close()
        if DEBUG>2: print >>sys.stderr, '__dbenv.close() successful'
        sys.exit(0)
        
        
        
    def __getparamindex(self,paramname,create=1):
        """Internal function to open the parameter indices at need.
        Later this may implement some sort of caching mechanism.
        If create is not set and index doesn't exist, raises
        KeyError. Returns "link" or "child" for this type of indexing"""
        try:
            ret=self.__fieldindex[paramname]        # Try to get the index for this key
        except:
            # index not open yet, open/create it
            try:
                f=self.__paramdefs[paramname]        # Look up the definition of this field
            except:
                # Undefined field, we can't create it, since we don't know the type
                raise FieldError,"No such field %s defined"%paramname
            
            tp=valid_vartypes[f.vartype][0]
            if not tp :
#                print "unindexable vartype ",f.vartype
                ret = None
                return ret
            if len(tp)>1 : return tp
            
            if not create and not os.access("%s/index/%s.bdb"%(self.path,paramname),os.F_OK): raise KeyError,"No index for %s"%paramname
            
            # create/open index
            if self.__importmode:
                self.__fieldindex[paramname]=MemBTree(paramname,"%s/index/%s.bdb"%(self.path,paramname),tp,self.__dbenv)
            else:
                self.__fieldindex[paramname]=FieldBTree(paramname,"%s/index/%s.bdb"%(self.path,paramname),tp,self.__dbenv)
            ret=self.__fieldindex[paramname]
        
        return ret
    
    
    
    #@write,private
    def __reindex(self,key,oldval,newval,recid,txn=None):
        """This function reindexes a single key/value pair
        This includes creating any missing indices if necessary"""

        if (key=="comments" or key=="permissions") : return        # comments & permissions are not currently indexed 
        if (oldval==newval) : return        # no change, no indexing required
        
        # Painful, but if this is a 'text' field, we index the words not the value
        # ie - full text indexing
        if isinstance(oldval,str) or isinstance(newval,str) :
            try:
                f=self.__paramdefs[key]        # Look up the definition of this field
            except:
                raise FieldError,"No such field %s defined"%key
            if f.vartype=="text" :
                self.__reindextext(key,oldval,newval,recid)
                return
        
        # whew, not full text, get the index for this key
        ind=self.__getparamindex(key)
#        print ind 
        if ind == None:
            return
        
        if ind=="child" or ind=="link" :
            # make oldval and newval into sets
            try: oldval=set((int(oldval),))
            except: 
                if oldval==None : oldval=set()
                else: oldval=set(oldval)
            try: newval=set((int(newval),))
            except: 
                if newval==None : newval=set()
                else : newval=set(newval)
                
            i=oldval&newval        # intersection
            oldval-=i
            newval-=i
            # now we know that oldval and newval are unique
            if (not self.__importmode) : 
               if ind=="child" :
                for i in oldval: self.__records.pcunlink(recid,i,txn=txn)
                for i in newval: self.__records.pclink(recid,i,txn=txn)
                return
            
               if ind=="link" :
                for i in oldval: self.__records.unlink(recid,i,txn=txn)
                for i in newval: self.__records.link(recid,i,txn=txn)
                return
            else:
                return
        # remove the old ref and add the new one
        if oldval!=None : ind.removeref(oldval,recid,txn=txn)
        if newval!=None : ind.addref(newval,recid,txn=txn)
        #print ind.items()



    #@write,private
    def __reindextext(self,key,oldval,newval,recid,txn=None):
        """This function reindexes a single key/value pair
        where the values are text strings designed to be searched
        by 'word' """

        unindexed_words=["in","of","for","this","the","at","to","from","at","for","and","it","or"]        # need to expand this
        
        ind=self.__getparamindex(key)
        if ind == None:
            print 'No parameter index for ',key
            return
        
        # remove the old ref and add the new one
        if oldval!=None:
            for s in oldval.split():
                t=s.lower()
                if len(s)<2 or t in unindexed_words: pass
                ind.removeref(t,recid,txn=txn)
    
        if newval!=None:
            for s in newval.split():
                t=s.lower()
                if len(s)<2 or t in unindexed_words: pass
                ind.addref(t,recid,txn=txn)
        
        #print ind.items()



    #@write,private
    def __reindexsec(self,oldlist,newlist,recid,txn=None):
        """This updates the security (read-only) index
        takes two lists of userid/groups (may be None)"""
#        print "reindexing security.."
#        print oldlist
#        print newlist
        o=set(oldlist)
        n=set(newlist)
        
        uo=o-n    # unique elements in the 'old' list
        un=n-o    # unique elements in the 'new' list
#        print o,n,uo,un

        # anything in both old and new should be ok,
        # So, we remove the index entries for all of the elements in 'old', but not 'new'
        for i in uo:
#            print i," ",len(self.__secrindex[i]),self.__secrindex.testref(i,recid)
            self.__secrindex.removeref(i,recid,txn=txn)
#        print "now un"
        # then we add the index entries for all of the elements in 'new', but not 'old'
        for i in un:
            self.__secrindex.addref(i,recid,txn=txn)



    def putrecordvalue(self,recid,param,value,ctxid,host=None):
        rec=self.getrecord(recid,ctxid,host=host)
        rec[param]=value
        self.putrecord(rec,ctxid,host=host)
        return self.getrecord(recid,ctxid,host=host)[param]
        #return recid
        #return self.renderview(recid,viewdef="$$%s"%param,ctxid=ctxid,host=host)

        
    def putrecordvalues(self,recid,values,ctxid,host=None):
        rec=self.getrecord(recid,ctxid,host=host)
        for k,v in values.items():
            if v==None:
                del rec[k]
            else:
                rec[k]=v
        self.putrecord(rec,ctxid,host=host)
        return self.getrecord(recid,ctxid,host=host)        

        
    def putrecordsvalues(self,d,ctxid,host=None):
        ret={}
        for k,v in d.items():
            ret[k]=self.putrecordvalues(k,v,ctxid,host=host)
        return ret
        
        
    def addcomment(self,recid,comment,ctxid):
        rec=self.getrecord(recid,ctxid)
        rec.addcomment(comment)
        self.putrecord(rec,ctxid)
        return self.getrecord(recid,ctxid)["comments"]
        
    def getuserdisplayname(self,username,ctxid,lnf=0,host=None):
        """Return the full name of a user from the user record."""

        if hasattr(username,"__iter__"):
            ret={}
            for i in username:
                ret[i]=self.getuserdisplayname(i,ctxid,lnf,host=host)
            return ret

        try:
            u=self.getrecord(self.getuser(username,ctxid).record,ctxid,host=host)
        except:
            return "(%s)"%username
                        
        if u["name_first"] and u["name_middle"] and u["name_last"]:
            if lnf:    uname="%s, %s %s"%(u["name_last"], u["name_middle"], u["name_last"])
            else:    uname="%s %s %s"%(u["name_first"],u["name_middle"],u["name_last"])
    
        elif u["name_first"] and u["name_last"]:
            if lnf: uname="%s, %s"%(u["name_last"],u["name_first"])
            else: uname="%s %s"%(u["name_first"],u["name_last"])
        
        elif u["name_last"]:
            uname=u["name_last"]
        
        elif u["name_first"]:
            uname=u["name_first"]
            
        else:
            uname=username

        return uname

# ian/ed: interesting idea...
#     def proxy(self, __class_, __methodname_, __id_, __ctxid_, *args, **kwargs):
#         cls = globals()(__class_)
#         method = getattr(cls, __methodname_)
#         object = self.getrecord(0, __ctxid_)
#         return method(object, *args, **kwargs)
        

    # ian: moved host to end
    #@write,user
    def putrecord(self,record,ctxid,parents=[],children=[],host=None):
        """The record has everything we need to commit the data. However, to 
        update the indices, we need the original record as well. This also provides
        an opportunity for double-checking security vs. the original. If the 
        record is new, recid should be set to None. recid is returned upon success. 
        parents and children arguments are conveniences to link new records at time of creation."""
        
        ctx=self.__getcontext(ctxid,host)
        
        if not isinstance(record,Record):
            try: record=Record(record,ctx)
            except: raise ValueError,"Record instance or dict required"
        
        record.setContext(ctx)
        record.validate()
        
        ######
        # This except block is where new records are created
        ######
        try:
            orig=self.__records[record.recid]        # get the unmodified record
        
        except:
            # Record must not exist, lets create it
            # p=record.setContext(ctx)

            # set recid
            #    txn=self.__dbenv.txn_begin(flags=db.DB_READ_UNCOMMITTED)
            print "got recid %s" % record.recid

            txn=self.newtxn()
            record.recid=self.__records.get(-1,txn)

            if not self.__importmode:
                df=file("/tmp/dbbug3","a")
                print >>df, "%s\n%s\n"%(str(ctx.__dict__),str(record))
                df.close()
        
            print 'CTX:', ctx
            if not self.checkcreate(ctx):
                txn and txn.abort()
                raise SecurityError,"No permission to create records"

            record["modifytime"]=record["creationtime"]
            if not self.__importmode:
                record["modifyuser"]=ctx.user
                
            self.__records.set(record.recid,record,txn)        # This actually stores the record in the database
            self.__recorddefbyrec.set(record.recid,record.rectype,txn)
            
            # index params
            for k,v in record.items():
                if k != 'recid':
                    self.__reindex(k,None,v,record.recid,txn)

            self.__reindexsec([],reduce(operator.concat,record["permissions"]),record.recid, txn=txn)        # index security
            self.__recorddefindex.addref(record.rectype,record.recid,txn)            # index recorddef
            self.__timeindex.set(record.recid,record["creationtime"],txn)
            
            self.__records.set(-1,record.recid+1,txn)            # Update the recid counter, TODO: do the update more safely/exclusive access
                                    
            #print "putrec->\n",record.__dict__
            #print "txn: %s" % txn
            if txn: txn.commit()
            
            elif not self.__importmode : DB_syncall()
            
            # ian todo: restore this
            #try:
            #    self.__validaterecordaddchoices(record,ctxid)
            #except:
            #    print "Unable to add choices to paramdefs."
            
            # ian
            if type(parents)==int: parents=[parents]
            for i in parents:
                self.pclink(i,record.recid,ctxid)

            if type(children)==int: children=[children]
            for i in children:
                self.pclink(record.recid,i,ctxid)
                        
            return record.recid
        
        ######
        # If we got here, we are updating an existing record
        ######

        #import g
        #g.orig = orig

        orig.setContext(ctx)                # security check on the original record
        record.setContext(ctx)            # security double-check on the record to be processed. This is required for DBProxy use.
        record.validate()
        
        record.setoparams(orig.items_dict())
        cp = record.changedparams()

        print "Changed params: %s"%cp
        
        if len(cp) == 0: 
            self.LOG(5,"update %d with no changes"%record.recid)
            return "No changes made"


        txn=self.newtxn()

        # Now update the indices
        for f in cp:
            # reindex will accept None as oldval or newval
            try:    oldval=orig[f]
            except: oldval=None
            
            try:    newval=record[f]
            except: newval=None

            self.__reindex(f,oldval,newval,record.recid,txn)
            
            if f not in ["comments","modifytime","modifyuser"]:
                #orig.addcomment(u"LOG: %s updated. was: "%f + unicode(oldval))
                orig._Record__comments.append((ctx.user,time.strftime("%Y/%m/%d %H:%M:%S"),(f,newval,oldval)))
            orig[f]=record[f]
            
                
        self.__reindexsec(reduce(operator.concat,orig["permissions"]),
            reduce(operator.concat,record["permissions"]),record.recid,txn)        # index security
        
        # Updates last time changed index
        if (not self.__importmode): 
            orig["modifytime"]=time.strftime("%Y/%m/%d %H:%M:%S")
            orig["modifyuser"]=ctx.user
            self.__timeindex.set(record.recid,'modifytime',txn)
        
        # any new comments are appended to the 'orig' record
        # attempts to modify the comment list bypassing the security
        # in the record class will result in a bunch of new comments
        # being added to the record.
        for i in record["comments"]:
            if not i in orig["comments"]: orig["comments"]=i[2]
        
        self.__records.set(record.recid,orig,txn)            # This actually stores the record in the database
        self.__recorddefbyrec.set(record.recid,record.rectype,txn)
        if txn: txn.commit()
        elif not self.__importmode : DB_syncall()

        return record.recid
        
        
        
    # ian: moved host to end    
    def newrecord(self,rectype,ctxid=None,init=0,inheritperms=None,host=None):
        """This will create an empty record and (optionally) initialize it for a given RecordDef (which must
        already exist)."""
        ctx=self.__getcontext(ctxid,host)
        rec=Record()
        rec.setContext(ctx)
        
        # try to get the RecordDef entry, this still may fail even if it exists, if the
        # RecordDef is private and the context doesn't permit access
        t=self.getrecorddef(rectype,ctxid,host=host)

        rec.recid=None
        rec.rectype=rectype                        # if we found it, go ahead and set up
                
        if init:
            for k,v in t.params.items():
                rec[k]=v                        # hmm, in the new scheme, perhaps this should just be a deep copy

        # ian
        if inheritperms!=None:
            if self.trygetrecord(inheritperms,ctxid):
                prec=self.getrecord(inheritperms,ctxid)
                n=[]
                for i in range(0,len(prec["permissions"])):
                    n.append(prec["permissions"][i]+rec["permissions"][i])
                rec["permissions"]=tuple(n)        
        
        return rec



    def getrecordnames(self,ctxid,dbid=0,host=None):
        """All record names a ctxid can access. Includes groups. Deprecated; calls getindexbycontext.""" 
        return self.getindexbycontext(ctxid,host=host)
    
    
    
    def getrecordschangetime(self,recids,ctxid,host=None):
        """Returns a list of times for a list of recids. Times represent the last modification 
        of the specified records"""

        secure=set(self.getindexbycontext(ctxid,host=host))
        rid=set(recids)
        rid-=secure
        if len(rid)>0 : raise Exception,"Cannot access records %s"%str(rid)
        
        try: ret=[self.__timeindex[i] for i in recids]
        except: raise Exception,"unindexed time on one or more recids"
        
        return ret 
        
        
    # ian todo: move host to end
    def trygetrecord(self,recid,ctxid,host=None,dbid=0):
        """Checks to see if a record could be retrieved without actually retrieving it."""
        ctx=self.__getcontext(ctxid,host)
        #if ctx.user=="root" or -1 in ctx.groups or -2 in ctx.groups:
        if self.checkreadadmin(ctx):
            return 1
        # ian: fix anonymous access
        if self.__secrindex.testref(-4,recid) : return 1 # anonymous access
        if self.__secrindex.testref(-3,recid) : return 1        # global read access
        if self.__secrindex.testref(ctx.user,recid) : return 1    # user access
        for i in ctx.groups: 
            try:
                if self.__secrindex.testref(i,recid) : return 1
            except: 
                continue
        return 0
    
    
    # ian todo: move host to end
    def getrecord(self,recid,ctxid,host=None,dbid=0):
        """Primary method for retrieving records. ctxid is mandatory. recid may be a list.
        if dbid is 0, the current database is used. host must match the host of the
        context"""
        

        ctx=self.__getcontext(ctxid,host)
        
        if (dbid!=0) : raise NotImplementedError("External database support not yet available") #Ed Changed to NotimplementedError
        
        # if a single id was requested, return it
        # setContext is required to make the record valid, and returns a binary security tuple
        
        if (hasattr(recid,'__int__')):
            recid = int(recid)
            rec=self.__records[recid]
            p=rec.setContext(ctx)
            if not p[0] : raise SecurityError,"Permission Denied" # ian: changed Exception to SecurityError
            return rec
        elif (hasattr(recid,'__iter__')):
            recl=map(lambda x:self.__records[x],recid)
            for rec in recl:
                p=rec.setContext(ctx)
                if not p[0] : raise SecurityError,"Permission denied on one or more records"    # ian: changed Exception to SecurityError
            return recl
        else:
            # ian: js only allows strings as Array keys.. so let's fallback to attempt to recast to int before giving up
            try:
                recid=int(recid)
                return self.getrecord(recid,ctxid,host)
            except:            
                raise KeyError,"Invalid Key %s"%str(recid) # Edward Langley changed Key Error to SecurityError for consistency
#        else : raise KeyError,"Invalid Key %s"%str(recid)
        
        
    def getparamvalue(self,paramname,recid,ctxid,dbid=0,host=None):
        #slow and insecure needs indexes for speed

        paramname=str(paramname).lower()
        
        paramindex = self.__getparamindex(paramname)
        if hasattr(recid, '__iter__'):
            results = []
            for key in paramindex.keys():
                if set(paramindex[key]) & set(recid):
                    results.insert(0, key)
            return results
        else:
            for key in paramindex.keys():
                if paramindex[key].pop() == recid:
                    return key
        
    def getrecordsafe(self,recid,ctxid,dbid=0,host=None):
        """Same as getRecord, but failure will produce None or a filtered list"""
        
        ctx=self.__getcontext(ctxid,host)
        
        if (dbid!=0) : return None
        
        if (isinstance(recid,int)):
            try:
                rec=self.__records[recid]
            except: 
                return None
            p=rec.setContext(ctx)
            if not p[0] : return None
            return rec
        elif (isinstance(recid,list)):
            try:
                recl=map(lambda x:self.__records[x],recid)
            except: 
                return None
            recl=filter(lambda x:x.setContext(ctx)[0],recl)
            return recl
        else : return None
    
    
    
    # ian: moved host to end. 
    # ian todo: give this a complete check; it's a big function.
    # ian todo: combine with secrecorddeluser to reduce security critical code
    #                        and just alias to adduser with an arg or something.
    #@write,user
    def secrecordadduser(self,usertuple,recid,ctxid,recurse=0,host=None):
        """This adds permissions to a record. usertuple is a 4-tuple containing users
        to have read, comment, write and administrativepermission. Each value in the tuple is either
        a string (username) or a tuple/list of usernames. If recurse>0, the
        operation will be performed recursively on the specified record's children
        to a limited recursion depth. Note that this ADDS permissions to existing
        permissions on the record. If addition of a lesser permission than the
        existing permission is requested, no change will be made. ie - giving a
        user read access to a record they already have write access to will
        have no effect. Any children the user doesn't have permission to
        update will be silently ignored."""
        
        if not isinstance(usertuple,tuple) and not isinstance(usertuple,list) :
            raise ValueError,"permissions must be a 4-tuple/list of tuples,strings,ints" 

        usertuple=list(usertuple)[:4]
        
        for i in range(4):
            if not isinstance(usertuple[i],tuple):
                if usertuple[i]==None : usertuple[i]=tuple()
                elif isinstance(usertuple[i],str) : usertuple[i]=(usertuple[i],)
                elif isinstance(usertuple[i],int) : usertuple[i]=(usertuple[i],)
                else:
                    try: usertuple[i]=tuple(usertuple[i])
                    except: raise ValueError,"permissions must be a 4-tuple/list of tuples,strings,ints"

        # all users
        userset = set(self.getusernames(ctxid)) | set((-4,-3,-2,-1))

        #print userset
        #print usertuple

        # get a list of records we need to update
        if recurse>0:
            if DEBUG: print "Add user recursive..."
            trgt=self.getchildren(recid,ctxid=ctxid,host=host,recurse=recurse-1)
            trgt.add(recid)
        else : trgt=set((recid,))
        
        ctx=self.__getcontext(ctxid,host)
        if self.checkadmin(ctx):
            isroot=1
        else:
            isroot=0
        
        # this will be a dictionary keyed by user of all records the user has
        # just gained access to. Used for fast index updating
        secrupd={}
        
        print trgt
        
        txn=self.newtxn()
        # update each record as necessary
        for i in trgt:
            #try:
            rec=self.getrecord(i,ctxid,host=host)            # get the record to modify
            #except:
            #    print "skipping %s"%i
            #    continue
            
            # if the context does not have administrative permission on the record
            # then we just skip this record and leave the permissions alone
            # TODO: probably we should also check for groups in [3]
            if ctx.user not in rec["permissions"][3] and not self.checkadmin(ctx): continue        
            
            print "rec: %s"%i
            
            cur=[set(v) for v in rec["permissions"]]        # make a list of sets out of the current permissions
            xcur=[set(v) for v in rec["permissions"]]        # copy of cur that will be changed
#            l=[len(v) for v in cur]    #length test not sufficient # length of each tuple so we can decide if we need to commit changes
            newv=[set(v) for v in usertuple]                # similar list of sets for the new users to add
            
            # check for valid user names
            newv[0]&=userset
            newv[1]&=userset
            newv[2]&=userset
            newv[3]&=userset
                        
            # update the permissions for each group
            xcur[0]|=newv[0]
            xcur[1]|=newv[1]
            xcur[2]|=newv[2]
            xcur[3]|=newv[3]
            
            # if the user already has more permission than we are trying
            # to assign, we don't do anything. This also cleans things up
            # so a user cannot have more than one security level
            xcur[0]-=xcur[1]
            xcur[0]-=xcur[2]
            xcur[0]-=xcur[3]
            xcur[1]-=xcur[2]
            xcur[1]-=xcur[3]
            xcur[2]-=xcur[3]
#            l2=[len(v) for v in cur]  # length test not sufficient
            
            # update if necessary
#            if l!=l2 :
            if xcur[0] != cur[0] or xcur[1] != cur[1] \
               or xcur[2] != cur[2] or xcur[3] != cur[3]:
                old=rec["permissions"]
                rec["permissions"]=(tuple(xcur[0]),tuple(xcur[1]),tuple(xcur[2]),tuple(xcur[3]))
#                print "new permissions: %s"%rec["permissions"]
# SHOULD do it this way, but too slow
#                rec.commit()
                
                # commit is slow because of the extensive checks for changes
                # in this case we know only the security changed. We also don't
                # update the modification time. In fact, we build up a list of changes
                # then do it all at once.
#                self.__reindexsec(reduce(operator.concat,old),
#                    reduce(operator.concat,rec["permissions"]),rec.recid)
                
                stu=(xcur[0]|xcur[1]|xcur[2]|xcur[3])-set(old[0]+old[1]+old[2]+old[3])
                for i in stu:
                    try: secrupd[i].append(rec.recid)
                    except: secrupd[i]=[rec.recid]
                
                # put the updated record back
                self.__records.set(rec.recid,rec,txn)
        
        for i in secrupd.keys() :
            self.__secrindex.addrefs(i,secrupd[i],txn)
        if txn: txn.commit()
        elif not self.__importmode : DB_syncall()
    
    
    
    # ian: moved host to end. see notes above.
    #@write,user
    def secrecorddeluser(self,users,recid,ctxid,recurse=0,host=None):
        """This removes permissions from a record. users is a username or tuple/list of
        of usernames to have no access to the record at all (will not affect group 
        access). If recurse>0, the operation will be performed recursively 
        on the specified record's children to a limited recursion depth. Note that 
        this REMOVES all access permissions for the specified users on the specified
        record."""


        if isinstance(users,str) or isinstance(users,int):
            users=set([users])
        else:
            users=set(users)

        # get a list of records we need to update
        if recurse>0:
            if DEBUG: print "Del user recursive..."
            trgt=self.getchildren(recid,ctxid=ctxid,host=host,recurse=recurse-1)
            trgt.add(recid)
        else : trgt=set((recid,))
        
        ctx=self.__getcontext(ctxid,host)
        users.discard(ctx.user)                # user cannot remove his own permissions
        #if ctx.user=="root" or -1 in ctx.groups : isroot=1
        if self.checkadmin(ctx): isroot=1
        else: isroot=0

        # this will be a dictionary keyed by user of all records the user has
        # just gained access to. Used for fast index updating
        secrupd={}
        
        txn=self.newtxn()
        # update each record as necessary
        for i in trgt:
            try:
                rec=self.getrecord(i,ctxid,host=host)            # get the record to modify
            except: continue
            
            # if the user does not have administrative permission on the record
            # then we just skip this record and leave the permissions alone
            # TODO: probably we should also check for groups in [3]            
            if (not isroot) and (ctx.user not in rec["permissions"][3]) : continue        
            
            cur=[set(v) for v in rec["permissions"]]        # make a list of Sets out of the current permissions
            l=[len(v) for v in cur]                            # length of each tuple so we can decide if we need to commit changes
            
            cur[0]-=users
            cur[1]-=users
            cur[2]-=users
            cur[3]-=users
                        
            l2=[len(v) for v in cur]
                
            # update if necessary
            if l!=l2 :
                old=rec["permissions"]
                rec["permissions"]=(tuple(cur[0]),tuple(cur[1]),tuple(cur[2]),tuple(cur[3]))

# SHOULD do it this way, but too slow
#                rec.commit()
                
                # commit is slow because of the extensive checks for changes
                # in this case we know only the security changed. We also don't
                # update the modification time
#                print reduce(operator.concat,old)
#                print reduce(operator.concat,rec["permissions"])
#                self.__reindexsec(reduce(operator.concat,old),
#                    reduce(operator.concat,rec["permissions"]),rec.recid)
                
                for i in users:
                    try: secrupd[i].append(rec.recid)
                    except: secrupd[i]=[rec.recid]
                
                
                # put the updated record back
                self.__records.set(rec.recid,rec,txn)
        
        for i in secrupd.keys() :
            self.__secrindex.removerefs(i,secrupd[i],txn)
        if txn: txn.commit()
        elif not self.__importmode : DB_syncall()


    ##########
    # internal view rendering functions
    ##########
    
    
    
    def getrecordrecname(self,recid,ctxid,host=None):
        """Render the recname view for a record."""
        try:
            rec=self.getrecord(recid,ctxid)
        except:
            return "(permission denied)"
            
        value=self.renderview(rec,viewtype="recname",ctxid=ctxid)
        if not value:
            value = "(%s: %s)"%(rec.rectype, rec.recid)
        return value
    
    
    
    def getrecordrenderedviews(self,recid,ctxid,host=None):
        """Render all views for a record."""
        rec=self.getrecord(recid,ctxid,host=host)
        recdef=self.getrecorddef(rec["rectype"],ctxid,host=host)
        views=recdef.views
        views["mainview"] = recdef.mainview
        for i in views:
            views[i] = self.renderview(rec,viewdef=views[i],ctxid=ctxid,host=host)
        return views
    
    
    
    # ian: moved host to end
    # ian todo: make ctxid required?
    def renderview(self,rec,viewdef=None,viewtype="defaultview",paramdefs={},macrocache={},ctxid=None,showmacro=True,host=None):
        """Render a view for a record. Takes a record instance or a recid.
        viewdef is an arbitrary view definition. viewtype is a name view from record def.
        paramdefs and macrocache are prefetched values to speed up when called many times. macrocache not currently used."""
                
        if type(rec) == int:
            if self.trygetrecord(rec,ctxid):
                rec=self.getrecord(rec,ctxid,host=host)
            else:
                print "renderview: permissions error %s"%rec
                return ""
                
        if viewdef == None:
            recdef=self.getrecorddef(rec["rectype"],ctxid,host=host)
            if viewtype=="mainview":
                viewdef=recdef.mainview
            else:
                viewdef = recdef.views.get(viewtype, recdef.name)
        
        # fixme: better, more general solution needed.
        #    try:
        # a=unicode(viewdef)
        #    except:

        a=unicode(viewdef,errors="ignore")
            
        iterator=regex2.finditer(a)
                
        for match in iterator:
            pass

            #################################
            # Parameter short_desc
            # TODO: trest
            if match.group("name"):

                name=str(match.group("name1"))
                if paramdefs.has_key(name):
                    value = paramdefs[name].desc_short
                else:
                    value = self.getparamdef(name).desc_short
                viewdef = viewdef.replace(u"$#"+match.group("name")+match.group("namesep"),value+match.group("namesep"))


            #################################
            # Record value
            elif match.group("var"):
                
                var=str(match.group("var1"))
                if paramdefs.has_key(var):
                    vartype=paramdefs[var].vartype                    
                else:
                    vartype = self.getparamdef(var).vartype

                # vartype representations. todo: external function
                value = rec[var]
                
                if vartype in ["user","userlist"]:
                    if type(value) != list:    value=[value]
                    ustr=[]
                    for i in value:
                        try:
                            urec=self.getrecord(self.getuser(i,ctxid).record,ctxid)
                            ustr.append(u"""%s %s %s (%s)"""%(urec["name_first"],urec["name_middle"],urec["name_last"],i))
                        except:
                            ustr.append(u"(%s)"%i)
                    value=u", ".join(ustr)
                
                elif vartype == "boolean":
                    if value:
                        value = u"True"
                    else:
                        value = u"False"
                
                elif vartype in ["floatlist","intlist"]:
                    value=u", ".join([str(i) for i in value])
                
                elif type(value) == type(None):
                    value = u""
                elif type(value) == list:
                    value = u", ".join(value)
                elif type(value) == float:
                    value = u"%0.2f"%value
                else:
                    value = pcomments.sub("<br />",unicode(value))
                
                # now replace..
                viewdef = viewdef.replace(u"$$"+match.group("var")+match.group("varsep"),value+match.group("varsep"))

             ######################################
             # Macros
            if match.group("macro"):

                if match.group("macro")=="recid":
                    value = unicode(rec.recid)
                else:
                    value = unicode(self.macroprocessor(rec, match.group("macro1"), match.group("macro2"), ctxid=ctxid, host=host))

                m2=match.group("macro2")
                if m2 == None:
                    m2=u""

                viewdef = viewdef.replace(u"$@" + match.group("macro1") + u"(" + m2 + u")" + match.group("macrosep"),value+match.group("macrosep"))

        return viewdef



    # Extensive modifications by Edward Langley
    def macroprocessor(self, rec, macr, macroparameters, ctxid, host=None):
        print 'macros(%d): %s' % (id(macro.MacroEngine._macros), macro.MacroEngine._macros)
        return macro.MacroEngine.call_macro(macr, True, self, rec, macroparameters, ctxid=ctxid, host=host)    



    ###########
    # The following routines for xmlizing aspects of the database are very simple, 
    # and also quite verbose. That is a lot of this could
    # be done with a function for, say, xmlizing a dictionary. However, this explicit approach
    # should be significantly faster, a key point if dumping an entire database
    ###########
        
    def getparamdefxml(self,names=None,host=None):
        """Returns XML describing all, or a subset of the existing paramdefs"""
        
        ret=[]
        if names==None : names=self.getparamdefnames()
        
        # these lines are long for better speed despite their ugliness
        for i in names:
            pd=self.getparamdef(i)
            # This should probably be modified to make sure all included strings are XML-safe
            ret.append('<paramdef name="%s">\n  <vartype value="%s"/>\n  <desc_short value="%s"/>\n  <desc_long value="%s"/>\n'%(pd.name,pd.vartype,escape2(pd.desc_short),escape2(pd.desc_long)))
            ret.append('  <property value="%s"/>\n  <defaultunits value="%s"/>\n  <creator value="%s"/>\n  <creationtime value="%s"/>\n  <creationdb value="%s"/>\n'%(pd.property,escape2(pd.defaultunits),pd.creator,pd.creationtime,pd.creationdb))
            
            if pd.choices and len(pd.choices)>0 :
                ret.append('  <choices>\n')
                for j in pd.choices:
                    ret.append('  <choice>%s</choice>\n'%escape2(j))
                ret.append('  </choices>\n')
            
            ch=self.getchildren(i,keytype="paramdef")
            if ch and len(ch)>0 :
                ret.append('  <children>\n')
                for j in ch:
                    ret.append('    <link name="%s"/>\n'%j)
                ret.append('  </children>\n')
                
            csn=self.getcousins(i,keytype="paramdef")
            if csn and len(csn)>0 :
                ret.append('  <cousins>\n')
                for j in csn:
                    ret.append('    <link name="%s"/>\n'%j)
                ret.append('  </cousins>\n')
            ret.append('</paramdef>\n')
            
        return "".join(ret)


    # ian: moved host to end
    def getrecorddefxml(self,ctxid,names=None,host=None):
        """Returns XML describing all, or a subset of existing recorddefs"""
        ret=[]
        if names==None : names=self.getrecorddefnames()

        for i in names:
            try: rd=self.getrecorddef(i,ctxid,host=host)
            except: continue

            ret.append('<recorddef name="%s">\n  <private value="%d"/>\n  <owner value="%s"/>\n  <creator value="%s"/>\n  <creationtime value="%s"/>\n  <creationdb value="%s"/>\n'%(i,rd.private,rd.owner,rd.creator,rd.creationtime,rd.creationdb))
            ret.append('  <mainview>%s</mainview>\n'%escape2(rd.mainview))
            
            if rd.params and len(rd.params)>0 :
                ret.append('  <params>\n')
                for k,v in rd.params.items():
                    if v==None : ret.append('    <param name="%s"/>\n'%k)
                    else: ret.append('    <param name="%s" default="%s"/>\n'%(k,v))
                ret.append('  </params>\n')
                
            if rd.views and len(rd.views)>0 :
                ret.append('  <views>\n')
                for k,v in rd.views.items():
                    ret.append('    <view name="%s">%s</view>\n'%(k,escape2(v)))
                ret.append('  </views>\n')
                
            ch=self.getchildren(i,keytype="recorddef")
            if len(ch)>0 :
                ret.append('  <children>\n')
                for j in ch:
                    ret.append('    <link name="%s"/>\n'%j)
                ret.append('  </children>\n')
                
            csn=self.getcousins(i,keytype="recorddef")
            if len(ch)>0 :
                ret.append('  <cousins>\n')
                for j in csn:
                    ret.append('    <link name="%s"/>\n'%j)
                ret.append('  </cousins>\n')
            
            ret.append('</recorddef>\n')
            
        return "".join(ret)


    # ian: moved host to end
    def getuserxml(self,ctxid,names=None,host=None):
        """Returns XML describing all, or a subset of existing users"""
        qc={'"':'&quot'}
        ret=[]
        if names==None : names=self.getusernames(ctxid,host=host)
        
        for i in names:
            try: u=self.getuser(i,ctxid,host=host)
            except: continue
            ret.append('<user name="%s">\n'%i)
            ret.append('  <password value="%s"/>\n  <disabled value="%d"/>\n  <privacy value="%d"/>\n  <creator value="%s"/>\n  <creationtime value="%s"/>\n'%(u.password,u.disabled,u.privacy,u.creator,u.creationtime))
            ret.append('  <firstname value="%s"/>\n  <midname value="%s"/>\n  <lastname value="%s"/>\n  <institution value="%s"/>\n'%(escape2(u.name[0]),escape2(u.name[1]),escape2(u.name[2]),escape2(u.institution)))
            ret.append('  <department value="%s"/>\n  <address>%s</address>\n  <city value="%s"/>\n  <state value="%s"/>\n  <zipcode value="%s"/>\n'%(escape2(u.department),escape2(u.address),escape2(u.city),u.state,u.zipcode))
            ret.append('  <country value="%s"/>\n  <webpage value="%s"/>\n  <email value="%s"/>\n  <altemail value="%s"/>\n'%(u.country,escape2(u.webpage),escape2(u.email),escape2(u.altemail)))
            ret.append('  <phone value="%s"/>\n  <fax value="%s"/>\n  <cellphone value="%s"/>\n'%(escape2(u.phone),escape2(u.fax),escape2(u.cellphone)))
            if len(u.groups)>0:
                ret.append('  <groups>\n')
                for j in u.groups:
                    ret.append('    <group value="%s"/>\n'%j)
                ret.append('  </groups>\n')
            ret.append('/user\n')

        return "".join(ret)


    
    # ian: moved host to end
    def getworkflowxml(self,ctxid,wfid=None,host=None):
        """Returns XML describing all, or a subset of workflows"""
        print "WARNING getworkflowxml unimplemented"
        return ""
    
    
    
    # ian: moved host to end
    def getrecordxml(self,ctxid,recids=None,host=None):
        """Returns XML describing all, or a subset of records"""
        qc={'"':'&quot'}
        ret=[]
        if recids==None : recids=self.getindexbycontext(ctxid,host=host)

        for i in recids:
            try: rec=self.getrecord(i,ctxid,host=host)
            except: continue
            
            ret.append('<record name="%s" dbid="%s" rectype="%s">\n'%(i,str(rec.dbid),rec.rectype))
            ret.append('  <creator value="%s"/>\n  <creationtime value="%s"/>\n'%(rec["creator"],rec["creationtime"]))
            
            ret.append('  <permissions value="read">\n')
            for j in rec["permissions"][0]:
                if isinstance(j,int) : ret.append('    <group value="%d"/>\n'%j)
                else : ret.append('    <user value="%s"/>\n'%str(j))
            ret.append('  </permissions>\n')
            
            ret.append('  <permissions value="comment">\n')
            for j in rec["permissions"][1]:
                if isinstance(j,int) : ret.append('    <group value="%d"/>\n'%j)
                else : ret.append('    <user value="%s"/>\n'%str(j))
            ret.append('  </permissions>\n')
            
            ret.append('  <permissions value="write">\n')
            for j in rec["permissions"][2]:
                if isinstance(j,int) : ret.append('    <group value="%d"/>\n'%j)
                else : ret.append('    <user value="%s"/>\n'%str(j))
            ret.append('  </permissions>\n')
            
            pk=rec.getparamkeys()
            for j in pk:
                ret.append('  <param name="%s" value="%s"/>\n'%(j,str(rec[j])))

            for j in rec["comments"]:
                ret.append('  <comment user="%s" date="%s">%s</comment>\n'%(j[0],j[1],escape2(j[2])))
            
            ch=self.getchildren(i,keytype="record")
            if len(ch)>0 :
                ret.append('  <children>\n')
                for j in ch:
                    ret.append('    <link name="%s"/>\n'%j)
                ret.append('  </children>\n')
                
            csn=self.getcousins(i,keytype="record")
            if len(csn)>0 :
                ret.append('  <cousins>\n')
                for j in csn:
                    ret.append('    <link name="%s"/>\n'%j)
                ret.append('  </cousins>\n')
                
            ret.append('</record>')
            
        return "".join(ret)
            
            
            
    def getasxml(self,body,host=None):
        return '<?xml version="1.0" encoding="UTF-8"?>\n<!-- Generated by EMEN2 -->\n<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">\n%s\n</xs:schema>'%body

        
    # ian: moved host to end
    # ian: changed to __backup to not export via rpc
    #@write,private
    def _backup(self,ctxid,users=None,paramdefs=None,recorddefs=None,records=None,workflows=None,bdos=None,outfile=None,host=None):
        """This will make a backup of all, or the selected, records, etc into a set of files
        in the local filesystem"""

        #if user!="root" :
        ctx=self.__getcontext(ctxid,host)
        if not self.checkadmin(ctx):
            raise SecurityError,"Only root may backup the database"


        print 'backup has begun'
        #user,groups=self.checkcontext(ctxid,host)
        user=ctx.user
        groups=ctx.groups
                
        if users==None: users=self.__users.keys()
        if paramdefs==None: paramdefs=set(self.__paramdefs.keys())
        if recorddefs==None: recorddefs=set(self.__recorddefs.keys())
        if records==None: records=set(range(0,self.__records[-1]))
        if workflows==None: workflows=set(self.__workflow.keys())
        if bdos==None: bdos=set(self.__bdocounter.keys())
        if isinstance(records,list) or isinstance(records,tuple): records=set(records)
        
        if outfile == None:
            out=open(self.path+"/backup.pkl","w")
        else:
            out=open(outfile,"w")

        print 'backup file opened'
        # dump users
        for i in users: dump(self.__users[i],out)
        print 'users dumped'
        # dump workflow
        for i in workflows: dump(self.__workflow[i],out)
        print 'workflows dumped'
        
        # dump binary data objects
        dump("bdos",out)
        bd={}
        for i in bdos: bd[i]= self.__bdocounter[i]
        dump(bd,out)
        bd=None
        print 'bdos dumped'
        
        # dump paramdefs and tree
        for i in paramdefs: dump(self.__paramdefs[i],out)
        ch=[]
        for i in paramdefs:
            c=set(self.__paramdefs.children(i))
#            c=set([i[0] for i in c])
            c&=paramdefs
            c=tuple(c)
            ch+=((i,c),)
        dump("pdchildren",out)
        dump(ch,out)
        print 'paramdefs dumped'
        
        ch=[]
        for i in paramdefs:
            c=set(self.__paramdefs.cousins(i))
            c&=paramdefs
            c=tuple(c)
            ch+=((i,c),)
        dump("pdcousins",out)
        dump(ch,out)
        print 'pdcousins dumped'
                
        # dump recorddefs and tree
        for i in recorddefs: dump(self.__recorddefs[i],out)
        ch=[]
        for i in recorddefs:
            c=set(self.__recorddefs.children(i))
#            c=set([i[0] for i in c])
            c&=recorddefs
            c=tuple(c)
            ch+=((i,c),)
        dump("rdchildren",out)
        dump(ch,out)
        print 'rdchildren dumped'
        
        ch=[]
        for i in recorddefs:
            c=set(self.__recorddefs.cousins(i))
            c&=recorddefs
            c=tuple(c)
            ch+=((i,c),)
        dump("rdcousins",out)
        dump(ch,out)
        print 'rdcousins dumped'

        # dump actual database records
        print "Backing up %d/%d records"%(len(records),self.__records[-1])
        for i in records:
            dump(self.__records[i],out)
        print 'records dumped'

        ch=[]
        for i in records:
            c=[x for x in self.__records.children(i) if x in records]
            c=tuple(c)
            ch+=((i,c),)
        dump("recchildren",out)
        dump(ch,out)
        print 'rec children dumped'
        
        ch=[]
        for i in records:
            c=set(self.__records.cousins(i))
            c&=records
            c=tuple(c)
            ch+=((i,c),)
        dump("reccousins",out)
        dump(ch,out)
        print 'rec cousins dumped'

        out.close()



    def restore(self,ctxid,host=None):
        """This will restore the database from a backup file. It is nondestructive, in that new items are
        added to the existing database. Naming conflicts will be reported, and the new version
        will take precedence, except for Records, which are always appended to the end of the database
        regardless of their original id numbers. If maintaining record id numbers is important, then a full
        backup of the database must be performed, and the restore must be performed on an empty database."""
        
        if not self.__importmode: self.LOG(3,"WARNING: database should be opened in importmode when restoring from file, or restore will be MUCH slower. This requires sufficient ram to rebuild all indicies.")
        
        self.LOG(4,"Begin restore operation")
        #user,groups=self.checkcontext(ctxid,host)
        ctx=self.__getcontext(ctxid,host)
        user=ctx.user
        groups=ctx.groups
        #if user!="root" :
        if not self.checkadmin(ctx):
            raise SecurityError,"Only root may restore the database"
        
        if os.access(self.path+"/backup.pkl",os.R_OK) : fin=open(self.path+"/backup.pkl","r")
        elif os.access(self.path+"/backup.pkl.bz2",os.R_OK) : fin=os.popen("bzcat "+self.path+"/backup.pkl.bz2","r")
        elif os.access(self.path+"/../backup.pkl.bz2",os.R_OK) : fin=os.popen("bzcat "+self.path+"/../backup.pkl.bz2","r")
        else: raise IOError,"backup.pkl not present"

        recmap={}
        nrec=0
        t0=time.time()
        tmpindex={}
        txn=None
        nel=0
        
        while (1):
            try:
                r=load(fin)
            except:
                break
            
            # new transaction every 100 elements
            #if nel%100==0 :
                #if txn : txn.commit()
                #txn=self.__dbenv.txn_begin(flags=db.DB_READ_UNCOMMITTED)
            nel+=1
            if txn: txn.commit()
            else : 
                if nel%500==0 : 
#                    print "SYNC:",self.__dbenv.lock_stat()["nlocks"]," ... ",
                    DB_syncall()
#                    print self.__dbenv.lock_stat()["nlocks"]
#                    time.sleep(10.0)
#                    print self.__dbenv.lock_stat()["nlocks"]

            txn=self.newtxn()
            
            # insert User
            if isinstance(r,User) :
                if self.__users.has_key(r.username,txn) :
                    print "Duplicate user ",r.username
                    self.__users.set(r.username,r,txn)
                else :
                    self.__users.set(r.username,r,txn)
            # insert Workflow
            elif isinstance(r,WorkFlow) :
                self.__workflow.set(r.wfid,r,txn)
            # insert paramdef
            elif isinstance(r,ParamDef) :
                r.name=r.name.lower()
                if self.__paramdefs.has_key(r.name,txn):
                    print "Duplicate paramdef ",r.name
                    self.__paramdefs.set(r.name,r,txn)
                else :
                    self.__paramdefs.set(r.name,r,txn)
            # insert recorddef
            elif isinstance(r,RecordDef) :
                r.name=r.name.lower()
                if self.__recorddefs.has_key(r.name,txn):
                    print "Duplicate recorddef ",r.name
                    self.__recorddefs.set(r.name,r,txn)
                else :
                    self.__recorddefs.set(r.name,r,txn)
            # insert and renumber record
            elif isinstance(r,Record) :
                # This is necessary only to import legacy database backups from before 04/16/2006
                try:
                    o=r._Record__owner
                    a=r._Record__permissions
                    r._Record__permissions=(a[0],a[1],a[2],(o,))
                    del r._Record__owner
                except:
                    pass
                
                # renumbering
                nrec+=1
#                print nrec
                if nrec%1000==0 :
                    print " %8d records  (%f/sec)\r"%(nrec,nrec/(time.time()-t0))
                    sys.stdout.flush()
                oldid=r.recid
#                r.recid = self.__dbseq.get()                                # Get a new record-id
                r.recid=self.__records.get(-1,txn)
                self.__records.set(-1,r.recid+1,txn)                # Update the recid counter, TODO: do the update more safely/exclusive access
                recmap[oldid]=r.recid
                self.__records.set(r.recid,r,txn)
                self.__recorddefbyrec.set(r.recid,r.rectype,txn)
                r.setContext(ctx)
                
                # work in progress. Faster indexing on restore.
                # Index record
                for k,v in r.items():
                    if k != 'recid':
                        try:
                            self.__reindex(k,None,v,r.recid,txn)
                        except:
                            if DEBUG: 
                                print "Unindexed value: (key, value, recid)"
                                print k
#                                print v
                                print r.recid
                
                self.__reindexsec([],reduce(operator.concat,r["permissions"]),r.recid,txn)        # index security
                self.__recorddefindex.addref(r.rectype,r.recid,txn)            # index recorddef
                self.__timeindex.set(r.recid,r["creationtime"],txn)

                
            elif isinstance(r,str) :
                if r=="bdos" :
                    rr=load(fin)            # read the dictionary of bdos
                    for i,d in rr.items():
                        self.__bdocounter.set(i,d,txn)
                elif r=="pdchildren" :
                    rr=load(fin)            # read the dictionary of ParamDef PC links
                    for p,cl in rr:
                        for c in cl:
                            self.__paramdefs.pclink(p,c,txn)
                elif r=="pdcousins" :
                    rr=load(fin)            # read the dictionary of ParamDef PC links
                    for a,bl in rr:
                        for b in bl:
                            self.__paramdefs.link(a,b,txn)
                elif r=="rdchildren" :
                    rr=load(fin)            # read the dictionary of ParamDef PC links
                    for p,cl in rr:
                        for c in cl:
                            self.__recorddefs.pclink(p,c,txn)
                elif r=="rdcousins" :
                    rr=load(fin)            # read the dictionary of ParamDef PC links
                    for a,bl in rr:
                        for b in bl:
                            self.__recorddefs.link(a,b,txn)
                elif r=="recchildren" :
                    rr=load(fin)            # read the dictionary of ParamDef PC links
                    for p,cl in rr:
                        for c in cl:
#                            print p, c
#                            print recmap[p],recmap[c[0]],c[1]
                            if isinstance(c,tuple) : print "Invalid (deprecated) named PC link, database restore will be incomplete"
                            else : self.__records.pclink(recmap[p],recmap[c],txn)
                elif r=="reccousins" :
                    rr=load(fin)            # read the dictionary of ParamDef PC links
                    for a,bl in rr:
                        for b in bl:
                            self.__records.link(recmap[a],recmap[b],txn)
                else : print "Unknown category ",r
        
        if txn: 
            txn.commit()
            self.LOG(4,"Import Complete, checkpointing")
            self.__dbenv.txn_checkpoint()
        elif not self.__importmode : DB_syncall()
        if self.__importmode :
            self.LOG(4,"Checkpointing complete, dumping indices")
            self.__commitindices()
            
            
            
    def restoretest(self,ctxid,host=None):
        """This method will check a database backup and produce some statistics without modifying the current database."""
        
        if not self.__importmode: print("WARNING: database should be opened in importmode when restoring from file, or restore will be MUCH slower. This requires sufficient ram to rebuild all indicies.")
        
        #user,groups=self.checkcontext(ctxid,host)
        ctx=self.__getcontext(ctxid,host)
        user=ctx.user
        groups=ctx.groups
        #if user!="root" :
        if not self.checkadmin(ctx):
            raise SecurityError,"Only root may restore the database"
        
        if os.access(self.path+"/backup.pkl",R_OK) : fin=open(self.path+"/backup.pkl","r")
        elif os.access(self.path+"/backup.pkl.bz2",R_OK) : fin=os.popen("bzcat "+self.path+"/backup.pkl.bz2","r")
        elif os.access(self.path+"/../backup.pkl.bz2",R_OK) : fin=os.popen("bzcat "+self.path+"/../backup.pkl.bz2","r")
        else: raise IOError,"backup.pkl not present"
        
        recmap={}
        nrec=0
        t0=time.time()
        tmpindex={}
        
        nu,npd,nrd,nr,np=0,0,0,0,0
        
        while (1):
            try:
                r=load(fin)
            except:
                break
            
            # insert User
            if isinstance(r,User) :
                nu+=1

            # insert paramdef
            elif isinstance(r,ParamDef) :
                npd+=1
            
            # insert recorddef
            elif isinstance(r,RecordDef) :
                nrd+=1
                
            # insert and renumber record
            elif isinstance(r,Record) :
                r.setContext(ctx)
                try:
                    o=r._Record__owner
                    a=r._Record__permissions
                    r._Record__permissions=(a[0],a[1],a[2],(o,))
                    del r._Record__owner
                except:
                    pass
                if (nr<20) : print r["identifier"]
                nr+=1
                
            elif isinstance(r,str) :
                if r=="pdchildren" :
                    rr=load(fin)            # read the dictionary of ParamDef PC links
                    np+=len(rr)
                elif r=="pdcousins" :
                    rr=load(fin)            # read the dictionary of ParamDef PC links
                    np+=len(rr)
                elif r=="rdchildren" :
                    rr=load(fin)            # read the dictionary of ParamDef PC links
                    np+=len(rr)
                elif r=="rdcousins" :
                    rr=load(fin)            # read the dictionary of ParamDef PC links
                    np+=len(rr)
                elif r=="recchildren" :
                    rr=load(fin)            # read the dictionary of ParamDef PC links
                    np+=len(rr)
                elif r=="reccousins" :
                    rr=load(fin)            # read the dictionary of ParamDef PC links
                    np+=len(rr)
                else : print "Unknown category ",r
                                
        print "Users=",nu,"  ParamDef=",npd,"  RecDef=",nrd,"  Records=",nr,"  Links=",np


    #@write,private
    def __del__(self): 
        self.close()


    #@write,admin
    def close(self):
        "disabled at the moment"
        if self.__allowclose == True:
            for btree in self.__dict__.values():
                if getattr(btree, '__class__', object).__name__.endswith('BTree'):
                    try:
                        btree.close()
                    except db.InvalidArgError, e:
                        print e
            for btree in self.__fieldindex.values():
                btree.close()
            self.__dbenv.close()
#        pass
#        print self.__btreelist
#        self.__btreelist.extend(self.__fieldindex.values())
#        print self.__btreelist
#        for bt in self.__btreelist:
#            print '--', bt ; sys.stdout.flush()
#            bt.close()