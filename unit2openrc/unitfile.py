#!/usr/bin/env python2
"""
Unit2OpenRC - Unit File

Loads and holds data from systemd unit file.
"""
from __future__ import unicode_literals
from . import ServiceConfig
from consts import *
from collections import OrderedDict
import re, ConfigParser

class UnitFile(ServiceConfig):
	CAMEL = re.compile('^([^a-z]*[a-z0-9]*_?)(.*)')
	# UnitFile() throws ValueError if any if these fields is missing
	REQUIRED_FIELDS = ( 'description', 'exec_start' )
	IGNORED_SECTIONS = ( 'Install', )
	
	def __init__(self, fileobj):
		ServiceConfig.__init__(self)
		# Parse unit file
		cp = UnitFileParser()
		cp.readfp(fileobj)
		
		# Copy data
		for s in cp.sections():
			if s not in self.IGNORED_SECTIONS:
				for o in cp.options(s):
					v = cp.get(s, o)
					if "\n" in v: v = v.split("\n")
					self.values[o] = v
		
		# Add default values
		if 'type' not in self.values:
			self.type = ST_SIMPLE	# Systemd default
		
		# Check required fields and values
		for o in self.REQUIRED_FIELDS:
			if o not in self.values:
				raise ValueError("Required field missing: %s" % (o,))
		if self.type not in SYSTEMD_SERVICE_TYPES:
			raise ValueError("Invalid service type: %s" % (self.type,))
		if self.type == ST_DBUS:
			if "bus_name" not in self:
				raise ValueError("DBus service without BusName specified")


class UnitFileParser(ConfigParser.RawConfigParser):
	"""
	Extends RawConfigParser for parsing Unit files,
	PLUS, converts CamelCase fields into lower_case_with_underscores.
	"""
	def __init__(self):
		ConfigParser.RawConfigParser.__init__(self,
				dict_type=UnitFileParser.MultiValueDict)
	
	
	def optionxform(self, n):
		"""
		Converts option name from CamelCase to lower_case_with_underscores
		"""
		words = []
		while len(n):
			m = UnitFile.CAMEL.match(n)
			if not m : break
			word, n = m.groups()
			if word.endswith("_"): word = word[0:-1]
			words.append(word.lower())
		return "_".join(words)
	
	
	class MultiValueDict(OrderedDict):
		def __setitem__(self, k, v):
			if isinstance(v, list) and k in self:
				self[k].extend(v)
			else:
				OrderedDict.__setitem__(self, k, v)


if __name__ == "__main__":
	# Loads file specified as first argument.
	# Used only to test loading
	import sys, pprint
	u = UnitFile(open(sys.argv[1], "r"))
	print u
	pprint.pprint(u.values)
