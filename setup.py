from distutils.core import setup, Extension
import sys

mods = []
if sys.platform == 'linux2':
	print 'linux'
	mod = Extension('umit.bluetooth.sniff',
			libraries = ['bluetooth'],
			include_dirs = ['csniff'],
		sources = ['csniff/basesniffmodule.c'])
	mods = [mod]

setup( name = 'UmitBluetoothSniffer',
	version = '0.1',
	description = 'Umit Bluetooth Sniffer: part of the Umit Bluetooth Attack Framework',
	author = 'Quek Shu Yang',
	author_email = 'quekshuy@gmail.com',
	url = 'http://trac.umitproject.org/wiki/BluetoothSniffing',
	ext_modules = mods,
	packages = ['umit', 'umit.bluetooth'] 
	)
