# $Id$

# Temporary fix --
import jsonrpc.jsonutil
def jsonencode(*args, **kwargs):
    return jsonrpc.jsonutil.encode(*args, **kwargs).replace('/', r'\/')