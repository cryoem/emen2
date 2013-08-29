if __name__ == "__main__":
    import emen2.db
    import emen2.db.config
    opts = emen2.db.config.DBOptions()
    args = opts.parse_args()
    db = emen2.db.opendb(admin=True)

