#!/bin/sh -u
# Very simple check for Amanda backup clients
# uses amcheck and parses the output for ok or error strings
# Errors will take precedence.

#amcheck SetName hostname.fqdn

if [ $# != 1 ]; then
   echo "Syntax $0 hostname|hostname.fqdn" 
   exit 1
fi

# init vars
disabled=False

# we have a dedicated backup subnet & hostnames
# cut off the fqdn and append .backup
# use backupclient=$1 if you dont need this.
shost=`echo $1 | cut -f1 -d\.`
backupclient=${shost}.backup

amuser="amanda"
# set name might also need to be configurable
# send patch if you need it.
amcommand="amcheck DailySet1 $backupclient"

msg=""
state=0


# call to keep track of highest error level found
max()
{
if [ $2 > 0 ] && [ $state -lt $2 ]; then
   state=$2
fi
# should a state higher than the ones nagios knows
# be added, then we fudge it to "UNKNOWN" (3)
if [ $2 -gt 3 ]; then
   state=3
fi
}


# su test, to separate su und amanda errors
su - $amuser -c "cd ~${amuser} && true"
if [ $? != 0 ]; then
   echo "Cannot switch to amanda user, exiting."
   exit 3
fi

# run amanda selfcheck now and pick what it returns
erg="`su - $amuser -c \"$amcommand\"`"
ret=$?

# let amandas return code influence overall result
# (this catches unknown error strings)
max $state $ret


# check for broken client def
check_def()
{
# this needs to be check first since amanda returns ok for the client if it's not
# even configured.
if echo "$erg" | grep "matches neither a host nor a disk" > /dev/null ; then
   msg="$msg Client $backupclient is not configured on server"
   disabled=True
   max $state 1
fi
}


# check for client access issues and broken backup.
check_access()
{
if echo "$erg" | grep "WARNING:.*selfcheck.*failed" > /dev/null ; then
   msg="$msg Amanda failed to connect"
   max $state 2
fi
if echo "$erg" | grep "ERROR: NAK" > /dev/null ; then
   msg="$msg Amanda denies access"
   max $state 2
fi
}

check_index()
{
if echo "$erg" | grep "NOTE: index.*does not exist" | grep $backupclient > /dev/null; then
   msg="$msg No initial backup for client."
   max $state 1
fi
}


check_ok()
{
# finally, check if the overall status is considered ok
if [ $state = 0 ] && echo "$erg" | grep "Client check: 1 host.* 0 problems" > /dev/null ; then
   msg="$msg Client is OK"
fi
}


# main


check_def
# only run finer checks if active client.
# speeds up stuff a lot
if [ $disabled = "False" ]; then
  check_access
  check_index
  check_ok
fi

case $state in
  0) code="OK";;
  1) code="WARN";;
  2) code="CRIT";;
esac
echo "$code -${msg}"
exit $state
