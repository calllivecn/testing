#!/usr/bin/env python3
# coding=utf-8
# date 2019-06-18 09:38:35
# author calllivecn <c-all@qq.com>


import io
import os
import sys
import stat
import logging
from struct import pack, unpack, pack_into, unpack_from, Struct


logger = logging.getLogger()
stream = logging.StreamHandler(sys.stderr)
fmt = logging.Formatter("%(filename)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")
stream.setFormatter(fmt)
logger.addHandler(stream)

logger.setLevel(logging.WARN)

version = "test v0.1"

__all__ = ["TarPaxInfo"]

NUL = b"\0"                     # the null character
BLOCKSIZE = 512                 # length of processing blocks
RECORDSIZE = BLOCKSIZE * 20     # length of records
#GNU_MAGIC = b"ustar  \0"        # magic gnu tar string
POSIX_MAGIC = b"ustar\x0000"    # magic posix tar string

LENGTH_NAME = 100               # maximum length of a filename
LENGTH_LINK = 100               # maximum length of a linkname
LENGTH_PREFIX = 155             # maximum length of the prefix field

REGTYPE = b"0"                  # regular file
AREGTYPE = b"\0"                # regular file
LNKTYPE = b"1"                  # link (inside tarfile)
SYMTYPE = b"2"                  # symbolic link
CHRTYPE = b"3"                  # character special device
BLKTYPE = b"4"                  # block special device
DIRTYPE = b"5"                  # directory
FIFOTYPE = b"6"                 # fifo special device
CONTTYPE = b"7"                 # contiguous file

XHDTYPE = b"x"                  # POSIX.1-2001 extended header
XGLTYPE = b"g"                  # POSIX.1-2001 global header

USTAR_FORMAT = 0                # POSIX.1-1988 (ustar) format
GNU_FORMAT = 1                  # GNU tar format
PAX_FORMAT = 2                  # POSIX.1-2001 (pax) format


#---------------------------------------------------------
# tarfile constants
#---------------------------------------------------------
# File types that tarfile supports:
SUPPORTED_TYPES = (REGTYPE, AREGTYPE, LNKTYPE,
                   SYMTYPE, DIRTYPE, FIFOTYPE,
                   CONTTYPE, CHRTYPE, BLKTYPE)

# File types that will be treated as a regular file.
REGULAR_TYPES = (REGTYPE, AREGTYPE,
                 CONTTYPE)


# Fields from a pax header that override a TarInfo attribute.
PAX_FIELDS = ("path", "linkpath", "size", "mtime", "atime",
              "uid", "gid", "uname", "gname")

# Fields from a pax header that are affected by hdrcharset.
PAX_NAME_FIELDS = {"path", "linkpath", "uname", "gname"}

# Fields in a pax header that are numbers, all other fields
# are treated as strings.
PAX_NUMBER_FIELDS = {
    "atime": float,
    "ctime": float,
    "mtime": float,
    "uid": int,
    "gid": int,
    "size": int
}

#--------------------------------------------------------
# Exception 
#--------------------------------------------------------
class TarError(Exception):
    """Base exception"""
    pass

class ExtractError(TarError):
    """General exception for extract errors."""
    pass

class ReadError(TarError):
    """Exception for unreadable tar archives."""
    pass

class CompressionError(TarError):
    """Exception for unavailable compression methods."""
    pass

class HeaderError(TarError):
    """Base exception for header errors."""
    pass

class EmptyHeaderError(HeaderError):
    """Exception for empty headers."""
    pass

class InvalidHeaderError(HeaderError):
    """Exception for invalid headers."""
    pass
#---------------------------------------------------------
# Some useful functions
#---------------------------------------------------------

def stn(s, length):
    """Convert a string to a null-terminated bytes object.
    """
    s = s.encode("utf-8")
    return s[:length] + (length - len(s)) * NUL

