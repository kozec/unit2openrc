#!/usr/bin/env python2
"""
Unit2OpenRC - main

Converts systemd unit files into OpenRC scripts
"""
from __future__ import unicode_literals
from unitfile import UnitFile
from rcfile import RCFile
import sys, os

def convert(unit_filename, rc_filename):
	"""
	Converts specified systemd unit into rc script with specified filename.
	"""
	try:
		u = UnitFile(open(unit_filename, "r"))
	except IOError, e:
		print >>sys.stderr, "Failed to read unit file: %s" % (e,)
		return 1
	except ValueError, e:
		print >>sys.stderr, "Invalid unit file: %s" % (e,)
		return 1
	
	short_name = os.path.split(rc_filename)[-1]
	try:
		rc = RCFile(short_name).from_unit(u)
		rc.write(open(rc_filename, "w"), unit_filename)
		os.chmod(rc_filename, 0755)
	except IOError, e:
		print >>sys.stderr, "Failed to write rc file: %s" % (e,)
		return 1


def main(argv):
	unit_filename = argv[1]
	rc_filename = argv[2]
	return convert(unit_filename, rc_filename)
