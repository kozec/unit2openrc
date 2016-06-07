#!/usr/bin/env python2
"""
Unit2OpenRC - Constants

Mainly paths to where input and outuput files are located.
"""
from __future__ import unicode_literals

# Paths
INIT_D = "/etc/init.d"
RUN_D = "/run"
DAEMON_DIR = "/usr/bin"		# Directory where daemon executables are stored (currently not used in any meaningfull way)
UNIT_DIRS = [
	# Directories where systemd units are placed, in order of precedence.
	'/etc/systemd/system',
	'/run/systemd/system',
	'/usr/lib/systemd/system',
]

# Settings
ALLOW_DBUS = True			# If set to True, it is possible to convert 'dbus' service type.
							# Requires dbus-service-wait executable to be available.
AUTO_IGNORED = [
	# In auto-generate mode (unit2openrc -a), services with names containing
	# any string from this list are ignored
	'@', 'systemd-', 'dbus-org', 'plymouth',
]
AUTO_IGNORED_EXACT = [
	# In auto-generate mode (unit2openrc -a), services with these exact
	# filenames are ignored
	'autovt@.service',
	'console-getty.service',
	'console-shell.service',
	'container-getty@.service',
	'debug-shell.service',
	'emergency.service',
	'getty@.service',
	'initrd-cleanup.service',
	'initrd-parse-etc.service',
	'initrd-switch-root.service',
	'initrd-udevadm-cleanup-db.service',
	'kmod-static-nodes.service',
	'ldconfig.service',
	'quotaon.service',
	'rescue.service',
	'serial-getty@.service',
	'debug-shell.service'
]

# Executables and rc file commands
START_STOP_DAEMON = "start-stop-daemon"
DBUS_SERVICE_WAIT = "dbus-service-wait"
EBEGIN = "ebegin"
EEND = "eend"
BEFORE = "before"
AFTER = "after"

# Messages
STARTING = "Starting %s '%s'"
STOPPING = "Stopping %s '%s'"

# Service types (shared by UnitFile *and* RCFile, but RCFile uses only SIMPLE and FORKING types)
ST_SIMPLE	= 'simple'
ST_FORKING	= 'forking'
ST_ONESHOT	= 'oneshot'
ST_DBUS		= 'dbus'
SYSTEMD_SERVICE_TYPES = ( ST_SIMPLE, ST_FORKING, ST_ONESHOT, ST_DBUS )
RC_SERVICE_TYPES = ( ST_SIMPLE, ST_FORKING, ST_DBUS )

UNIT_NAMES_DICT = {
	"network.target"		: "net",
	"nss-lookup.target"		: "net",
	"local-fs.target"		: "localmount",
	"remote-fs.target"		: "netmount",
	"network-online.target"	: "net-online",
	"dbus.socket"			: "dbus",
}

# Header of generated rc file
RC_HEADER = """#!/usr/bin/openrc-run
# This file was auto-generated from %(source_file_name)s
# by %(unit2openrc)s.

"""