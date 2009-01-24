from emen2.Database.subsystems.macro import add_macro

from functools import partial#

#g = emen2.globalns.GlobalNamespace('')
#g.debug.msg(g.LOG_INIT, 'MACROS: Importing core macros')


@add_macro('recid')
def get_recid(engine, db, rec, parameters, **extra):
	return rec.recid

@add_macro('recname')
def get_recname(engine,db, rec, parameters, ctxid, host, **extra):
	recdef=db.getrecorddef(rec.rectype,ctxid,host=host)
	view = recdef.views.get("recname", "(no recname view)")
	result = db.renderview(rec,view,ctxid=ctxid,host=host)
	return result

def isofrecdef(engine, db, recid, recdef, rinfo):
	rec = db.getrecord(recid, **rinfo)
	return rec.rectype == recdef

import time

@add_macro('childcount')
def get_childcount(engine, db, rec, recdef, ctxid, host, **extra):
	#print "childcount"
	recid = rec['recid']

	key1 = engine.get_cache_key('indexbyrecorddef',recdef)
	key2 = engine.get_cache_key('ccount')
	
	res1 = engine.check_cache(key1)
	res2 = engine.check_cache(key2)
	
	hit1, ind = res1 or (False, set())
	hit2, childrendict = res2 or (False, {})

	#print childrendict

	if hit1 is False:
		#print "getindexbyrecorddef"
		ind=db.getindexbyrecorddef(recdef, ctxid)
		engine.store(key1, ind)

	#if hit3 is False:
	#	print "getindexdictbycontext"
	#	indc=db.getindexbycontext(ctxid)
	#	engine.store(key3,indc)

	if hit2 is False or not childrendict.has_key(recid):
		#print "macro getchildren"
		childrendict[recid]=db.getchildren(recid,recurse=2,ctxid=ctxid)
		
	return len(childrendict[recid] & ind)	
		
	#if hit is False:
		#t=time.time()
		#query=db.getchildren(recid,recurse=2,ctxid=ctxid)
		##r=query & db.getindexbyrecorddef(recdef, ctxid)
		#query=db.getchildren(recid,recurse=2,ctxid=ctxid)
		##print query
		##print len(query)
		#groups=db.groupbyrecorddef(query,ctxid)
		##print time.time()-t
		#engine.store(engine.get_cache_key(recid), groups)

	#groups={}
	#result = 0
	#if groups.has_key(recdef): result = len(groups[recdef])
	#return result

###############################################################################################################################################

def def_join_func(lis, sep=' '): return str.join(sep, lis)
def render_records(db, rec, view, get_recs, rinfo, join_func=def_join_func, renderer=None):
	if renderer is None:
		renderer = partial(db.renderview, viewtype=view, **rinfo)
	recid, result = rec.recid, []
	if isinstance(recid, int):
		result = map(renderer, get_recs(recid))
	return join_func(result)

html_join_func = partial(def_join_func, sep='<br />')
import thread

@add_macro('renderchildren')
def do_renderchildren(engine, db, rec, view, ctxid, host, **extra):
	rinfo = dict(ctxid=ctxid,host=host)
	get_records = partial(db.getchildren, **rinfo)
	return render_records(db, rec, view, get_records,rinfo, html_join_func)

@add_macro('renderchild')
def do_renderchild(engine, db, rec, args, ctxid, host, **extra):
	rinfo = dict(ctxid=ctxid,host=host)
	view, key, value = args.split(' ')
	def get_records(recid):
		return db.getindexbyvalue(key.encode('utf-8'), value, **rinfo).intersection(db.getchildren(recid, **rinfo))
	return render_records(db, rec, view, get_records,rinfo, html_join_func)

@add_macro('renderchildrenoftype')
def do_renderchildrenoftype(db, rec, args, ctxid, host, **extra):
	rinfo = dict(ctxid=ctxid,host=host)
	view, recdef = args.split(' ')
	def get_records(recid):
		return [rec for rec in db.getchildren(recid, **rinfo) if isofrecdef(rec, recdef, rinfo)]
	return render_records(rec, view, get_records,rinfo, html_join_func)



