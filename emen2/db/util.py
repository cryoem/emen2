# $Id: util.py,v 1.1 2012/10/19 08:19:34 irees Exp $

# Temporary fix --
import jsonrpc.jsonutil
def jsonencode(*args, **kwargs):
    return jsonrpc.jsonutil.encode(*args, **kwargs).replace('/', r'\/')