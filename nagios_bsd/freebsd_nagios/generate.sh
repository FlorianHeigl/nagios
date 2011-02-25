#!/bin/bash
# alles scheisse,btw


# create backup copy of nagios config
cp -p /usr/local/nagios/etc/freebsd.cfg freebsd.cfg.bck
cp service /usr/local/nagios/etc/freebsd.cfg


# generate list of host-service assocs for hostgroup use
# redirect can die as soon as I'm able to make a real,list
for service in www ftp cvsup
 do 
  echo "define hostgroup {
  hostgroup_name freebsd-$service
  alias	FreeBSD $service servers
  members `grep $service freebsd.mirrors | tr '\n' ',' `
  }" >> /usr/local/nagios/etc/freebsd.cfg
done
 
echo "#### Host definitions ####" >> /usr/local/nagios/etc/freebsd.cfg
for node in `cat freebsd.mirrors`
 do cat hosttemplate | sed -e"s/lalahost/$node/g" >> /usr/local/nagios/etc/freebsd.cfg 
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
#  cp freebsd.cfg.bck /usr/local/nagios/etc/freebsd.cfg 
#fi
