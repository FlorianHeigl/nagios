#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# +------------------------------------------------------------------+
# |             ____ _               _        __  __ _  __           |
# |            / ___| |__   ___  ___| | __   |  \/  | |/ /           |
# |           | |   | '_ \ / _ \/ __| |/ /   | |\/| | ' /            |
# |           | |___| | | |  __/ (__|   <    | |  | | . \            |
# |            \____|_| |_|\___|\___|_|\_\___|_|  |_|_|\_\           |
# |                                                                  |
# +------------------------------------------------------------------+
#
# This file is an addon for Check_MK.
# The official homepage for this check is at http://bitbucket.org/darkfader
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

# Das ist das haesslichste Stueck Python, das ich bisher je geschrieben habe
# Aber ich wollte es fertigbauen
# Habe Kopfweh
# und brauch einfach Uebung
import subprocess
#import pprint

fs = {}

data =  file("/proc/mounts").readlines()
for line in data:
    line = line.split(" ")
    if "xfs" in line[2]:
        dev, mount = line[0], line[1]
        fragmentation = subprocess.Popen(["xfs_db", "-c", "frag", "-r", dev ], stdout=subprocess.PIPE) 
        for dev in fragmentation.stdout.readlines():
           actual, ideal, fragpct = dev.split(",")
           frag = float(fragpct.split(" ")[-1].split("%")[0])
           
        # tuck this into a dict at least now.
        fs.update( { mount : frag } )



# Mess should be over here.

msg = ""
state = 0
for mount in fs.keys():
    if fs[mount] > 70.0:
        msg = msg + "%s : %.02f%% fragmented" % (mount, fs[mount])
        state = state + 1

if state == 0:
    print "0 fs_status_XFS - OK - no heavily fragmented Filesystems"
else:
    print "1 fs_status_XFS - WARNING - %s" % msg



    
       







# My starting point looked no better.
#grep xfs /proc/mounts | awk '{print $2 ; system ("xfs_db -c frag -r "$1)}
# actual 267068, ideal 264434, fragmentation factor 0.99%
#/home
#actual 25443, ideal 18839, fragmentation factor 25.96%
