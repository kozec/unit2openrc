#!/usr/bin/env python2
"""
Unit2OpenRC - RC File

Holds and writes rc file data.
Cannot load already existing file.
"""
from __future__ import unicode_literals
from . import ServiceConfig
from unitfile import UnitFile
from consts import *
from cStringIO import StringIO
import os, shlex

class RCFile(ServiceConfig):
	def __init__(self, shortname):
		ServiceConfig.__init__(self)
		self.shortname = shortname
		self.pidfile = os.path.join(RUN_D, shortname + ".pid")
		self.type = ST_FORKING
		self.description = "Description not set"
		# start and stop are lists of commands executed when starting or
		# stopping service; commands are specified as lists of arguments,
		# so both start and stop contains list of lists
		self.start = []
		self.stop  = []
		# start_pre and stop_pre are in same format as start and stop,
		# but used in different function
		self.start_pre = []
		self.stop_pre = []
		# see man openrc-run for these
		self.need = []
		self.want = []
		self.after = []
		self.before = []
		# env contains environment variables set on top of rc file
		self.env = {}
	
	
	def from_unit(self, unit):
		"""
		Copies and converts values from UnitFile.
		Returns self
		"""
		# Convert basic stuff
		self.description = unit.description
		if 'pidfile' in unit:
			self.pidfile = unit.pidfile
		# Convert environment
		if 'environment' in unit:
			for v in shlex.split(unit.environment):
				if "=" in v:
					k, v = v.split("=", 1)
					self.env[k] = v
				else:
					print >>sys.stderr, "Warning: Invalid environment var definition:", v
		
		# Convert deps
		if 'requires' in unit:
			self.needs = RCFile.convert_requirements(unit.requires)
		if 'wants' in unit:
			self.want = RCFile.convert_requirements(unit.wants)
		if 'after' in unit:
			self.after = RCFile.convert_requirements(unit.after)
		if 'before' in unit:
			self.before = RCFile.convert_requirements(unit.before)
		if unit.type == ST_DBUS:
			self.need.append('dbus')
			self.want.append('dbus')
		
		# Convert ExecStart, ExecStop, ExecStartPre and ExecStopPre options
		self.start, self.stop = [], []
		self.start_pre, self.stop_pre = [], []
		self.type = unit.type
		if unit.type not in RC_SERVICE_TYPES:
			raise ValueError("Unsupported service type: %s" % (unit.type,))
		
		# Convert 'start' command ExecStart and ExecStartPost, 2nd being optional
		self.start.append(Command(EBEGIN, STARTING % (self.description, self.shortname)))
		self.start.append(StartStopDaemon.start(Command.split(unit.exec_start),
			self.pidfile, forking = unit.type not in (ST_SIMPLE, ST_DBUS)))
		if unit.type == ST_DBUS:
			self.start.extend(Command.multiple(
				Command(DBUS_SERVICE_WAIT, unit.bus_name),
				"if [ $? -ne 0 ] ; then",
				Command.indented(
					"# ensure service is killed if it fails to acquire dbus name",
					Command("kill", '-9', '$(<', self.pidfile, ')' ),
					Command(EEND, '1' ),
					"return 1"
				),
				"fi",
				"true"
			))
		
		if "exec_start_post" in unit:
			self.start.extend(RCFile.convert_exec_post(unit.exec_start_post))
		else:
			self.start.append(Command(EEND, "$?"))
		
		# ... 'stop' command, both ExecStop and ExecStopPost are optional
		self.stop.append(Command(EBEGIN, STOPPING % (self.description, self.shortname)))
		if "exec_stop" in unit:
			self.stop.append(Command.split(unit.exec_stop))
		if unit.type == ST_SIMPLE or "exec_stop" not in unit:
			self.stop.append(StartStopDaemon.stop(self.pidfile))
		
		if "exec_stop_post" in unit:
			self.stop.extend(RCFile.convert_exec_post(unit.exec_stop_post))
		else:
			self.stop.append(Command(EEND, "$?"))
		
		# Convert ExecStartPre and ExecStopPre options
		if "exec_start_pre" in unit:
			self.start_pre.extend(RCFile.convert_exec_pre(unit.exec_start_pre))
		if "exec_stop_pre" in unit:
			self.stop_pre.extend(RCFile.convert_exec_pre(unit.exec_stop_pre))
		
		return self
	
	
	def write(self, outfileobj, source_file_name="unknown file"):
		"""
		Writes rc script into provided file object.
		source_file_name is used only in comment string and doesn't actually
		affect anything.
		"""
		o = StringIO()
		
		# Output header
		o.write(RC_HEADER % dict(
			source_file_name = source_file_name,
			unit2openrc = "Unit2OpenRC"
		))
		
		# Output PID file and environment variables
		for v in self.env:
			val = self.env[v]
			if " " in val:
				val = '"%s"' % (val.encode('unicode_escape').replace('"', '\\"'),)
			o.write("%s=%s\n" % (v, val))
		o.write("pidfile=%s\n" % (self.pidfile))
		o.write("\n")
		
		# Oputput depend function if needed
		depend = []
		if len(self.need):   depend.append(Command( 'need',   *self.need))
		if len(self.want):   depend.append(Command( 'want',   *self.want))
		if len(self.after):  depend.append(Command( 'after' , *self.after))
		if len(self.before): depend.append(Command( 'before', *self.before))
		if len(depend):
			RCFile.output_function(o, 'depend', depend)
		
		# Outuput start_pre and stop_pre functions, if needed
		if len(self.start_pre):
			RCFile.output_function(o, 'start_pre', self.start_pre)
		if len(self.stop_pre):
			RCFile.output_function(o, 'stop_pre', self.stop_pre)
		
		# Outuput start and stop functions
		RCFile.output_function(o, 'start', self.start)
		RCFile.output_function(o, 'stop', self.stop)
		
		outfileobj.write(o.getvalue().encode('utf-8'))
	
	
	@staticmethod
	def convert_exec_pre(options):
		"""
		Converts 'ExecStartPre' and 'ExecStopPre' options from systemd
		to list of command used later in rc script start_pre and stop_pre
		functions
		"""
		options = RCFile.ensure_list(options)
		rv = []
		for o in options:
			if o.startswith("-"):
				rv.append(Command.split(o[1:]))
			else:
				rv.append(Command.split(o).extend("||", "return", "1"))
		if len(rv):
			rv.append(Command("return", "0"))
		return rv
	
	
	@staticmethod
	def convert_exec_post(options):
		"""
		Converts 'ExecStartPost' and 'ExecStopPost' options from systemd
		to list of command that can be appended to start() or stop() function.
		
		Generated list is in indented if-then-else block that checks if
		"start-stop-daemon" command failed and executes commands only if that's
		not case. Generated block also takes care of calling 'eend' command.
		"""
		options = RCFile.ensure_list(options)
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
		"""
		rv = []
		rv.append(Command.split("if [ $? -eq 0 ] ; then"))
		for o in options:
			rv.append(Command.split(o).extend("||", "return", "1").indent())
		rv.extend(Command.multiple(
			   Command(EEND, "0").indent(),
			"else",
			   Command(EEND, "1").indent(),
			"fi"
		))
		return rv
		"""
	
	
	@staticmethod
	def output_function(o, name, commands):
		""" Writes bash function 'name' into file-like object 'o' """
		o.write('%s() {\n' % (name,))
		for c in commands:
			o.write("\t")
			o.write(c.to_string())
			o.write("\n")
		o.write('}\n\n')
	
	
	@staticmethod
	def ensure_list(v):
		""" Returns v if v is list; returns [v] otherwise """
		if type(v) == list: return v
		return [v]
	
	@staticmethod
	def convert_requirement(r):
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
	
	
	@staticmethod
	def convert_requirements(rs):
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
					x = RCFile.convert_requirement(x)
					if x: rv.add(x)
		add(rs)
		return list(rv)
	
	def __str__(self):
		return "<RCFile '%s'>" % (self.shortname, )


