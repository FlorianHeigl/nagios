# +------------------------------------------------------------------+
# |             ____ _               _        __  __ _  __           |
# |            / ___| |__   ___  ___| | __   |  \/  | |/ /           |
# |           | |   | '_ \ / _ \/ __| |/ /   | |\/| | ' /            |
# |           | |___| | | |  __/ (__|   <    | |  | | . \            |
# |            \____|_| |_|\___|\___|_|\_\___|_|  |_|_|\_\           |
# |                                                                  |
# | Copyright Mathias Kettner 2012             fh@mathias-kettner.de |
# +------------------------------------------------------------------+
#
# This file is not part of the official Check_MK distribution!
# The official homepage is at http://mathias-kettner.de/check_mk.
# The check_mk_remote can be found at http://bitbucket.org/darkfader
#
# check_mk is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  check_mk is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# ails.  You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.

datasource_programs += [
  ( "cat ${OMD_ROOT}/tmp/check_mk/cmkresult.<HOST>", [ 'MyHost' ]),
]

# Check command check_file_age
extra_nagios_conf="""define command {
    command_name check-mk-hostfileage 
#    command_line $USER4$/lib/nagios/plugins/check_file_age -w 60 -c 75 -f $OMD_ROOT/tmp/check_mk/cmkresult.$HOSTNAME$
    command_line $USER4$/lib/nagios/plugins/check_file_age -w 60 -c 75 -f %s/tmp/check_mk/cmkresult.$HOSTNAME$
}""" % omd_root

# Hostcheck redefinition fuer MyHost
extra_host_conf["check_command"]=[("check-mk-hostfileage", [ "MyHost" ])]


