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
	mod = Extension(PARENT_PKG + '.sniff',
			libraries = BTLIBRARIES,
			include_dirs = INCLUDE_DIRS,
		sources = [SNIFFMODDIR + os.sep + 'basesniffmodule.c', 
				   SNIFFMODDIR + os.sep + 'bthandler.c'])
	
	mod2 = Extension(PARENT_PKG + '.sniff_fileio',
			libraries = BTLIBRARIES,
			include_dirs = INCLUDE_DIRS,
		sources = [ SNIFFMODDIR  + os.sep + 'sniffio.c'])

	mod3 = Extension(PARENT_PKG + '._crack',
			libraries = BTLIBRARIES,
			include_dirs = INCLUDE_DIRS,
		sources = [ SNIFFMODDIR + os.sep + 'sniffcrack.c'])
	
	mods = [mod, mod2, mod3]

setup( name = 'UmitBluetoothSniffer',
	version = '0.1',
	description = 'Umit Bluetooth Sniffer: part of the Umit Bluetooth Attack Framework',
	author = 'Quek Shu Yang',
	author_email = 'quekshuy@gmail.com',
	url = 'http://trac.umitproject.org/wiki/BluetoothSniffing',
	ext_modules = mods,
	packages = ['umit', 'umit.bluetooth'] 
	)
