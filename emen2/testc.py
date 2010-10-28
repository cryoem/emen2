# $Id$

# Some imports that are frequently useful..
import os
import sys
import collections
import operator
import time
import urllib
import subprocess
import emen2.db.admin
db = emen2.db.admin.opendb()

# print db.query(c=[['rectype','==','project'], ['creator','==','ianrees'], ['name_project','contains','Test']])
# print db.query(c=[['rectype','==','publication*'], ['creator', '==', 'ianrees']])

__version__ = "$Revision$".split(":")[1][:-1].strip()
