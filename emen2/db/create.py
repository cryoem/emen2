"""Create a new database."""
import emen2.db.config

class CreateOptions(emen2.db.config.DBOptions):
    def parseArgs(self):
        pass

if __name__ == "__main__":
    import emen2.db
    db = emen2.db.opendb(admin=True)
    emen2.db.database.setup(db=db)
            
        