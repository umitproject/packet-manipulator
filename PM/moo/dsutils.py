import sys
import os

def getoutput(cmd):
    """Return output (stdout or stderr) of executing cmd in a shell."""
    return getstatusoutput(cmd)[1]

def getstatusoutput(cmd):
    """Return (status, output) of executing cmd in a shell."""
    if sys.platform == 'win32':
        pipe = os.popen(cmd, 'r')
        text = pipe.read()
        sts = pipe.close() or 0
        if text[-1:] == '\n':
            text = text[:-1]
        return sts, text
    else:
        from commands import getstatusoutput
        return getstatusoutput(cmd)

def pkgc_version_check(name, longname, req_version):
    is_installed = not os.system('pkg-config --exists %s' % name)
    if not is_installed:
        print "Could not find %s" % longname
        return 0

    orig_version = getoutput('pkg-config --modversion %s' % name)
    version = map(int, orig_version.split('.'))
    pkc_version = map(int, req_version.split('.'))

    if version >= pkc_version:
        return 1
    else:
        print "Warning: Too old version of %s" % longname
        print "         Need %s, but %s is installed" % \
              (pkc_version, orig_version)
        self.can_build_ok = 0
        return 0

def pkc_get_include_dirs(names):
    if type(names) != tuple:
        names = (names,)
    retval = []
    for name in names:
        output = getoutput('pkg-config --cflags-only-I %s' % name)
        retval.extend(output.replace('-I', '').split())
    return retval

def pkc_get_libraries(names):
    if type(names) != tuple:
        names = (names,)
    retval = []
    for name in names:
        output = getoutput('pkg-config --libs-only-l %s' % name)
        retval.extend(output.replace('-l', '').split())
    return retval

def pkc_get_library_dirs(names):
    if type(names) != tuple:
        names = (names,)
    retval = []
    for name in names:
        output = getoutput('pkg-config --libs-only-L %s' % name)
        retval.extend(output.replace('-L', '').split())
    return retval