def nts(s):
    """Convert a null-terminated bytes object to a string.
    """
    p = s.find(b"\0")
    if p != -1:
        s = s[:p]
    return s.decode("utf-8")

def nti(s):
    """Convert a number field to a python number.
    """
    # There are two possible encodings for a number field, see
    # itn() below.
    if s[0] in (0o200, 0o377):
        n = 0
        for i in range(len(s) - 1):
            n <<= 8
            n += s[i + 1]
        if s[0] == 0o377:
            n = -(256 ** (len(s) - 1) - n)
    else:
        try:
            s = nts(s)
            n = int(s.strip() or "0", 8)
        except ValueError:
            raise InvalidHeaderError("invalid header")
    return n

#def itn(n, digits=8, format=DEFAULT_FORMAT):
def itn(n, digits=8):
    """Convert a python number to a number field.
    """
    # POSIX 1003.1-1988 requires numbers to be encoded as a string of
    # octal digits followed by a null-byte, this allows values up to
    # (8**(digits-1))-1. GNU tar allows storing numbers greater than
    # that if necessary. A leading 0o200 or 0o377 byte indicate this
    # particular encoding, the following digits-1 bytes are a big-endian
    # base-256 representation. This allows values up to (256**(digits-1))-1.
    # A 0o200 byte indicates a positive number, a 0o377 byte a negative
    # number.
    n = int(n)
    if 0 <= n < 8 ** (digits - 1):
        #s = bytes("%0*o" % (digits - 1, n), "ascii") + NUL
        s = bytes("{:0>{}o}".format(n, digits - 1), "ascii")  + NUL
    else:
        raise ValueError("overflow in number field")

    return s

def calc_chksums(buf):
    """Calculate the checksum for a member's header by summing up all
       characters except for the chksum field which is treated as if
       it was filled with spaces. According to the GNU tar sources,
       some tars (Sun and NeXT) calculate chksum with signed char,
       which will be different if there are chars in the buffer with
       the high bit set. So we calculate two checksums, unsigned and
       signed.
    """
    unsigned_chksum = 256 + sum(unpack_from("148B8x356B", buf))
    signed_chksum = 256 + sum(unpack_from("148b8x356b", buf))
    return unsigned_chksum, signed_chksum

def copyfileobj(src, dst, length=None, exception=OSError, bufsize=None):
    """Copy length bytes from fileobj src to fileobj dst.
       If length is None, copy the entire content.
    """
    bufsize = bufsize or 16 * 1024
    if length == 0:
        return
    if length is None:
        shutil.copyfileobj(src, dst, bufsize)
        return

    blocks, remainder = divmod(length, bufsize)
    for b in range(blocks):
        buf = src.read(bufsize)
        if len(buf) < bufsize:
            raise exception("unexpected end of data")
        dst.write(buf)

    if remainder != 0:
        buf = src.read(remainder)
        if len(buf) < remainder:
            raise exception("unexpected end of data")
        dst.write(buf)
    return


class tarinfo:
    """
    tar file detail info
    """

    __slots__ = ("path", "linkpath", "mode", "uid", "gid", "size", "mtime",
                 "type_", "uname", "gname",
                 "devmajor", "devminor")
    #__all__ = []

    def __init__(self, filename = ""):
        self._path = filename
        self._linkpath = ""
        self._name = filename
        self._mode = 0o644
        self._uid = 0
        self._gid = 0
        self._size = 0 
        self._atime = 0.0
        self._mtime = 0.0
        self._type = "x"
        self._uname = None
        self._gname = None
        self._devmajor = bytes(8)
        self._devminor = bytes(8)

        self.ustar_header_block = bytearray(BLOCKSIZE)

        self._pax_headers = {}


    def __get_ustar_header(self, fp):

        buf = fp.read(BLOCKSIZE)
        
    def __set_uster_header(self):
        pass

    def __get_ext_ustar_header(self):
        ext_name_header = b"./PaxHeader author=ZhangXu repositories=https://github.com/calllivecn/tar.py"
        self.__set_uster_header(self)


    def __get_pax_header(self):
        pass



