#!/usr/bin/env python2
"""
Unit2OpenRC - RC File

Holds and writes rc file data.
Cannot load already existing file.
"""
from __future__ import unicode_literals
from . import ServiceConfig, Command
from unitfile import UnitFile
from consts import *
from cStringIO import StringIO
import os

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
			o.write("export %s=%s\n" % (v, val))
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
	def output_function(o, name, commands):
		""" Writes bash function 'name' into file-like object 'o' """
		o.write('%s() {\n' % (name,))
		for c in commands:
			o.write("\t")
			o.write(c.to_string())
			o.write("\n")
		o.write('}\n\n')
	
	
	def __str__(self):
		return "<RCFile '%s'>" % (self.shortname, )


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

