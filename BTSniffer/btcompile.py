#! /usr/bin/env python

## 	This file contains a hacked version of a build script for now
#	TODO: write the equivalent in bash script or find a good build tool
#	like make that works well with Python to accomplish the same
import os, sys
import shutil
import re
import subprocess

class btcompile():

    def __init__(self):
        # build and setup commands
        self.CMD_BUILD 		= 'python setup.py build'

        self.PATH_PM            = '../'
        self.PATH_BUILD			= 'build/'
        self.WANTED_FILE_EXTS 	= ['py','so']
        self.PATH_BT_BACKEND 	= self.PATH_PM + 'umit/pm/backend/bt_sniffer/'
        self.PATH_BT_PINCRACK	= self.PATH_PM + 'btpincrack-v0.3'
        self.PATH_LIB_PREFIX	= '%slib.linux' % self.PATH_BUILD
        self.dependency         = 'dep_check'
        self.python_dev_file         = self.dependency + '/' + 'python-dev.c'
        self.bluetooth_dev_file      = self.dependency + '/' + 'bluetooth-dev.c'

        self.blue_deps = [ 'Bluez :- The Linux Bluetooth Stack',
                            'Bluetooth',
                            'Libbluetooth-dev'
                           ]
        self.python_deps = ['python-dev : Header files and a static library for Python']

    def _cpfunc(self,arg, dirname, flist):
	    if self.PATH_LIB_PREFIX in dirname:
		    for f in flist:
			    if f[f.rfind('.') + 1:] in self.WANTED_FILE_EXTS:
				    srcfile = os.path.join(dirname, f)
				    shutil.copy2(srcfile, self.PATH_BT_BACKEND)

    
    def gcc(self):#check if gcc is present
        return True

    def python_dev(self):
        proc = subprocess.Popen('gcc ' + self.python_dev_file,
                                    shell=True,
                                    stderr=subprocess.PIPE
                                   )
        # Need to pass -I/usr/include/python2.6 as compile time argument, find better way
        for dep in self.python_deps:
            print dep
        return False

    def blue_dev(self):
        proc = subprocess.Popen('gcc ' + self.bluetooth_dev_file,
                                    shell=True,
                                    stderr=subprocess.PIPE
                                   )
        #No errors if strlength is 0
        if len(proc.communicate()[1])==0:
            return True
        
        for dep in self.blue_deps:
            print dep
        return False

    def make(self):
        if self.gcc():
            blue_check=self.blue_dev()
            python_check=self.python_dev()
        
            if blue_check or python_check:
                return False

            #Compile and copy the C files for BTSniffer to PATH_BT_BACKEND
            os.system(self.CMD_BUILD)
            if os.path.exists(self.PATH_BT_BACKEND):
                shutil.rmtree(self.PATH_BT_BACKEND)        
            os.makedirs(self.PATH_BT_BACKEND)
            os.path.walk(self.PATH_BUILD, self._cpfunc, None)

            #Delete old btpincrack in PM, copy it again
            if os.path.exists(self.PATH_BT_PINCRACK):
                shutil.rmtree(self.PATH_BT_PINCRACK)
            shutil.copytree('btpincrack-v0.3',self.PATH_BT_PINCRACK)

        else:
            return False

#btcompile().make()
