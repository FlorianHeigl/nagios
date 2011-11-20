#!/bin/sh

# (c) Wartungsfenster.de 2011
#



local_hostname=`hostname`
MK_CONFDIR=/etc/check_mk

# ideally have your TMPDIR on some ramdisk that can't die
if ! [[ $TMPDIR ]]; then
    TMPDIR=/var/tmp
fi



be_done()
{
    rm $TMPDIR/cmkresult.$$
}

validate()
# Verify config dir exists and that the config file exists
{
    if [ -d $MK_CONFDIR ]                                    && 
       [ -r $MK_CONFDIR/cmkserver.cfg ]                      &&
       cmkserver=`grep cmkserver  $MK_CONFDIR/cmkserver.cfg | cut -f2 -d\=` &&
         omduser=`grep omduser    $MK_CONFDIR/cmkserver.cfg | cut -f2 -d\=`  
    then
        export cmkserver omduser
    else
        echo "Please set cmkserver and omduser in"
        echo "$MK_CONFDIR/cmkserver.cfg"
        exit 1
    fi
    if ! `which check_mk_agent >/dev/null`; then
        echo "check_mk_agent was not found in path, please install it." 
        exit 1
    fi
}

get_result()
{
   check_mk_agent > $TMPDIR/cmkresult.$$ 
}

copy_result()
{
    sshcmd='scp -o PreferredAuthentications=publickey -qC'
    $sshcmd $TMPDIR/cmkresult.$$ ${omduser}@${cmkserver}:tmp/check_mk/cmkresult.`hostname`
    if [ $? != 0 ]; then
        echo "Failed to submit agent output via SCP"
    fi
}

   # main :)
   validate    &&
   get_result  &&
   copy_result 
   # always cleanup
   be_done
