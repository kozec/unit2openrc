#!/usr/bin/env python2
"""
Unit2OpenRC - Conversion

Evertything interesting happens here.
"""
from __future__ import unicode_literals
from unitfile import UnitFile
from rcfile import RCFile, Command, StartStopDaemon
from . import ensure_list
from consts import *
import os, shlex


def convert(source, target):
	"""
	Performs actuall conversion.
	
	Currently, 'source' has to be UnitFile and 'target' RCFile.
	"""
	if isinstance(source, UnitFile) and isinstance(target, RCFile):
		_unit2openrc(source, target)
	else:
		raise TypeError("Unsupported conversion")


def _unit2openrc(unit, rc):
	"""
	Copies and converts data from UnitFile instance into RCFile instance
	"""
	# Convert basic stuff
	rc.description = unit.description
	if 'pidfile' in unit:
		rc.pidfile = unit.pidfile
	# Convert environment
	if 'environment' in unit:
		for x in ensure_list(unit.environment):
			for v in shlex.split(x):
				if "=" in v:
					k, v = v.split("=", 1)
					rc.env[k] = v
				else:
					print >>sys.stderr, "Warning: Invalid environment var definition:", v
	
	# Convert deps
	if 'requires' in unit:
		rc.needs = _convert_requirements(unit.requires)
	if 'wants' in unit:
		rc.want = _convert_requirements(unit.wants)
	if 'after' in unit:
		rc.after = _convert_requirements(unit.after)
	if 'before' in unit:
		rc.before = _convert_requirements(unit.before)
	if unit.type == ST_DBUS:
		rc.need.append('dbus')
		rc.want.append('dbus')
	
	# Convert ExecStart, ExecStop, ExecStartPre and ExecStopPre options
	rc.start, rc.stop = [], []
	rc.start_pre, rc.stop_pre = [], []
	rc.type = unit.type
	if unit.type not in RC_SERVICE_TYPES:
		raise ValueError("Unsupported service type: %s" % (unit.type,))
	
	# Convert 'start' command ExecStart and ExecStartPost, 2nd being optional
	rc.start.append(Command(EBEGIN, STARTING % (rc.description, rc.shortname)))
	rc.start.append(StartStopDaemon.start(Command.split(unit.exec_start),
		rc.pidfile, forking = unit.type not in (ST_SIMPLE, ST_DBUS)))
	if unit.type == ST_DBUS:
		rc.start.extend(Command.multiple(
			Command(DBUS_SERVICE_WAIT, unit.bus_name),
			"if [ $? -ne 0 ] ; then",
			Command.indented(
				"# ensure service is killed if it fails to acquire dbus name",
				Command("kill", '-9', '$(<', rc.pidfile, ')' ),
				Command(EEND, '1' ),
				"return 1"
			),
			"fi",
			"true"
		))
	
	if "exec_start_post" in unit:
		rc.start.extend(_convert_exec_post(unit.exec_start_post))
	else:
		rc.start.append(Command(EEND, "$?"))
	
	# ... 'stop' command, both ExecStop and ExecStopPost are optional
	rc.stop.append(Command(EBEGIN, STOPPING % (rc.description, rc.shortname)))
	if "exec_stop" in unit:
		rc.stop.append(Command.split(unit.exec_stop))
	if unit.type == ST_SIMPLE or "exec_stop" not in unit:
		rc.stop.append(StartStopDaemon.stop(rc.pidfile))
	
	if "exec_stop_post" in unit:
		rc.stop.extend(_convert_exec_post(unit.exec_stop_post))
	else:
		rc.stop.append(Command(EEND, "$?"))
	
	# Convert ExecStartPre and ExecStopPre options
	if "exec_start_pre" in unit:
		rc.start_pre.extend(_convert_exec_pre(unit.exec_start_pre))
	if "exec_stop_pre" in unit:
		rc.stop_pre.extend(_convert_exec_pre(unit.exec_stop_pre))


def _convert_exec_pre(options):
	"""
	Converts 'ExecStartPre' and 'ExecStopPre' options from systemd
	to list of command used later in rc script start_pre and stop_pre
	functions
	"""
	options = ensure_list(options)
	rv = []
	for o in options:
		if o.startswith("-"):
			rv.append(Command.split(o[1:]))
		else:
			rv.append(Command.split(o).extend("||", "return", "1"))
	if len(rv):
		rv.append(Command("return", "0"))
	return rv


def _convert_exec_post(options):
	"""
	Converts 'ExecStartPost' and 'ExecStopPost' options from systemd
	to list of command that can be appended to start() or stop() function.
	
	Generated list is in indented if-then-else block that checks if
	"start-stop-daemon" command failed and executes commands only if that's
	not case. Generated block also takes care of calling 'eend' command.
	"""
	options = ensure_list(options)
	return Command.multiple(
		"if [ $? -eq 0 ] ; then",
		Command.indented(
			[ Command.split(o).extend("||", "return", "1") for o in options ],
			Command(EEND, "0")
		),
		"else",
			Command(EEND, "1").indent(),
		"fi"
	)


def _convert_requirement(r):
	"""
	Converts requirement for need, wants, after (...) list from systemd
	unit name to open-rc daemon name.
	This is done mainly by stripping .service part of name, but uses
	UNIT_NAMES_DICT for some special names (e.g. 'network.target' -> 'net')
	
	May return empty string for some names, such as .socket and .device
	units. These are later ignored.
	"""
	if r in UNIT_NAMES_DICT:
		return UNIT_NAMES_DICT[r]
	
	for suffix in ('device', 'socket'):
		if r.endswith("." + suffix):
			# Ignored
			return ""
	
	for suffix in ('target', 'service'):
		if r.endswith("." + suffix):
			return ".".join(r.split(".")[0:-1])
	
	return r


def _convert_requirements(rs):
	"""
	Calls convert_requirement for each item in list and
	filters out empty returns.
	Supports nested lists as well.
	"""
	rv = set()
	def add(r):
		if type(r) == list:
			for x in r: add(x)
		else:
			for x in shlex.split(r):
				x = _convert_requirement(x)
				if x: rv.add(x)
	add(rs)
	return list(rv)


if __name__ == "__main__":
	# Loads file specified as first argument.
	# Used only to test loading
	import sys, pprint
	u = UnitFile(sys.argv[1])
	print u
	pprint.pprint(u.values)

