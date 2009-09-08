"""
Taken from PythonInfo Wiki Distutils Tutorial, with thanks to DonnIngle

"""

from distutils.core import setup, Extension
import sys, os

PARENT_PKG = 'umit.bluetooth'
BTLIBRARIES = ['bluetooth']
SNIFFMODDIR = 'csniff'
INCLUDE_DIRS = [SNIFFMODDIR]

mods = []
if sys.platform == 'linux2':
	# print 'linux'
	mod = Extension(PARENT_PKG + '.btsniff',
			libraries = BTLIBRARIES,
			include_dirs = INCLUDE_DIRS,
		sources = [SNIFFMODDIR + os.sep + 'basesniffmodule.c', 
				   SNIFFMODDIR + os.sep + 'bthandler.c',
				   SNIFFMODDIR + os.sep + 'layers.c'])
	
	mod2 = Extension(PARENT_PKG + '.btsniff_fileio',
			libraries = BTLIBRARIES,
			include_dirs = INCLUDE_DIRS,
		sources = [ SNIFFMODDIR  + os.sep + 'sniffio.c'])

	mod3 = Extension(PARENT_PKG + '._crack',
			libraries = BTLIBRARIES,
			include_dirs = INCLUDE_DIRS,
		sources = [ SNIFFMODDIR + os.sep + 'sniffcrack.c'])
	
	mod4 = Extension(PARENT_PKG + '.btlayers',
					 libraries = BTLIBRARIES,
					 include_dirs = INCLUDE_DIRS,
					 sources = [SNIFFMODDIR + os.sep + 'layers.c'])
	testmod = Extension(PARENT_PKG + '.harness', 
					    libraries = BTLIBRARIES,
					    include_dirs = INCLUDE_DIRS,
					    sources = [SNIFFMODDIR + os.sep + 'harness.c',
								   SNIFFMODDIR + os.sep + 'layers.c'])
	
	mods = [
		    mod4, 
		    mod3,
		    mod2,
		    mod,
		    testmod
		    ]

setup( name = 'UmitBluetoothSniffer',
	version = '0.1',
	description = 'Umit Bluetooth Sniffer: part of the Umit Bluetooth Attack Framework',
	author = 'Quek Shu Yang',
	author_email = 'quekshuy@gmail.com',
	url = 'http://trac.umitproject.org/wiki/BluetoothSniffing',
	ext_modules = mods,
	packages = ['umit', 'umit.bluetooth'] 
	)
