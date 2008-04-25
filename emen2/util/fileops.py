import os
import os.path
import codecs
import g

import listops

def openreadclose(path):
    tmp = codecs.open(path, 'r', 'utf-8')
    try:
        result = tmp.read()
    finally:
        tmp.close()
    return result
        
def walk_path(extension, cb):
    def res(pathname):
        for pwd in os.walk(pathname):
            for fil in pwd[2]:
                item=os.path.splitext(os.path.basename(fil))
                cb(pwd, pathname, extension, item)
    return res
