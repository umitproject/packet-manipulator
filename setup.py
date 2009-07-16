"""
Taken from PythonInfo Wiki Distutils Tutorial, with thanks to DonnIngle

"""

from distutils.core import setup, Extension
import sys

mods = []
if sys.platform == 'linux2':
	print 'linux'
	mod = Extension('umit.bluetooth.sniff',
			libraries = ['bluetooth'],
			include_dirs = ['csniff'],
		sources = ['csniff/basesniffmodule.c', 'csniff/bthandler.c'])
	
	mod2 = Extension('umit.bluetooth.sniff_fileio',
			libraries = ['bluetooth'],
			include_dirs = ['csniff'],
		sources = ['csniff/sniffio.c'])
	
	mods = [mod, mod2]

setup( name = 'UmitBluetoothSniffer',
	version = '0.1',
	description = 'Umit Bluetooth Sniffer: part of the Umit Bluetooth Attack Framework',
	author = 'Quek Shu Yang',
	author_email = 'quekshuy@gmail.com',
	url = 'http://trac.umitproject.org/wiki/BluetoothSniffing',
	ext_modules = mods,
	packages = ['umit', 'umit.bluetooth'] 
	)
