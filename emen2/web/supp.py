raise Exception, "Deprecated"

# move these two functions elsewhere...



from sets import Set
import re
import os
import pickle
from operator import itemgetter
import time

from emen2.emen2config import *
from emen2 import Database
		
		
		
		
		

# taken from http://rightfootin.blogspot.com/2006/09/more-on-python-flatten.html
# def flatten(l, ltypes=(list, tuple)):
#     ltype = type(l)
#     l = list(l)
#     i = 0
#     while i < len(l):
#         while isinstance(l[i], ltypes):
#             if not l[i]:
#                 l.pop(i)
#                 i -= 1
#                 break
#             else:
#                 l[i:i + 1] = l[i]
#         i += 1
#     return ltype(l)
# 
# 
# 
# 
# def usertype(pd):
# 	return pd.vartype in ["user","userlist"]
# def binarytype(pd):
# 	return pd.vartype in ["binary","binaryimage"]




