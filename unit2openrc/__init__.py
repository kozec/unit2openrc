#!/usr/bin/env python2

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
	
pass