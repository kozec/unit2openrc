#!/usr/bin/env python2
from distutils.core import setup
import glob


packages = [ 'unit2openrc' ]

if __name__ == "__main__":
	setup(name = 'unit2openrc',
	    version = "0.1",
	    description = 'Converts systemd units into openrc scripts',
	    author = 'kozec',
	    packages = packages,
	    # data_files = data_files,
	    scripts = ['scripts/unit2openrc'],
	    license = 'BSD',
	    platforms = ['Linux'],
	)
