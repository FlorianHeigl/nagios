#!/usr/bin/python

# A proof of concept Nagios check for MooseFS
# This check is supposed to warn you with a WARNING 
# if there's missing replicas
# or CRITICAL if there's no replicas left for some data

# TODO: 
# needs to sys.exit with "state" (otherwise Nagios will show OK!!!)

# HOWTO:
# needs MooseFS libs
# adjust your "masterhost" below
# access is via standard port,
# moosefs does not authenticate this, so it should just work.

# CAVEAT: 
# Doesn't comply to Nagios plugin dev guide (no -h support)
# All other MooseFS checks I write will be directly for Check_MK


from moosefs import MooseFS

weavers = MooseFS(masterhost='192.168.10.162')
matrix  =  weavers.mfs_info()['matrix']


state = 0
goal = 0
msg = ""

for goal_data in matrix:

    cur_goal = goal
    goal = goal + 1

    chunks_per_goal = matrix[cur_goal]

    # skip goal 0 chunks
    if cur_goal == 0:
      continue

    else:
      i = 0
      undergoal = 0

      while i < cur_goal:
         undergoal = undergoal + chunks_per_goal[i]
         i = i + 1
      if undergoal:
         # lost data:
         if   chunks_per_goal[0] > 0:
            state = max(state, 2)
            msg += "%i chunks of goal %i data lost" % (undergoal, cur_goal)
         # missing replicas
         else:
            state = max(state, 1)
            msg += "%i chunks of goal %i lack replicas" % (undergoal, cur_goal)
      else:
         state = max(state, 0)


nagios_state_names = { 
    0 : "OK",
    1 : "WARN",
    2 : "CRIT",
    3 : "UNKW" }

if state == 0:
   msg = "No errors"

print nagios_state_names[state] + " - " + msg


