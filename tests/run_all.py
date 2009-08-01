''' 


    Simple testing tool. 
    TODO: find out about nosetest


'''

import os, re, sys

             
def getbuilddirroot():
    bdroot = ''.join([os.getcwd(), os.sep, 'build', os.sep])
    build_dir_p = re.compile(r'^lib')
    for dir in os.listdir(bdroot):
        if build_dir_p.match(dir):
            bdroot = ''.join([bdroot, dir])
            break
    return bdroot


if not sys.platform == 'linux2':
    print 'BTSniffing development only on Linux for now'
    exit()

# get into project root
print "Checking we're in project root .... ",
bdroot = testsroot = None
if 'setup.py' in os.listdir(os.getcwd()):
     print "yes"
     print 'Doing disutils build'
     os.system('python setup.py build')
     bdroot = getbuilddirroot()
     print 'build dir project root: ', bdroot
else:
    raise IOError("run_tests: not in project root. Run script in BTSniffer root")
    exit()

print 'Checking that tests exist ... ', 
if 'tests' in os.listdir(os.getcwd()):
    print 'yes'
    testsroot = ''.join([os.getcwd(), os.sep, 'tests'])
else:
    raise IOError("run_tests: no tests folder.")
    exit()
    
# Get all tests files
testfiles = []
testfile_p = re.compile(r'^[Tt]est')
for f in os.listdir(testsroot):
    if testfile_p.search(f):
        testfiles.append(f)
if len(testfiles) == 0:
    raise IOError('Serious error')
# Copy the test files over
print 'Copying test files....'
for file in testfiles:
    orgtest = os.sep.join([testsroot, file])
    print 'Copying %s to %s' % (orgtest, bdroot)
    os.system('cp %s %s' % (os.sep.join([testsroot, file]), bdroot))

print 'Running tests...'
os.chdir(bdroot)
os.system('nosetests')

print 'Cleaning up...'
for f in testfiles:
    os.remove(f)

