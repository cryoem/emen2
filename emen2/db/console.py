#!/usr/bin/env python
# This will become an IPython based EMEN2 console.

if __name__ == "__main__":
    import emen2.db
    import emen2.db.config
    opts = emen2.db.config.DBOptions()
    args = opts.parse_args()
    db = emen2.db.opendb(admin=True)
    