class Command(object):
	"""
	Holds command arguments.
	Converted to string by RCFile.write method.
	"""
	
	def __init__(self, *args):
		self.args = list(args)
		self.prefix = ""
	
	
	def indent(self, amount=1):
		"""
		Adds indent (spaces) before command.
		Returns self.
		"""
		self.prefix += "\t" * amount
		return self
	
	
	def extend(self, *a):
		"""
		Adds command arguments.
		Returns self.
		"""
		self.args.extend(a)
		return self
	
	
	def to_string(self):
		"""
		Returns command arguments as quoted, escaped, unicode string.
		"""
		# escape quotes and special characters
		l = [ (x.encode('utf-8').encode('string_escape').replace("\\'", "'")
				.replace('"', '\\"').decode('utf-8'))
				if '"' in x else x for x in self.args ]
		# quote arguments
		l = [ '"%s"' % (x,) if " " in x and x.strip() != "" else x for x in l ]
		return self.prefix + " ".join(l)	
	
	@staticmethod
	def multiple(*commands):
		"""
		Creates list of multiple Command instances.
		Each parameter should be either Command instance or string that will
		be passed to Command.split() method.
		"""
		rv = []
		for c in commands:
			if type(c) == list:
				rv.extend(c)
			elif isinstance(c, Command):
				rv.append(c)
			else:
				rv.append(Command.split(c))
		return rv
	
	
	@staticmethod
	def indented(*commands):
		"""
		Works as 'multiple', but calls 'indent' on each command to add indent
		to entire group.
		"""
		return [ c.indent() for c in Command.multiple(*commands) ]
	
	
	@staticmethod
	def split(s):
		""" Parses arguments from string and returns new Command object """
		return Command(*shlex.split(s))


class StartStopDaemon(Command):
	"""
	Holds data for start-stop-daemon command.
	"""
	def __init__(self, daemon_command, pidfile, start, forking=False):
		"""
		daemon_command has to be Command instance.
		Generates -S (start) command if start is True; Othewise
		generates -K (kill) command.
		"""
		Command.__init__(self)
		if not start:
			# stop
			self.args = [ START_STOP_DAEMON, '-K', '-p', pidfile ]
		else:
			daemon_args = daemon_command.args
			daemon_args = [ daemon_args[0], "--" ] + daemon_args[1:]
			if forking:
				self.args = [ START_STOP_DAEMON, '-S' ] + daemon_args
			else:
				self.args = [ START_STOP_DAEMON, '-S', '-b', '-m', '-p',
					pidfile, '-x' ] + daemon_args
			
	
	@staticmethod
	def start(daemon_command, pidfile, forking=False):
		return StartStopDaemon(daemon_command, pidfile, True, forking=forking)
	
	@staticmethod
	def stop(pidfile, forking=False):
		return StartStopDaemon(None, pidfile, False, forking=forking)


if __name__ == "__main__":
	# Loads file specified as first argument.
	# Used only to test loading
	import sys, pprint
	u = UnitFile(sys.argv[1])
	print u
	pprint.pprint(u.values)

