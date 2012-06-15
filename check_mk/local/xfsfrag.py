#!/usr/bin/python

# Das ist das haesslichste Stueck Python, das ich bisher je geschrieben habe
# Aber ich wollte es fertigbauen
# Habe Kopfweh
# und brauch einfach Uebung
import subprocess
import pprint

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
