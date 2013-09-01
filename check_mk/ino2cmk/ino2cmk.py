#!/usr/local/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# ino2cmk.py
# Florian Heigl 2013 fh@florianheigl.de
# License: WAR-FTP

# Config parser for writing check_mk config from external data.
# the data is, in this case from inoXML a proprietary config management
# system (that sadly wasn't opensourced right from the start, it's quite 
# powerful)
#
#
# example input:
# Server ID, Service Level,  Status, Custom mods, Build version, hostname, customer (ID and name)
# 12      TESTING         ENABLED         10/10   i386_freebsd_9.1_build1         host-12.customer-intern.de   123 (customer name)
#
#
# TODOS:
# Read live data instead of the dump
# Store and compare an output, so inactive servers can be preserved for a while
# write hosts count for .wato file, so WATO shows correct contents.
# write wato attributes (like IP address)
# Only use numeric customer IDs
# write a file with the host tags and groups
# write lock files for hosts and subdirs
# unsorted folder is not being written.

# Done:
# Write WATO files and tarball them. (:

import os
import subprocess


def read_data(source):
    d = {}

    if source != "backup" and os.path.isfile(source):
       f = open(source, 'r')
       for line in f:
         parts = line.split("\t")
         if parts[0] == "ID":
            continue
         stripped = [ item.strip() for item in parts ]
         id, usage, status, admin_commands, buildid, nil, hostname, customer = stripped
         if stripped[2] == "ENABLED":
              d[id] = { "usage" : usage, "buildid" : buildid, "hostname": hostname, "customer": customer }
       f.close() 
    else:
       print "error reading data file"

    return d


def build_tags(server_data):
    # each wato folder becomes a key in here with a list of id's
    wato_folders = {}
    all_customers      = []
    all_customer_names = []

    for id in server_data.keys():
      wato_folder = ""
      server_data[id]["tags"] = []

      # Use the service from inomgr
      server_data[id]["tags"].append(server_data[id]['usage'].lower())

      # find the customer name and change the output a little.
      customer_name = server_data[id]["customer"].replace("(","").replace(")","").replace(" ","_").replace(".","")
      customer_id = server_data[id]["customer"].split("(")[0]

      # apply a tag to point out customer systems
      # can probably be replaced via rule.
      if "ispname" not in customer_name.lower():
         server_data[id]["tags"].append("kundensystem")
      server_data[id]["tags"].append(customer_id)
      if customer_id not in all_customers:
          all_customers.append(customer_id)
      if customer_name not in all_customer_names:
          all_customer_names.append(customer_name)


      # Now gather more info from the inoXML config
      dc = "unknown"
      buildhost = False
      ucarp  = False
      backup = False
      
      # This is slow.
      # if you need to work with more systems, please fix.
      syscfg  = open('/home/me/inoxmldoc/%s.cfg' % id, 'r')
      for line in syscfg.readlines():
          # Datacenter location
          if   "in1" or "rz1" in line:
              dc = "rz1"
          elif "in2" or "rz2" in line:
              dc = "rz2"
          if "tinderbox" in line:
              buildhost = True
          if "ucarp" in line:
              ucarp = True
          if "set1daily" in line or "set2daily" in line:
              backup = True
          
          
      # Apply tags for items we found.
      # note, only stuff that is needed to select a good WATO folder or enforcing rules
      # needs to be done here. everything else ----> via inventory.
      server_data[id]["tags"].append(dc)
      if buildhost:
          server_data[id]["tags"].append("buildhost")
      if ucarp:
          server_data[id]["tags"].append("ha-cluster")
          server_data[id]["tags"].append("ucarp")
          # Change usage to critical for clusters. Seems they matter.
          server_data[id]["usage"] = "critical"
      if backup:
          server_data[id]["tags"].append("backup")

      # Apply the fileagent tag to all of them.
      server_data[id]["tags"].append("fileagent")

      # Note: Don't add the 'wato' tag here.

      # Finally, handle WATO folders.
      if "kundensystem" in server_data[id]["tags"]:
          w = "/wato/billable/servers/"
      elif "buildhost" in server_data[id]["tags"]:
          w = "/wato/internal/buildenv/"
      elif server_data[id]["usage"] == "testing":
          w = "/wato/testing/"
      else:
          w = "/wato/undefined/"

      if w not in wato_folders.keys():
          wato_folders.update({ w : [] })
      
      # add the server's id to wato folder
      wato_folders[w] += [ id ]


    return server_data, all_customers, all_customer_names, wato_folders
      



# Print the config file contents
def write_cfg(server_data, wato_folder, member_ids):

    if not os.path.exists("./%s" % wato_folder):
        os.makedirs("./%s" % wato_folder)

    mkconf = open("./%shosts.mk" % wato_folder, 'wb')

    mkconf.write("""# Written by in2cmk.py
# encoding: utf-8

all_hosts += [
""")

    for id in member_ids:
        tags = ("|").join(server_data[id]['tags'])
        host_entry = "%s|%s" % (server_data[id]['hostname'], tags)
        mkconf.write("""    '%s|wato|"/" + FOLDER_PATH + "/"',\n""" % host_entry)

    mkconf.write("]\n")

    # Let me do something about the IP addresses for you.
    mkconf.write("ipaddresses.update({")
    for id in server_data.keys():
        if not ".public-domain.de" in server_data[id]["hostname"]:
            mkconf.write("""    "%s" : "127.0.0.1",\n""" % server_data[id]["hostname"])
    mkconf.write("})\n")

    mkconf.close()



# MAIN...

# check i'm in the right directory, there should be a WATO subfolder
if not os.path.exists("./wato"):
    print "sad sad" 

server_data = read_data("workdump")
server_data, all_customers, all_customer_names, wato_folders = build_tags(server_data)


for wato_folder, member_ids in wato_folders.items():
    write_cfg(server_data,wato_folder,member_ids)

# output the customer tags
print "tag group customers:" 
for customer_id in all_customers:
    print customer_id
    for customer_name in all_customer_names:
         print customer_name
         if customer_name.startswith(customer_id):
             print "customer_id : customer_name"

