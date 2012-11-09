#!/usr/bin/ksh
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
# (c) Wartungsfenster.de 2011



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
