#!/bin/bash

# This script is called from OpenNebula if a VM successfully booted or 
# had a clean termination.
# In those cases, there will be a re-inventory of the Check_MK 
# services that represent single VMs.


# need to update all affected sites.
omdsites="allsvc"
omdserver="one-omd"


trip_site()
{
# This was wayyyyyy too harsh on the nagios server.
#  ssh -i ~oneadmin/.ssh/id_dsa-one2cmk $omdsite@$omdserver "
#  cmk --checks=lnx_if,qemu,one_vms -II
#  cmk -O
#  "
  ssh -i ~oneadmin/.ssh/id_dsa-one2cmk $omdsite@$omdserver "
  touch ~/tmp/check_mk/needs-reinventory
  "

}


log_data()
{
    echo "$@" >> /var/log/one/hook.log
}

log_data `date`
for omdsite in $omdsites ; do
   log_data "resetting site $omdsite, reason: $1 $2"
   OUT=`trip_site 2>&1`
   log_data "$OUT"
done
