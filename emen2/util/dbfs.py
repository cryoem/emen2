#!/usr/bin/env python

#    Copyright (C) 2006  Andrew Straw  <strawman@astraw.com>
#
#    This program can be distributed under the terms of the GNU LGPL.
#    See the file COPYING.
#

import os, stat, errno
# pull in some spaghetti to make this stuff work without fuse-py being installed
try:
    import _find_fuse_parts
except ImportError:
    pass
import fuse
from fuse import Fuse
from emen2.util.db_manipulation import DBTree
from emen2.test import *


if not hasattr(fuse, '__version__'):
    raise RuntimeError, \
        "your fuse-py doesn't know of fuse.__version__, probably it's too old."

fuse.fuse_python_api = (0, 2)

hello_path = '/hello'
hello_str = 'Hello World!\n'

class MyStat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0

class HelloFS(Fuse):
    dbtree = DBTree(db, ctxid, None)
    
    def getattr(self, path):
        st = MyStat()
        if path == '/':
            st.st_mode = stat.S_IFDIR | 0755
            st.st_nlink = 2
            return st
        
        path = path[1:]
        item = self.dbtree.getrecord(self.dbtree.get_path_id(filter(bool,path.split('/'))))
        if len(item) > 1:
            return -errno.EINVAL
        elif len(item) < 1:
            return -errno.ENOENT
        else:
            item = item.pop()
            st.st_mode = stat.S_IFDIR | 0755
            st.st_ino = item.recid
            st.st_nlink = 1
            st.st_size = len(str(item))
        return st

    def readdir(self, path, offset):
        path=path[1:]
        for r in  self.dbtree.get_children(filter(bool, path.split('/'))):
            x = self.dbtree.getrecord(r)
            index = x.get('indexby', str(x.recid)) 
            yield fuse.Direntry(str(index))

    def open(self, path, flags):
        item = self.dbtree.getrecord(self.dbtree.get_path_id(path.split('/')))
        if item == set([]):
            return -errno.ENOENT
        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (flags & accmode) != os.O_RDONLY:
            return -errno.EACCES

    def read(self, path, size, offset):
        path = path[1:]
        item = self.dbtree.getrecord(self.dbtree.get_path_id(path.split('/')))
        if not item:
            return -errno.ENOENT
        text = str(item)
        slen = len(text)
        if offset < slen:
            if offset + size > slen:
                size = slen - offset
            buf = text[offset:offset+size]
        else:
            buf = ''
        return buf

def main():
    usage="""
Userspace hello example

""" + Fuse.fusage
    server = HelloFS(version="%prog " + fuse.__version__,
                     usage=usage,
                     dash_s_do='setsingle')

    server.parse(errex=1)
    server.main()
    Database.DB_cleanup()

if __name__ == '__main__':
    main()
