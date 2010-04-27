import traceback
import re
import os
import pickle 
import time
import random
import optparse
import sys
import pylab
import collections

#
# try:
# 	import matplotlib
# 	matplotlib.use('Agg')
# 	from matplotlib import pylab, font_manager
# 	from matplotlib.ticker import FormatStrFormatter
# 	from matplotlib import colors
# except:
# 	g.log("No matplotlib, plotting will fail")
# 



def plot(xparam, yparam, subset=None, groupby=None, grouptype="recorddef", rectypes=None, childof=None, cutoff=100, db=None):

	# Colors to use in plot..
	allcolor = ['b', 'g', 'r', 'c', 'm', 'y', '#00ff00', '#800000', '#000080', '#808000', '#800080', '#c0c0c0', '#008080', '#7cfc00', '#cd5c5c', '#ff69b4', '#deb887', '#a52a2a', '#5f9ea0', '#6495ed', '#b8890b', '#8b008b', '#f08080', '#f0e68c', '#add8e6', '#ffe4c4', '#deb887', '#d08b8b', '#bdb76b', '#556b2f', '#ff8c00', '#8b0000', '#8fbc8f', '#ff1493', '#696969', '#b22222', '#daa520', '#9932cc', '#e9967a', '#00bfff', '#1e90ff', '#ffd700', '#adff2f', '#00ffff', '#ff00ff', '#808080']

	try: cutoff = int(cutoff)
	except: cutoff = 100

	# Get items
	c1 = db.getindexdictbyvalue(xparam)
	c2 = db.getindexdictbyvalue(yparam)
	z = set(c1) & set(c2)

	# Restrict items
	if subset:
		z &= subset

	if childof:
		z &= db.getchildren(childof, recurse=50)

	# print "%s items before grouping"%(len(z))

	# Grouping actions
	grouped = collections.defaultdict(set)
	groupnames = {}

	if grouptype == "parent":
		parents = db.getparents(z, recurse=10, flat=True)
		for p in db.groupbyrecorddef(parents).get(groupby,set()):
			grouped[p] = db.getchildren(p, recurse=50, rectype=rectypes) & z
		groupnames = db.renderview(grouped.keys(), viewtype="recname")
		for k in groupnames:
			groupnames[k] = "%s %s"%(k, groupnames[k])

	elif grouptype == "value":
		c = db.getindexdictbyvalue(groupby)
		z &= set(c)
		for p in z:
			grouped[c[p]].add(p)
		for p in grouped:
			groupnames[p] = p
	
	elif grouptype == "recorddef":
		c = db.groupbyrecorddef(z)
		for k,v in c.items():
			grouped[k]=v
		for p in grouped:
			groupnames[p] = p
	
	
	# Ok, actual plotting is pretty simple...
	handles = []
	labels = []

	total = float(len(grouped))
	for count, (k,v) in enumerate(grouped.items()):
		if len(v) < cutoff:
			print "Skipping %s"%k
			continue
		
		handle = pylab.scatter(map(c1.get, v), map(c2.get, v), c=allcolor.pop(0))# cm.hsv(count/total)
		handles.append(handle)

		label = '%s (%s)'%(groupnames.get(k), len(v))
		labels.append(label)
		# pylab.axis([0, 6, 0, 500])
	
	
	# pylab.legend(handles, labels,  bbox_to_anchor=(1, 1))
	# pylab.show()
	

	# From plot_old	
	t = str(time.time())
	rand = str(random.randint(0,100000))
	tempfile = "/graph/t" + t + ".r" + rand + ".png"
	pylab.savefig("tweb" + tempfile)
	return tempfile, z
	
	




def plot_old(thequery, L, groupby=0):
	data = L['data']
	allx = []
	ally = []
	dataRid = []
	myloc = 1
	figsize=(10,6)
	
	if thequery.find("group by") >= 0:
		groupby = 1
	else:
		groupby = 0
	
	if groupby == 0:
			allx = data['x']

			pylab.hold(False)
			if len(allx) == 0:
				page = "<h2>No Result Found! Please change your query and try again</h2>"
				return page

			if thequery.find('histogram') >= 0:
				ally = data[0]
				#ax = pylab.subplot(111)				   
				strX = 1

				N = len(allx)
				ind = range(N)
				width = 1

				sc = pylab.bar(ind, ally, width,yerr=None,xerr=None)

				thefigure = sc[0].get_figure()
