import traceback
import re
import os
import pickle 
import time
import random
import optparse
import sys
import collections

try:
	import matplotlib.backends.backend_agg
	import matplotlib.figure
except:
	g.log("No matplotlib, plotting will fail")





	


def main():
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
	




