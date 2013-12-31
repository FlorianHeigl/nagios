#!/usr/bin/python

# A proof of concept Nagios check for MooseFS
# This check is supposed to warn you with a WARNING 
# if there's missing replicas
# or CRITICAL if there's no replicas left for some data

# HOWTO:
# needs MooseFS libs (included)
# access is via standard port, no auth needed(!)

# CAVEAT: 
# All other MooseFS checks I write will be directly for Check_MK


from moosefs import MooseFS
import sys


def sh_syntax():
   print """

Syntax:
nagios-moosefs-replicas.py [-H <mfsmaster hostname>]

If the mfsmaster is not specified, the check will try to default to 'mfsmaster'

"""


# Handle arguments, help or hostname to check
if   len(sys.argv) == 2 and "-h" in sys.argv:
    sh_syntax()
    sys.exit(5)
elif len(sys.argv) == 3 and "-H" == sys.argv[1]:
     mfsmaster=sys.argv[2] 
else:
    # Fall back to the default hostname, if none other was given.
    mfsmaster="mfsmaster"

# Try building a connection, crash-land on any error.
try:
    mfsobj = MooseFS(masterhost=mfsmaster)
except:
    print "UNKNOWN - Error occured connecting to mfsmaster"
    # Raise should only be done if connected to a terminal, so it doesn't spill into nagios.
    #raise
    sys.exit(3)

# if connection succeeded, load the table of replicas.
matrix  =  mfsobj.mfs_info()['matrix']


# For easy reuse of check in Check_MK
if not nagios_state_names:
    nagios_state_names = { 
        0 : "OK",
        1 : "WARN",
        2 : "CRIT",
        3 : "UNKW" }


state = 0
goal  = 0
msg   = ""


# parse the table per-goal (horizontally)
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

      # slide through the matrix row, checking for non-zero entries (vertically)
      # only look at entries _less_ than the designated goal.
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


# Add a message in case there were no errors.
if state == 0:
   msg = "No errors"

print nagios_state_names[state] + " - " + msg

sys.exit(state)

