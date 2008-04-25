import emen2.util.db_manipulation

class Context(object):
    def __init__(self, cur_dir, db, ctxid, host=None):
        self.__tree = emen2.util.db_manipulation.DBTree(db, ctxid, host, cur_dir)