# $Id: rpc.py,v 1.1 2012/09/17 22:00:10 irees Exp $

if __name__ == "__main__":
    # Start the web server directly
    import emen2.web.server
    emen2.web.server.start_rpc()

__version__ = "$Revision: 1.1 $".split(":")[1][:-1].strip()