class TarPaxInfo:
    """
    只实现了，POSIX 1003.1-2001 (pax) 格式
    """
    

    """
    ustar 格式 一个512 块，不足，后面填充 NUL。
    INFO = {                                    # offset | length (unit: byte)
            "name":     self.name,              # 0     |100
            "mode":     self.mode & 0o7777,     # 100   |8
            "uid":      self.uid,               # 108   |8
            "gid":      self.gid,               # 116   |8
            "size":     self.size,              # 124   |12
            "mtime":    self.mtime,             # 136   |12
            "chksum":   self.chksum,            # 148   |8
            "typeflag": self.typeflag,          # 156   |1
            "linkname": self.linkname,          # 157   |100
            "magic":    self.magix,             # 257   |6
            "version":  self.version,           # 263   |2
            "uname":    self.uname,             # 265   |32
            "gname":    self.gname,             # 297   |32
            "devmajor": self.devmajor,          # 329   |8
            "devminor": self.devminor           # 337   |8
            "prefix":   self.prefix,            # 345   |115 GNU tar 没有用这个字段。
            }
    """

    # PAX 拓展关格式 "%d %s=%s\n" % (length, keyword, value)
    POSIX = (
            "path",
            "linkpath",
            #"charset",         # 就是UTF-8
            #"comment",         # 注释
            "gid",              # 八进制字符串 <= oct(7777777)
            "uid",
            "uname",            # 所属用户名
            "gname",            # 所属用户组
            #"hdrcharset",       # 默认值UTF-8
            "atime",
            "mtime",
            "size"              # 八进制字符串 <= oct(77777777777)
            )

    def __init__(self):

        self.save_permission = False

        self.inodes = {}
        self.pax_headers = {}

    @classmethod
    def _create_pax_ext_header(cls, type_, pax_header_len):
        """
        实际上就是ustar模式的一个ext头
        """

        pax_ext_header = b"./PaxHeader author=ZhangXu repositories=https://github.com/calllivecn/tar.py"
        ustar = bytearray(BLOCKSIZE)

        # ustar field

        # name : len(name) = 100
        ustar[0:len(pax_ext_header)] = pax_ext_header

        # mode : 0000644\0 
        ustar[100:108] = b"0000644\x00"

        # size : 这里是指拓展头的大小
        ustar[124:136] = bytes("{:0>11o}".format(pax_header_len), "ascii") + NUL

        # chksum <用space,用计算>
        ustar[148:156] = b"        "

        # typeflag
        ustar[156:157] = type_ 
        #ustar[156:157] = b"g" 

        # magic(6) + version(2) = 8byte
        ustar[257:265] = POSIX_MAGIC

        # chksum
        chksum = calc_chksums(ustar)[0]
        ustar[148:156] = bytes("{:0>7o}".format(chksum), "ascii") + NUL

        return bytes(ustar)

    @classmethod
    def _create_pax_generic_header(cls, type_, pax_headers): 
        """Return a POSIX.1-2008 extended or global header sequence
           that contains a list of keyword, value pairs. The values
           must be strings.
        """
        # Check if one of the fields contains surrogate characters and thereby
        # forces hdrcharset=BINARY, see _proc_pax() for more information.
        binary = False
        for keyword, value in pax_headers.items():
            try:
                value.encode("utf-8")
            except UnicodeEncodeError:
                binary = True
                break

        records = b""
        if binary:
            # Put the hdrcharset field at the beginning of the header.
            records += b"21 hdrcharset=BINARY\n"

        for keyword, value in pax_headers.items():
            keyword = keyword.encode("utf-8")
            if binary:
                # Try to restore the original byte representation of `value'.
                # Needless to say, that the encoding must match the string.
                value = value.encode("utf-8", "surrogateescape")
            else:
                value = value.encode("utf-8")

            l = len(keyword) + len(value) + 3   # ' ' + '=' + '\n'
            n = p = 0
            while True: 
                n = l + len(str(p))
                if n == p:
                    break
                p = n
            records += bytes(str(p), "ascii") + b" " + keyword + b"=" + value + b"\n"

        # We use a hardcoded "././@PaxHeader" name like star does
        # instead of the one that POSIX recommends.

        # Create pax header + record blocks.
        #return cls._create_header(info, USTAR_FORMAT, "ascii", "replace") + \
        ext_header = cls._create_pax_ext_header(XHDTYPE, len(records)) + cls._create_payload(records)

        return ext_header + cls._create_pax_ext_header(type_, 0)

    @staticmethod
    def _create_payload(payload):
        """Return the string payload filled with zero bytes
           up to the next 512 byte border.
        """
        blocks, remainder = divmod(len(payload), BLOCKSIZE)
        if remainder > 0:
            payload += (BLOCKSIZE - remainder) * NUL
        return payload


    def filemetadata(self, filename):

        fullname = filename.replace(os.sep, "/")
        fullname = fullname.lstrip("/")

        pax = self.pax_headers.copy()

        pax["path"] = fullname

        if hasattr(os, "lstat"):
            fstat = os.lstat(filename)
        else:
            fstat = os.stat(filename)

        linkname = ""
        
        st_mode = fstat.st_mode
        if stat.S_ISREG(st_mode):
            inode = (fstat.st_ino, fstat.st_dev)

            if fstat.st_nlink > 1 and inode in self.inodes and fullname != self.inodes[inode]:
                type_ = LNKTYPE
                linkname = self.indes[inode]
            else:
                type_ = REGTYPE
                if inode[0]:
                    self.inodes[inode] = fullname

        elif stat.S_ISDIR(st_mode):
             type_ = DIRTYPE

        elif stat.S_ISFIFO(st_mode):
             type_ = FIFOTYPE

        elif stat.S_ISLNK(st_mode):
             type_ = SYMTYPE
             linkname = os.readlink(fullname)

        elif stat.S_ISCHR(st_mode):
             type_ = CHRTYPE

        elif stat.S_ISBLK(st_mode):
             type_ = BLKTYPE

        else:
            logger.warn("不支持的文件类型：{}".format(filename))
        
        if linkname:
            pax["linkpath"] = linkname

        s, c = divmod(fstat.st_size, BLOCKSIZE)
        if c > 0:
            s += 1

        pax["size"] = "{:o}".format(fstat.st_size)

        if self.save_permission:
            pax["uid"] = str(fstat.st_uid)
            pax["gid"] = str(fstat.st_gid)

            try:
                import pwd
                pax["uname"] = pwd.getpwuid(fstat.st_uid).pw_name
            except ModuleNotFoundError:
                pass

        
            try:
                import grp
                pax["gname"] = pwd.getpwuid(fstat.st_gid).gr_name
            except ModuleNotFoundError:
                pass

        pax["atime"] = str(fstat.st_atime)
        pax["mtime"] = str(fstat.st_mtime)

        # return pax_header data
        return self._create_pax_generic_header(type_, pax)


if __name__ == "__main__":
    tarpaxinfo = TarPaxInfo()
    
    out_tarname = sys.argv[1]

    tar_fp = open(out_tarname, "wb")

    for file_dir in sys.argv[2:]:

        filesize = os.path.getsize(file_dir)


        tarfiledata = tarpaxinfo.filemetadata(file_dir)
        
        with open(file_dir, "rb") as fp:

            tar_fp.write(tarfiledata)

            tar_fp.write(fp.read())


        s, c = divmod(filesize, BLOCKSIZE)
        if c > 0:
            fill_data = (BLOCKSIZE - c) * NUL
            tar_fp.write(fill_data)
            tar_fp.write(bytes(2*BLOCKSIZE)) 

    tar_fp.close()

        
    
