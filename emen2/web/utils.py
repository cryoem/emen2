#standard imports
import re
import os
from operator import itemgetter
import time
import math
import copy

#standard emen2 imports
from emen2.emen2config import *
import emen2.globalns
g = emen2.globalns.GlobalNamespace('')


#special imports
import demjson


###### ian
from emen2.TwistSupport_html.public.views import View, Page
from emen2.TwistSupport_html.publicresource import PublicView



# from: http://basicproperty.sourceforge.net
def flatten(l, ltypes=(set, list, tuple)):
    ltype = type(l)
    l = list(l)
    i = 0
    while i < len(l):
        while isinstance(l[i], ltypes):
            if not l[i]:
                l.pop(i)
                i -= 1
                break
            else:
                l[i:i + 1] = l[i]
        i += 1
    return ltype(l)
