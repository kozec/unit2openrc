#!/usr/bin/env python2
"""
Unit2OpenRC - main

Converts systemd unit files into OpenRC scripts
"""
from __future__ import unicode_literals
from unitfile import UnitFile
from rcfile import RCFile
from convert import convert
from consts import *
import sys, os, argparse

HELP = """ Converts systemd unit files into OpenRC scripts """


def main(argv):
	parser = argparse.ArgumentParser(description=HELP)
	parser.add_argument('unit', type=str,
		help="""input, systemd unit. Either full path to file or unit name with
			or without suffix. If path is ommited, unit is searched in default
			locations. If suffix is ommited, .service is assumed"""
		)
	parser.add_argument('rc_file', type=str, nargs="?",
		help="""output, openrc script. Either full path to file or just name.
			If path is ommited, script is created in default %s directory.
			If ommited completly, name of sytemd unit stripped of extension
			is used.
			""" % (INIT_D,)
		)
	args = parser.parse_args()

	if "/" in args.unit:
		unit_filename = args.unit
	else:
		# Unit name without path was passed - search for it
		unit_filename = None
		for path in UNIT_DIRS:
			for suffix in ("", ".service"):
				fn = os.path.join(path, args.unit + suffix)
				if os.path.exists(fn):
					unit_filename = fn
					break
			if unit_filename : break
		if not unit_filename:
			print >>sys.stderr, "Unknown systemd unit: %s" % (args.unit,)
			return 1
	
	if args.rc_file is None:
		rc_filename = os.path.split(unit_filename)[-1]
		rc_filename = rc_filename.split(".")[0]
		rc_filename = os.path.join(INIT_D, rc_filename)
	elif "/" in args.rc_file:
		rc_filename = args.rc_file
	else:
		rc_filename = os.path.join(INIT_D, args.rc_file)

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
		rc = RCFile(short_name)
		convert(u, rc)
		rc.write(open(rc_filename, "w"), unit_filename)
		os.chmod(rc_filename, 0755)
	except IOError, e:
		print >>sys.stderr, "Failed to write rc file: %s" % (e,)
		return 1
	
	print "Converted %s" % (rc.shortname)
