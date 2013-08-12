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

# These filenames are not allowed on Windows.
# Additional filename checking is done by the 
# security.filename_blacklist and security.filename_whitelist.
WINDOWS_DEVICE_FILENAMES = ['CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
    'COM6', 'COM7', 'COM8', 'COM9', 'LPT1',
    'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6',
    'LPT7', 'LPT8', 'LPT9']

def parse(bdokey, counter=None):
    """Parse a 'bdo:2010010100001' type identifier into parts and
    find location in the filesystem."""

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

# Write contents to a temporary file.
def writetmp(filedata=None, fileobj=None, basepath=None, suffix="upload"):
    '''Write to temporary storage, and calculate size/md5.
    :return: Temporary file path, the file size, and an md5 digest.
    '''
    if filedata:
        fileobj = cStringIO.StringIO(filedata)
    if not fileobj:
        raise ValueError, "No data to write to temporary file."

    # Seek to the beginning of the fileobj.
    fileobj.seek(0)

    # Check that the directory for this day exists.
    basepath = basepath or parse('')['basepath']
    if not os.path.exists(basepath):
        os.makedirs(basepath)

    # Open the temporary file
    (fd, tmpfile) = tempfile.mkstemp(dir=basepath, suffix='.%s'%suffix)

    # Copy to the output file, updating md5 and size
    m = hashlib.md5()
    filesize = 0
    with os.fdopen(fd, "w+b") as f:
        for line in fileobj:
            f.write(line)
            m.update(line)
            filesize += len(line)
    md5sum = m.hexdigest()
    emen2.db.log.info("Wrote file: %s, filesize: %s, md5sum: %s"%(tmpfile, filesize, md5sum))
    return filesize, md5sum, tmpfile

class Binary(emen2.db.dataobject.BaseDBObject):
    """Binary file stored on disk and managed by EMEN2.

    Provides following attributes:
        filename, record, md5, filesize, compress, filepath

    The Binary name has a specific format, bdo:YYYYMMDDXXXXX, where YYYYMMDD is
    date format and XXXXX is 5-char hex ID code of file for the day.

    The filename attribute is the original name of the uploaded file. The
    filesize attribute is the size of the file, and the md5 attribute is the
    MD5 checksum of the file. The filename may be changed by an owner after a
    Binary is committed, but the contents (filesize and md5) cannot be changed.
    If the file is compressed, compress will be set to the compression format
    (gz, bz2).
    
    Filenames must be alphanumeric or . ( ) - = _. Certain illegal filenames
    are not allowed (COM, NUL, etc), and filenames cannot begin with a dot. The
    configuration settings security.filename_blacklist and
    security.filename_whitelist are also applied. These are lists of regular
    expressions checked against the filename. Any hit in the blacklist will
    raise an error. If a whitelist is specified, at least one hit in the
    whitelist is required. See also: _validate_filename()

    Binaries are generally associated with a Record, stored in the record
    attribute. Read permission on a Binary requires either ownership of the
    item, or read permission on the associated Record. The owner of the Binary
    can change which Record is associated.

    When a Binary is retrieved from the database, the filepath property will
    be accessible. This points to the physical file on disk containing the data.

    These BaseDBObject methods are overridden:

        init            Set attributes
        setContext      Check read permissions and bind Context
        validate        Check required attributes

    :attr filename: File name
    :attr filesize: Size of the uncompressed file
    :attr md5: MD5 checksum of the uncompressed file
    :attr compress: File is gzip compressed
    :attr record: Associated Record
    :property filepath: Path to the file on disk
    """

    attr_public = emen2.db.dataobject.BaseDBObject.attr_public | set(["filepath", "filename", "record", "compress", "filesize", "md5"])
    filepath = property(lambda x:x._filepath)

    def init(self, d):
        super(Binary, self).init(d)        
        self.__dict__['filename'] = None
        self.__dict__['record'] = None
        self.__dict__['md5'] = None
        self.__dict__['filesize'] = None
        self.__dict__['compress'] = False
        self.__dict__['filesize_compress'] = None
        self.__dict__['md5_compress'] = None
        self.__dict__['_filepath'] = None
        self._filepath = None

    def setContext(self, ctx):
        super(Binary, self).setContext(ctx=ctx)
        self.__dict__['_filepath'] = parse(self.name).get('filepath')
        if self.isowner():
            return True
        if self.record is not None:
            rec = self._ctx.db.record.get(self.record, filt=False)

    def validate(self):
        # Validate
        if not all([self.filename, self.md5, self.filesize != None]):
            raise emen2.db.exceptions.ValidationError, "filename, filesize, and MD5 checksum are required"

    ##### Setters #####
    
    # filepath is set during setContext, and discarded during commit (todo)
    def _set_filepath(self, key, value):
        return set()

    # These immutable attributes only ever be set for a new Binary, before commit
    def _set_md5(self, key, value):
        if not self.isnew():
            raise emen2.db.exceptions.ValidationError, "Cannot change a Binary's file attachment"
        return self._set(key, value, self.isowner())

    def _set_md5_compress(self, key, value):
        if not self.isnew():
            raise emen2.db.exceptions.ValidationError, "Cannot change a Binary's file attachment"
        return self._set(key, value, self.isowner())

    def _set_compress(self, key, value):
        if not self.isnew():
            raise emen2.db.exceptions.ValidationError, "Cannot change a Binary's file attachment"
        return self._set(key, value, self.isowner())

    def _set_filesize(self, key, value):
        if not self.isnew():
            raise emen2.db.exceptions.ValidationError, "Cannot change a Binary's file attachment"
        return self._set(key, value, self.isowner())

    def _set_filesize_compress(self, key, value):
        if not self.isnew():
            raise emen2.db.exceptions.ValidationError, "Cannot change a Binary's file attachment"
        return self._set(key, value, self.isowner())

    # These can be changed normally
    def _set_filename(self, key, value):
        # Sanitize filename.. This will allow unicode characters,
        #    and check for reserved filenames on linux/windows
        value = unicode(value)
        value = self._validate_filename(value)
        return self._set(key, value, self.isowner())

    def _set_record(self, key, value):
        return self._set(key, value, self.isowner())
        
    def _validate_filename(self, value):
        """
        """
        # ... make this a regex.
        value = "".join([i for i in value if i.isalpha() or i.isdigit() or i in '.()-=_'])

        # Check for illegal Windows filenames.
        if value.upper() in WINDOWS_DEVICE_FILENAMES:
            raise self.error("Disallowed filename: %s"%value)

        # Check the filename whitelist / blacklist settings.
        blacklist = emen2.db.config.get('security.filename_blacklist')
        if blacklist and any([re.search(i, value) for i in blacklist]):
            raise self.error("Disallowed filename: %s"%value)
        whitelist = emen2.db.config.get('security.filename_whitelist')
        if whitelist and not any([re.search(i, value) for i in whitelist]):
            raise self.error("Disallowed filename: %s"%value)            
        return value

