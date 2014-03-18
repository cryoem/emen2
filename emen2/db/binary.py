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
    
def parse(creationtime=None, name=None):
    # Timestamps are now in ISO8601 format
    # e.g.: "2011-10-16T02:00:00+00:00"
    creationtime = creationtime or emen2.db.database.utcnow()
    year = int(creationtime[:4])
    mon = int(creationtime[5:7])
    day = int(creationtime[8:10])

    # YYYYMMDD
    datekey = "%04d-%02d-%02d"%(year, mon, day)
    datedir = os.path.join('%04d'%year, '%02d'%mon, '%02d'%day)

    # Get the binary storage paths from config
    # Find the last item matching the current date
    # Resolve the parsed bdo key to a directory (filedir)
    binarydirs = emen2.db.config.get('paths.binary')
    bp = [x for x in sorted(binarydirs.keys()) if str(x)<=datekey]
    filedir = os.path.join(binarydirs[bp[-1]], datedir)

    # ... same for previewpath
    previewdirs = emen2.db.config.get('paths.preview')
    pp = [x for x in sorted(previewdirs.keys()) if str(x)<=datekey]
    previewdir = os.path.join(previewdirs[pp[-1]], datedir)
    
    ret = {
        "creationtime":creationtime,
        "name":name,
        "filedir":filedir,
        "previewdir":previewdir
    }
    if name:
        ret["filepath"] = os.path.join(filedir, name)
        ret["previewpath"] = os.path.join(previewdir, name)
    return ret
    
# Write contents to a temporary file.
def writetmp(filedata=None, fileobj=None, filedir=None, suffix="upload"):
    '''Write to temporary storage, and calculate size/md5.
    :return: Temporary file path, the file size, and an md5 digest.
    '''
    if filedata:
        fileobj = cStringIO.StringIO(filedata)
    if not fileobj:
        raise ValueError("No data to write to temporary file.")

    # Seek to the beginning of the fileobj.
    fileobj.seek(0)

    # Check that the directory for this day exists.
    filedir = filedir or parse(None, 'tmp')['filedir']
    if not os.path.exists(filedir):
        os.makedirs(filedir)

    # Open the temporary file
    (fd, tmpfile) = tempfile.mkstemp(dir=filedir, suffix='.%s'%suffix)

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

    Provides following parameters:
        filename, record, md5, filesize, compress

    The filename parameter is the original name of the uploaded file. The
    filesize parameter is the size of the file, and the md5 parameter is the
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
    parameter. Read permission on a Binary requires either ownership of the
    item, or read permission on the associated Record. The owner of the Binary
    can change which Record is associated.

    When a Binary is retrieved from the database, the filepath property will
    be accessible. This points to the physical file on disk containing the data.

    These BaseDBObject methods are overridden:

        init            Init Binary
        setContext      Check read permissions and bind Context
        validate        Check required parameters

    :attr filename: File name
    :attr filesize: Size of the uncompressed file
    :attr md5: MD5 checksum of the uncompressed file
    :attr compress: File is gzip compressed
    :attr record: Associated Record
    :property filepath: Path to the file on disk
    """

    def init(self):
        super(Binary, self).init()
        self.filepath = None
        self.data['filename'] = None
        self.data['record'] = None
        self.data['compress'] = False
        self.data['filesize'] = None
        self.data['md5'] = None

    def setContext(self, ctx):
        super(Binary, self).setContext(ctx=ctx)
        self.filepath = parse(self.creationtime, self.name).get('filepath')
        if self.isowner():
            return
        # Check we can access the associated record.
        if self.record is not None:
            self.ctx.db.record.get(self.record, filt=False)

    def validate(self):
        # Validate
        if not all([self.filename, self.filesize is not None]):
            print self.filename, self.filesize
            raise emen2.db.exceptions.ValidationError("Cannot upload empty file, or a file without a name.")

    ##### Setters #####
    
    # These immutable parameters only ever be set for a 
    # new Binary, before commit
    def _set_md5(self, key, value):
        if not self.isnew():
            raise emen2.db.exceptions.ValidationError("Cannot change a Binary's file attachment.")
        self._set(key, self._strip(value), self.isowner())

    def _set_compress(self, key, value):
        if not self.isnew():
            raise emen2.db.exceptions.ValidationError("Cannot change a Binary's file attachment.")
        self._set(key, self._strip(value), self.isowner())

    def _set_filesize(self, key, value):
        if not self.isnew():
            raise emen2.db.exceptions.ValidationError("Cannot change a Binary's file attachment.")
        self._set(key, int(value), self.isowner())

    # These can be changed normally
    def _set_filename(self, key, value):
        # Sanitize filename.. This will allow unicode characters,
        #    and check for reserved filenames on linux/windows
        value = self._validate_filename(value)
        self._set(key, value, self.isowner())

    def _set_record(self, key, value):
        self._set(key, self._strip(value), self.isowner())
        
    def _validate_filename(self, value):
        """
        """
        value = self._strip(value)
        # ... make this a regex.
        value = "".join([i for i in value if i.isalpha() or i.isdigit() or i in '.()-=_#'])

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

