"""EMEN2: An extesible electronic lab notebook and database."""

def opendb(**kwargs):
    """Open a database. Shorter alias to emen2.db.database.opendb."""
    import emen2.db.database
    return emen2.db.database.opendb(**kwargs)
