# $Id: __main__.py,v 1.6 2012/09/14 06:26:25 irees Exp $

if __name__ == "__main__":
    # Start the web server directly
    import emen2.web.server
    emen2.web.server.start_standalone()

__version__ = "$Revision: 1.6 $".split(":")[1][:-1].strip()
