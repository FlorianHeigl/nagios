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
shost=`echo $1 | cut -f1 -d\.`
backupclient=${shost}.backup

amuser="amanda"
amcommand="amcheck DailySet1 $backupclient"

msg=""
state=0

# su test
su - $amuser -c "cd ~${amuser} && true"
if [ $? != 0 ]; then
   echo "Cannot switch to amanda user, exiting."
   exit 3
fi

erg="`su - $amuser -c \"$amcommand\"`"
# Return code not used atm
ret=$?


# check for broken client def
if echo "$erg" | grep "matches neither a host nor a disk" > /dev/null ; then
   msg="$msg Client is not configured for backups"
   state=$(( $state + 1 ))
fi

# check for client access issue
if echo "$erg" | grep "ERROR: NAK" > /dev/null ; then
   msg="$msg Client is configured for backups, but they're not working."
   state=$(( $state + 1 ))
fi

if echo "$erg" | grep "Client check: 1 host.* 0 problems" > /dev/null ; then
   msg="$msg Client is OK"
fi

if [ $state = 0 ]; then
   msg="OK -${msg}"
else
   msg="CRIT -${msg}"
fi

echo "$msg"
exit $state
