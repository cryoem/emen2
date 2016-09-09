# $Id: __main__.py,v 1.14 2012/07/28 06:31:17 irees Exp $

if __name__ == "__main__":
    import emen2.db
    db = emen2.db.opendb(admin=True)

__version__ = "$Revision: 1.14 $".split(":")[1][:-1].strip()
