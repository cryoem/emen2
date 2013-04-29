import os
import sys
import time
import shutil
import collections

# Berkeley DB
# Note: the 'bsddb' module is not sufficient.
import bsddb3

# EMEN2 Config
import emen2.db.config
import emen2.db.log
from emen2.db.exceptions import *

# EMEN2 DBObjects
import emen2.db.dataobject
import emen2.db.record
import emen2.db.binary
import emen2.db.paramdef
import emen2.db.recorddef
import emen2.db.user
import emen2.db.context
import emen2.db.group

# ian: todo: move this to EMEN2DBEnv
DB_CONFIG = """\
# Don't touch these
set_data_dir data
set_lg_dir journal
set_lg_regionmax 1048576
set_lg_max 8388608
set_lg_bsize 2097152
"""


##### EMEN2 Database Environment #####

class EMEN2DBEnv(object):
    """EMEN2 Database Environment."""

    def __init__(self, path=None, snapshot=False):
        """
        :keyword path: Directory containing environment.
        :keyword snapshot: Use Berkeley DB Snapshot (Multiversion Concurrency Control) for read transactions
        """
        
        # Database environment directory
        self.path = path
        self.snapshot = snapshot or emen2.db.config.get('bdb.snapshot')
        self.cachesize = emen2.db.config.get('bdb.cachesize') * 1024 * 1024l

        # Make sure the DB_CONFIG is present.
        configpath = os.path.join(self.path, "DB_CONFIG")
        if not os.path.exists(configpath):
            emen2.db.log.info("Copying default DB_CONFIG file: %s"%configpath)
            f = open(configpath, "w")
            f.write(DB_CONFIG)
            f.close()

        # Databases
        self.keytypes =  {}

        # Pre- and post-commit actions.
        # These are used for things like renaming files during the commit phase.
        # TODO: The details of this are highly likely to change,
        #     or be moved to a different place.
        self._txncbs = collections.defaultdict(list)

        # Open DBEnv and main tables.
        self.dbenv = self.open()
        self.init()

    def open(self):
        """Open the Database Environment."""
        emen2.db.log.info("Opening database environment: %s"%self.path)
        dbenv = bsddb3.db.DBEnv()

        if self.snapshot:
            dbenv.set_flags(bsddb3.db.DB_MULTIVERSION, 1)
        
        txncount = (self.cachesize / 4096) * 2
        if txncount > 1024*128:
            txncount = 1024*128
            
        dbenv.set_cachesize(0, self.cachesize)
        dbenv.set_tx_max(txncount)
        dbenv.set_lk_max_locks(300000)
        dbenv.set_lk_max_lockers(300000)
        dbenv.set_lk_max_objects(300000)

        flags = 0
        flags |= bsddb3.db.DB_CREATE
        flags |= bsddb3.db.DB_INIT_MPOOL
        flags |= bsddb3.db.DB_INIT_TXN
        flags |= bsddb3.db.DB_INIT_LOCK
        flags |= bsddb3.db.DB_INIT_LOG
        flags |= bsddb3.db.DB_THREAD
        dbenv.open(self.path, flags)
        return dbenv

    def init(self):
        # Authentication. These are not public.
        self._context = emen2.db.btrees.DBODB(keytype='context', dbenv=self, dataclass=emen2.db.context.Context)

        # Main database items. These are available in the public API.
        self.add_db(emen2.db.btrees.RelateDB, keytype='paramdef', dataclass=emen2.db.paramdef.ParamDef)
        self.add_db(emen2.db.btrees.RelateDB, keytype='recorddef', dataclass=emen2.db.recorddef.RecordDef)

        # Finish porting these to generic DB
        self.add_db(emen2.db.group.GroupDB, keytype='group')
        self.add_db(emen2.db.user.UserDB, keytype='user')
        self.add_db(emen2.db.user.NewUserDB, keytype='newuser')
        self.add_db(emen2.db.binary.BinaryDB, keytype="binary")
        self.add_db(emen2.db.record.RecordDB, keytype="record") 

    def add_db(self, cls, **kwargs):
        """Add a BTree."""
        db = cls(dbenv=self, **kwargs)
        self.keytypes[db.keytype] = db

    # ian: todo: make this nicer.
    def close(self):
        """Close the Database Environment"""
        for k,v in self.keytypes.items():
            v.close()
        self.dbenv.close()

    def __getitem__(self, key, default=None):
        """Pass dictionary gets to self.keytypes."""
        return self.keytypes.get(key, default)


    ##### Log archive #####

    def journal_archive(self, remove=True, checkpoint=True, txn=None):
        """Archive completed log files.

        :keyword remove: Remove the log files after moving them to the backup location
        :keyword checkpoint: Run a checkpoint first; this will allow more files to be archived
        """
        outpath = emen2.db.config.get('paths.journal_archive')

        if checkpoint:
            emen2.db.log.info("Log Archive: Checkpoint")
            self.dbenv.txn_checkpoint()

        archivefiles = self.dbenv.journal_archive(bsddb3.db.DB_ARCH_ABS)

        emen2.db.log.info("Log Archive: Preparing to move %s completed log files to %s"%(len(archivefiles), outpath))

        if not os.access(outpath, os.F_OK):
            os.makedirs(outpath)

        outpaths = []
        for archivefile in archivefiles:
            dest = os.path.join(outpath, os.path.basename(archivefile))
            emen2.db.log.info('Log Archive: %s -> %s'%(archivefile, dest))
            shutil.move(archivefile, dest)
            outpaths.append(dest)

        return outpaths
  
        
    ##### Transaction management #####

    def newtxn(self, write=False):
        """Start a new transaction.
        
        :keyword write: Transaction will be likely to write data; turns off Berkeley DB Snapshot
        :return: New transaction
        """
        flags = bsddb3.db.DB_TXN_SNAPSHOT
        if write:
            flags = 0

        txn = self.dbenv.txn_begin(flags=flags)
        # emen2.db.log.msg('TXN', "NEW TXN, flags: %s --> %s"%(flags, txn))
        return txn

    def txncheck(self, txn=None, write=False):
        """Check a transaction status, or create a new transaction.

        :keyword txn: An existing open transaction
        :keyword write: See newtxn
        :return: Open transaction
        """
        if not txn:
            txn = self.newtxn(write=write)
        return txn

    def txnabort(self, txn):
        """Abort transaction.

        :keyword txn: An existing open transaction
        :exception: KeyError if transaction was not found
        """
        # emen2.db.log.msg('TXN', "TXN ABORT --> %s"%txn)
        txnid = txn.id()
        self._txncb(txnid, 'abort', 'before')
        txn.abort()
        self._txncb(txnid, 'abort', 'after')
        self._txncbs.pop(txnid, None)

    def txncommit(self, txn):
        """Commit a transaction.

        :param txn: An existing open transaction
        :exception: KeyError if transaction was not found
        """
        # emen2.db.log.msg('TXN', "TXN COMMIT --> %s"%txn)
        txnid = txn.id()
        self._txncb(txnid, 'commit', 'before')
        txn.commit()
        self._txncb(txnid, 'commit', 'after')
        self._txncbs.pop(txnid, None)

    def checkpoint(self, txn=None):
        """Checkpoint the database environment."""
        return self.dbenv.txn_checkpoint()

    def txncb(self, txn, action, args=None, kwargs=None, condition='commit', when='before'):
        if when not in ['before', 'after']:
            raise ValueError, "Transaction callback 'when' must be before or after"
        if condition not in ['commit', 'abort']:
            raise ValueError, "Transaction callback 'condition' must be commit or abort"
        item = [condition, when, action, args or [], kwargs or {}]
        self._txncbs[txn.id()].append(item)

    # This is still being developed. Do not touch.
    def _txncb(self, txnid, condition, when):
        # Note: this takes txnid, not a txn. This
        # is because txn.id() is null after commit.
        actions = self._txncbs.get(txnid, [])
        for c, w, action, args, kwargs in actions:
            if w == when and c == condition:
                if action == 'rename':
                    self._txncb_rename(*args, **kwargs)
                elif action == 'email':
                    self._txncb_email(*args, **kwargs)
                elif action == 'thumbnail':
                    self._txncb_thumbnail(*args, **kwargs)
    
    def _txncb_rename(self, source, dest):
        emen2.db.log.info("Renaming file: %s -> %s"%(source, dest))
        try:
            shutil.move(source, dest)
        except Exception, e:
            emen2.db.log.error("Couldn't rename file %s -> %s"%(source, dest))

    def _txncb_email(self, *args, **kwargs):
        try:
            sendmail(*args, **kwargs)
        except Exception, e:
            emen2.db.log.error("Couldn't send email: %s"%e)
            
    def _txncb_thumbnail(self, bdo):
        try:
            emen2.db.handlers.thumbnail_from_binary(bdo, wait=False)
        except Exception, e:
            emen2.db.log.error("Couldn't start thumbnail builder")
    
