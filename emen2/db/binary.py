# $Id: binary.py,v 1.59 2013/05/01 03:16:07 irees Exp $
"""Database support for Binary attachments."""

import time
import re
import traceback
import math
import os

# For file writing
import shutil
import hashlib
import cStringIO
import tempfile

# EMEN2 imports
import emen2.db.dataobject
import emen2.db.config
import emen2.db.exceptions


class Binary(emen2.db.dataobject.BaseDBObject):
    """Binary file stored on disk and managed by EMEN2.

    Provides following attributes:
        filename, record, md5, filesize, compress, filepath

    The Binary name has a specific format, bdo:YYYYMMDDXXXXX, where YYYYMMDD is
    date format and XXXXX is 5-char hex ID code of file for the day.

    The filename attribute is the original name of the uploaded file. The
    filesize attribute is the uncompressed size of the file, and the md5
    attribute is the MD5 checksum of the uncompressed file. The filename may be
    changed by an owner after a Binary is committed, but the contents (filesize
    and md5) cannot be changed. Files may be compressed after they have been
    created; in this case, the compress param will specify the compression
    scheme (gzip, bz2, etc.) and filesize_compress and md5_compress will have
    values for the compressed file.

    File names are checked to prevent illegal characters, and names such as "."
    and invalid file names on some platforms ("COM", "NUL", etc.).

    Binaries are generally associated with a Record, stored in the record
    attribute. Read permission on a Binary requires either ownership of the
    item, or read permission on the associated Record. The owner of the Binary
    can change which Record is associated.

    When a Binary is retrieved from the database, the filepath property will
    be accessible. This points to the physical file on disk containing the data.

    These BaseDBObject methods are extended:

        init            Set attributes
        setContext        Check read permissions and bind Context
        validate        Check required attributes

    And the following method is provided:

        parse            Parse name

    :attr filename: File name
    :attr filesize: Size of the uncompressed file
    :attr md5: MD5 checksum of the uncompressed file
    :attr filesize_compress: Size of the compressed file
    :attr md5_compress: MD5 checksum of the compressed file
    :attr compress: File is gzip compressed
    :attr record: Associated Record
    :property filepath: Path to the file on disk
    """

    attr_public = emen2.db.dataobject.BaseDBObject.attr_public | set(["filepath", "filename", "record", "compress", "filesize", "md5", "filesize_compress", "md5_compress"])
    attr_protected = emen2.db.dataobject.BaseDBObject.attr_protected | set(["compress", "filesize", "md5", "filesize_compress", "md5_compress"])
    filepath = property(lambda x:x._filepath)

    def init(self, d):
        self.__dict__['filename'] = None
        self.__dict__['record'] = None
        self.__dict__['md5'] = None
        self.__dict__['filesize'] = None
        self.__dict__['compress'] = False
        self.__dict__['filesize_compress'] = None
        self.__dict__['md5_compress'] = None
        self.__dict__['_filepath'] = None
        self._filepath = None

    ##### DBObject interface #####

    def setContext(self, ctx):
        super(Binary, self).setContext(ctx=ctx)
        self.__dict__['_filepath'] = self.parse(self.name).get('filepath')
        if self.isowner():
            return True
        if self.record is not None:
            rec = self._ctx.db.record.get(self.record, filt=False)

    # filepath is set during setContext, and discarded during commit (todo)
    def _set_filepath(self, key, value):
        return set()

    # These immutable attributes only ever be set for a new Binary, before commit
    def _set_md5(self, key, value):
        if self.name:
            raise emen2.db.exceptions.ValidationError, "Cannot change a Binary's file attachment"
        return self._set(key, value, self.isowner())

    def _set_md5_compress(self, key, value):
        if self.name:
            raise emen2.db.exceptions.ValidationError, "Cannot change a Binary's file attachment"
        return self._set(key, value, self.isowner())

    def _set_compress(self, key, value):
        if self.name:
            raise emen2.db.exceptions.ValidationError, "Cannot change a Binary's file attachment"
        return self._set(key, value, self.isowner())

    def _set_filesize(self, key, value):
        if self.name:
            raise emen2.db.exceptions.ValidationError, "Cannot change a Binary's file attachment"
        return self._set(key, value, self.isowner())

    def _set_filesize_compress(self, key, value):
        if self.name:
            raise emen2.db.exceptions.ValidationError, "Cannot change a Binary's file attachment"
        return self._set(key, value, self.isowner())

    # These can be changed normally
    def _set_filename(self, key, value):
        # Sanitize filename.. This will allow unicode characters,
        #    and check for reserved filenames on linux/windows
        value = unicode(value)
        value = "".join([i for i in value if i.isalpha() or i.isdigit() or i in '.()-=_'])
        if value.upper() in ['..', '.', 'CON', 'PRN', 'AUX', 'NUL',
                                    'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
                                    'COM6', 'COM7', 'COM8', 'COM9', 'LPT1',
                                    'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6',
                                    'LPT7', 'LPT8', 'LPT9']:
            value = u"renamed."+value
        return self._set(key, value, self.isowner())

    def _set_record(self, key, value):
        return self._set(key, value, self.isowner())

    def validate(self):
        # Validate
        if not all([self.filename, self.md5, self.filesize != None]):
            raise emen2.db.exceptions.ValidationError, "Filename, filesize, and MD5 checksum are required"

    ##### Utility methods #####

    # Write contents to a temporary file.
    def writetmp(self, filedata=None, fileobj=None, basepath=None, suffix="upload"):
        '''Write to temporary storage, and calculate size/md5.
        :return: Temporary file path, the file size, and an md5 digest.
        '''
        if filedata:
            fileobj = cStringIO.StringIO(filedata)
        if not fileobj:
            raise ValueError, "No data to write to temporary file."

        fileobj.seek(0)

        # In narrow circumstances, this might not be the same filesystem
        # as the final file destination. So use a higher level tool like
        # shutil to rename the file, instead of just os.rename.
        basepath = basepath or self.parse('')['basepath']

        if not os.path.exists(basepath):
            os.makedirs(basepath)
            
        (fd, tmpfile) = tempfile.mkstemp(dir=basepath, suffix='.%s'%suffix)

        m = hashlib.md5()
        filesize = 0
        # Copy to the output file, updating md5 and size
        with os.fdopen(fd, "w+b") as f:
            for line in fileobj:
                f.write(line)
                m.update(line)
                filesize += len(line)

        md5sum = m.hexdigest()
        emen2.db.log.info("Wrote file: %s, filesize: %s, md5sum: %s"%(tmpfile, filesize, md5sum))

        # Update filesize/md5
        self.__dict__['filesize'] = filesize
        self.__dict__['md5'] = md5sum
        return tmpfile

    @staticmethod
    def parse(bdokey, counter=None):
        """Parse a 'bdo:2010010100001' type identifier into constituent parts
        and resolve location in the filesystem."""

        prot, _, bdokey = (bdokey or "").rpartition(":")
        if not prot:
            prot = "bdo"

        # ian: todo: implement other BDO protocols, e.g. references to uris
        if prot not in ["bdo"]:
            raise Exception, "Invalid binary protocol: %s"%prot

        if bdokey:
            # Now process; must be 14 chars long..
            year = int(bdokey[:4])
            mon = int(bdokey[4:6])
            day = int(bdokey[6:8])
            if counter == None:
                counter = int(bdokey[9:13],16)
        else:
            # Timestamps are now in ISO8601 format
            # e.g.: "2011-10-16T02:00:00+00:00"
            bdokey = emen2.db.database.utcnow()
            year = int(bdokey[:4])
            mon = int(bdokey[5:7])
            day = int(bdokey[8:10])
            counter = counter or 0

        # YYYYMMDD
        datekey = "%04d%02d%02d"%(year, mon, day)
        datedir = os.path.join('%04d'%year, '%02d'%mon, '%02d'%day)

        # Get the binary storage paths from config
        # Find the last item matching the current date
        binarypaths = emen2.db.config.get('paths.binary')
        bp = [x for x in sorted(binarypaths.keys()) if str(x)<=datekey]

        # Resolve the parsed bdo key to a directory (basepath) and file (filepath)
        basepath = os.path.join(binarypaths[bp[-1]], datedir)
        filepath = os.path.join(basepath, "%05X"%counter)
        
        # ... same for previewpath
        previewpaths = emen2.db.config.get('paths.preview')
        pp = [x for x in sorted(previewpaths.keys()) if str(x)<=datekey]
        previewpath = os.path.join(previewpaths[pp[-1]], datedir, "%05X"%counter)

        # The BDO name (bdo:YYYYMMDDXXXXX)
        name = "%s:%s%05X"%(prot, datekey, counter)

        return {
            "prot":prot,
            "year":year,
            "mon":mon,
            "day":day,
            "counter":counter,
            "datekey":datekey,
            "basepath":basepath,
            "filepath":filepath,
            "previewpath":previewpath,
            "name":name
            }


__version__ = "$Revision: 1.59 $".split(":")[1][:-1].strip()