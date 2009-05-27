import fnmatch
import os
import os.path
import codecs
#import g

import listops

def openreadclose(path):
    tmp = codecs.open(path, 'r', 'utf-8')
    try:
        result = tmp.read()
    finally:
        tmp.close()
    return result
        
def walk_path(extension, cb):
    def res(pathname, *args, **kwargs):
        for pwd in os.walk(pathname):
            for fil in pwd[2]:
                item=os.path.splitext(os.path.basename(fil))
                cb(pwd, pathname, extension, item, *args, **kwargs)
    return res

#from Python Cookbook http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/499305
def locate(pattern, root=os.curdir):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.'''
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)
            
