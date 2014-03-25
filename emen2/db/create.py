"""Create a new database."""

if __name__ == "__main__":
    import emen2.db
    import emen2.db.config
    opts = emen2.db.config.DBOptions()

    opts.add_argument("--rootemail", help="Root email")
    opts.add_argument("--rootpw", help="Root password")
    
    args = opts.parse_args()
    db = emen2.db.opendb(admin=True)
    emen2.db.database.setup(db=db, rootpw=args.rootpw, rootemail=args.rootemail)