################################################################################################################################################

#print "import core macro"
@add_macro('img')
def do_img(engine, db, rec, args, ctxid, host, **extra):
	#print "img macro"
	default=["file_binary_image","640","640"]
	try:
		ps=args.split(" ")
	except:
		return "(Image Error)"
	for i,v in list(enumerate(ps))[:3]:
		default[i]=v
	param,width,height=default
	
	try:	
		pd=db.getparamdef(param)
	except:
		return "(Unknown parameter)"

	#print pd.vartype

	if pd.vartype=="binary":
		bdos=rec[param]		
	elif pd.vartype=="binaryimage":
		bdos=[rec[param]]
	else:
		return "(Invalid parameter)"
	
	#print bdos
	if bdos==None:
		return "(No Image)"
	
	ret=[]
	for i in bdos:
		try:
			fname,bname,lrecid=db.getbinary(i[4:],ctxid)
			ret.append('<img src="/download/%s/%s" style="max-height:%spx;max-width:%spx;" />'%(i[4:],fname,height,width))
		except:
			ret.append("(Error: %s)"%i)
		
	return "".join(ret)



@add_macro('getrectypesiblings')
def getrectypesiblings(engine, db,rec, args, ctxid, host, **extra):
	"""returns siblings and cousins of same rectype"""
	ret = {}
	parents = db.getparents(rec.recid,ctxid=ctxid)
	siblings = set()

	for i in parents:
		siblings = siblings.union(db.getchildren(i,ctxid=ctxid))

	groups = db.groupbyrecorddef(siblings, ctxid)

	if groups.has_key(rec.rectype):
		q = db.getindexdictbyvaluefast(groups[rec.rectype],"modifytime",ctxid)
		ret = [i[0] for i in sorted(q.items(), key=itemgetter(1), reverse=True)] #BUG: What is supposed to happen here?	

	return str(ret)
	
@add_macro('getfilenames')	
def getfilenames(engine, db,rec, args, ctxid, host, **extra):
	"""returns dictionary of {bid:upload filename}"""
	files = {}
	if rec["file_binary"] or rec["file_binary_image"]:	
		bids = []
		if rec["file_binary"]:
			bids += rec["file_binary"]
		if rec["file_binary_image"]:
			bids += [rec["file_binary_image"]]

		for bid in bids:
			bid = bid[4:]
			try:
				bname,ipath,bdocounter=db.getbinary(bid,ctxid,host)
			except Exception, inst:
				bname="Attachment error: %s"%bid
			files[bid]=bname
		
	return files
	#return str(files)


################################################################################################################################################

def def_join_func(lis, sep=', '): return str.join(sep, lis)
def getvalue(db, recset, attribute, join_func=def_join_func, **rinfo):
	#isgettable = partial(db.trygetrecord, **rinfo)
	#get = partial(db.getrecord, **rinfo)
	#tmp = [ get(rec) for rec in recset if isgettable(rec)]
	tmp = []
	for i in recset:
		try:
			tmp.append(db.getrecord(i,**rinfo))
		except:
			print "error with macro get record: %s"%i
	return join_func([rec[attribute] for rec in tmp if rec.has_key(attribute)])
	
@add_macro('childvalue')
def get_childrenvalue(engine, db, rec, attribute, ctxid, host, **extra):
	recid = rec.recid
	children = db.getchildren(recid, ctxid=ctxid)
	return getvalue(db, children, attribute, ctxid=ctxid, host=host)

@add_macro('parentvalue')
def get_parentvalue(engine, db, rec, attribute, ctxid, host, **extra):
	recid = rec['recid']
	parents = db.getparents(recid, ctxid=ctxid)
	return getvalue(db, parents, attribute, ctxid=ctxid, host=host)

from cgi import escape
@add_macro('escape')
def escape_paramdef_val(engine, db, rec, paramname, **extra):
	return escape(rec.get(paramname, ''))
