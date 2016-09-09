# $Id: __init__.py,v 1.35 2013/05/14 15:52:32 irees Exp $
"""EMEN2: An extesible electronic lab notebook and database."""

def opendb(**kwargs):
    """Open a database."""
    # Import the config first and parse
    import emen2.db.config
    cmd = emen2.db.config.UsageParser()
    import emen2.db.database
    return emen2.db.database.opendb(**kwargs)


def opendbwithopts(optclass, **kwargs):
    import emen2.db.config
    cmd = emen2.db.config.UsageParser(optclass=optclass)
    import emen2.db.database
    return cmd, emen2.db.database.opendb(**kwargs)
        

__version__ = "$Revision: 1.35 $".split(":")[1][:-1].strip()