#				thefigure.set_figsize_inches((6,4))
#				fig = sc.get_figure()
				thefigure.set_figsize_inches(figsize)				
				theaxes = thefigure.get_axes()
				theaxes[0].yaxis.set_major_formatter(FormatStrFormatter('%d'))					  
				pylab.xticks(ind, allx, rotation=45, fontsize=8)
				#pylab.xlim(-width, len(ind))
			else:
				ally = data['y']
				sc = pylab.scatter(allx, ally)
	else:
		dotcolor = ['b', 'g', 'r', 'c', 'm', 'y','w', 'k', 'c']
		allcolor=['b', 'g', 'r', 'c', 'm', 'y', '#00ff00', '#800000', '#000080', '#808000', '#800080', '#c0c0c0', '#008080', '#7cfc00', '#cd5c5c', '#ff69b4', '#deb887', '#a52a2a', '#5f9ea0', '#6495ed', '#b8890b', '#8b008b', '#f08080', '#f0e68c', '#add8e6', '#ffe4c4', '#deb887', '#d08b8b', '#bdb76b', '#556b2f', '#ff8c00', '#8b0000', '#8fbc8f', '#ff1493', '#696969', '#b22222', '#daa520', '#9932cc', '#e9967a', '#00bfff', '#1e90ff', '#ffd700', '#adff2f', '#00ffff', '#ff00ff', '#808080', 'w', 'k', 0.3, 0.6, 0.9]

		#allcolor = colors.getColors()
		allshape= ['o', 's', '^', '>', 'v', '<', 'd', 'p', 'h', '8']
		pylab.hold(False)  


		if data == [] or len(data) == 0:
					page = "<h2>No Result Found! Please change your query and try again</h2>"
					return page
		i = 0
		labels = []
		thekeys = []

		if thequery.find('histogram') >= 0:
				   k = 0
				   allx = data['x']
				   ind = range(len(allx))
				   width = 1
				   #ax = pylab.subplot(111)					  

				   #yoff = pylab.arange([0.0] * len(allx))
				   yoff = []
				   for theone in allx:
					   yoff.append(0.0)
				   allsc = []
				   ykeys = []
				   for thekey in data.keys():
					   if type(thekey) == int:
						   ykeys.append(thekey)
				   ykeys.sort()
				   pylab.hold(False) 
				   for thekey in ykeys: 
					  if type(thekey) == int:
						   myY = data[thekey]
						   sc = pylab.bar(ind, myY, width, bottom=yoff, color=allcolor[k%len(allcolor)],yerr=None,xerr=None)
						   thefigure = sc[0].get_figure()
						   theaxes = thefigure.get_axes()
						   theaxes[0].yaxis.set_major_formatter(FormatStrFormatter('%d'))
						   i = 0
						   tmp = []
						   for theY in myY:
							   tmp.append(yoff[i])
							   yoff[i] += theY
							   i += 1
						   ally.append(tmp)
						   k += 1
						   if k>0:
								   pylab.hold(True)
						   allsc.append(sc[0])
				   pylab.hold(False) 
				   ally.append(yoff)
				   newkeys = []
				   for thekey in data['keys']:
					   newkeys.append(str(thekey))
				   pylab.legend(allsc, newkeys, loc=2, shadow=0, prop=font_manager.FontProperties(size='small', weight=500), handletextsep=0.005, axespad=0.01, pad=0.01, labelsep=0.001, handlelen=0.02)
				   #newind = range(len(allx)+1)
				   pylab.xticks(ind, allx, rotation=45, fontsize=8)
				   pylab.xlim(-width, len(ind)+1)

		else:
			pylab.hold(False)
			for thekey in data.keys():
				if i>0:
					 pylab.hold(True) 
				if groupby == 1:
					datax = data[thekey]['x']
					datay = data[thekey]['y']
				else:
					datax = data['x']
					datay = data['y']
				allx.extend(datax)
				ally.extend(datay)
				label = str(dotcolor[i%8]) + '--' + allshape[i/8]
				lines = pylab.plot([datax[0]], [datay[0]], label, markersize=5)
				sc = pylab.scatter(datax, datay, c=dotcolor[i%len(dotcolor)], marker=allshape[i/8], s=20)

				fig = sc.get_figure()
				fig.set_figsize_inches(figsize)
				
				labels.append(lines)
				thekeys.append(str(thekey))

				i += 1
			pylab.hold(False) 
			try:
				pylab.legend(labels, thekeys, numpoints=2, shadow=0, prop=font_manager.FontProperties(size='small'), handletextsep=0.01, axespad=0.005, pad=0.005, labelsep=0.001, handlelen=0.01)
			except:
				pass




	pylab.xlabel(L['xlabel'])
	pylab.ylabel(L['ylabel'])

	t = str(time.time())
	rand = str(random.randint(0,100000))
	tempfile = "/graph/t" + t + ".r" + rand + ".png"
	pylab.savefig("tweb" + tempfile)				

	return tempfile
		
	





def main():
	# def plot(xparam, yparam, subset=None, groupby=None, grouptype="recorddef", rectypes=None, cutoff=100):
	parser = optparse.OptionParser()
	parser.add_option("--grouptype",type="string", default="recorddef", help="Group Type -- use groupby for argument")
	parser.add_option("--groupby", type="string")
	parser.add_option("--childof", type="int", help="Child of")
	parser.add_option("--cutoff", type="int", default=100, help="Discard groups with less than cutoff items")
	(options, args) = parser.parse_args(sys.argv[2:])
	
	if len(args) < 1:
		parser.error("X and Y parameters required")

	plot(xparam=args[0], yparam=args[1], groupby=options.groupby, grouptype=options.grouptype, cutoff=options.cutoff, childof=options.childof)



if __name__ == "__main__":
	main()
	




