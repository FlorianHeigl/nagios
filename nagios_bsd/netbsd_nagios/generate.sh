#!/bin/bash
# alles scheisse,btw


# create backup copy of nagios config
cp -p /usr/local/nagios/etc/netbsd.cfg netbsd.cfg.bck
cp service /usr/local/nagios/etc/netbsd.cfg


# generate list of host-service assocs for hostgroup use
# redirect can die as soon as I'm able to make a real,list
for service in www ftp cvsup
 do 
  echo "define hostgroup {
  hostgroup_name netbsd-$service
  alias	NetBSD $service servers
  members `grep $service netbsd.mirrors | tr '\n' ',' `
  }" >> /usr/local/nagios/etc/netbsd.cfg
done
 
echo "#### Host definitions ####" >> /usr/local/nagios/etc/netbsd.cfg
for node in `cat netbsd.mirrors`
 do cat hosttemplate | sed -e"s/lalahost/$node/g" >> /usr/local/nagios/etc/netbsd.cfg 
done


# go live
#nagios -v /usr/local/nagios/etc/nagios.cfg
#if [ $? = 0 ]
# then 
# restart nagios and re-read config
#  killall -HUP nagios
# else
# trash the changes
#  echo alles scheisse
#  cp netbsd.cfg.bck /usr/local/nagios/etc/netbsd.cfg 
#fi
