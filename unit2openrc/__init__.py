#!/usr/bin/env python2
"""
Unit2OpenRC - common tools and classes
"""
import shlex

class ServiceConfig(object):
	""" Common part of RCFile and UnitFile """
	
	def __init__(self):
		self.__dict__['values'] = {}
	
	
	def __getattr__(self, k):
		""" Overrides getattr to provide simpler access to self.values dict """
		if k in self.values:
			return self.values[k]
		return object.__getattribute__(self, k)
	
	
	def __hasattr__(self, k):
		""" Overrides hasattr to provide simpler access to self.values dict """
		return k in self.values or object.__hasattribute__(self, k)
	
	
	def __contains__(self, k):
		""" Overrides 'in' operator to provide simpler access to self.values dict """
		return k in self.values
	
	
	def __setattr__(self, k, v):
		""" Redirects all new values into self.values dict """
		if not k in self.__dict__:
			self.values[k] = v
		else:
			return object.__setattr__(self, k, v)
	
	
	def __str__(self):
		return "<%s '%s'>" % (self.__class__.__name__, self.description, )


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


def ensure_list(v):
	""" Returns v if v is list; returns [v] otherwise """
	if type(v) == list: return v
	return [v]
