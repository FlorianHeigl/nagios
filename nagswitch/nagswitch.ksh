#!/usr/local/bin/ksh93
# Copyright Florian Heigl(2008) 
# availability / other licences upon request. i refuse to think about it now.
# no warranties. 


# Syntax to be
# nagswitch -n <switch name> -g <hostgroup name> [-i <switch ip address] [-c "Description String"] 


# Variables
naghostname=""
# ex: naghostname="vendor-model-num"	
# mandatory: switch hostname as used by nagios
#
naghostname_ip=""
# ex: naghostname_ip="192.168.0.1"	
# mandatory: alternate ip for accessing the switch in case the nagios hostname
# is not resolvable or the visible hostname isnt routable etc.
# obviously this should be optional
# IPv6 addresses should work just as fine
#
naghostgrp=""
# ex: naghostgrp="lanswitches"
# mandatory: nagios hostgroup the device should be added to, must be predefined
# it would be possible, but not helpful to use something like "default" for 
# small environments (i guess)
#
#numports=16			# number of switchports
# obsolete, removed, 
# will be enumerated via snmp, unless specified
# there are a few pieces that would not work with the switch being unreachable
# needs to some consideration
# also it seems some switches allow for per-vlan statistics and other stuff
# that will be shown as interfaces and need to be filtered, probably via
# iftype (dealt with, as long as the interface types are ethernet-ish
#


naghostname="msu1800-1"	
naghostname_ip="192.168.15.35"	
nagdescr="Nortel ESU 1800"
naghostgroup=switches

#naghostname="c2924xl-1"
#naghostname_ip="192.168.15.37"
#naghostgroup="switches"

#naghostname="lcs-gs9420-1"
#naghostname_ip="192.168.15.36"
#nagdescr="Longshine GS9420"
#naghostgroup="switches"

#naghostname="linksys"
#naghostname_ip="192.168.10.17"
#nagdescr="Linksys WRT54GL DDWRT"
#naghostgroup="routers"


SNMPCMD="snmpget -c public -v 1"
SNMPWCMD="snmpwalk -c public -v 1"


# exit if our needed vars are unset, especially now that i can't supply them 
# via cmd line

if [ -z $naghostname ] || [ -z naghostname_ip ]
then
    echo "Please supply needed information, see source."
fi

# define a description string if not already set
if [ -z $nagdescr ]
then
    nagdescr=$( $SNMPCMD $naghostname SNMPv2-MIB::sysName.0 | cut -f3 -d\: )
fi


# start writing info to cfg file

# start out by host definition, use host/service templates
echo "define host{
        use             generic-switch
        host_name       $naghostname
        alias           $nagdescr 
        address         $naghostname_ip
        hostgroups      switches
        }" > $naghostname.cfg


# set up generic services (ping, uptime)
echo "define service{
	use			generic-service
	host_name		$naghostname
	service_description	PING
        service_description     PING
        check_command           check_ping!200.0,20%!600.0,60%
        normal_check_interval   5
        retry_check_interval    1
}" >> $naghostname.cfg

#set up specific services (ssh, http[s], telnet, snmp)



# set up services for each port (link state, bandwidth)
# to be added: 
# these will all be needed to make this script actually useful, as in 
# reducing false positives
# * error counters
# * full duplex / autoneg (must be adjustable to full-duplex manual for 
#   people still living in '90s, UNLESS gigabit link)
# * bandwidth monitoring right now uses random values for fast ethernet, 
#   need to find a query link speed to get those right
# 
# * also, need to set up according to admin/oper states:
#   op down at scan: 	no notifications
#   admin down at scan:	no active checks 
#   on the other hand it seems admin state is only implemented on tolerably 
#   good switches, so i can't use that. for now i'll just filter ports that
#   are down on scan. 



# id of switchport padded with two zeroes, not yet according to port number
# this isnt real padding, obviously. wc -c on number of ports should 
# do though, but i.e. vlan ports (1026++ on my switch) should be excluded

typeset -Z02 idpad
all_port_services=""

for id in $( $SNMPWCMD $naghostname_ip IF-MIB::ifIndex | awk '{print $NF}' )

do 

# gather interface type (ethernet...) and state
ifType="$( $SNMPCMD $naghostname_ip IF-MIB::ifType.$id | awk '{print $NF}' | cut -f1 -d\( )"
ifOperStatus="$( $SNMPCMD $naghostname_ip IF-MIB::ifOperStatus.$id | awk '{print $NF}'| cut -f1 -d\( )"

if [ "X${ifType}" = "XethernetCsmacd" ] && [ "X${ifOperStatus}" = "Xup" ] || [ "X${ifType}" = "XgigabitEthernet" ] && [ "X${ifOperStatus}" = "Xup" ]

then

idpad="$id"

# i wonder if anyone work prefer the ifName supplied names (1/10...)
# geeks probably yes, monitoring people probably not.
# 
echo "define service{
        use                     generic-service
        host_name               $naghostname
        service_description     Port $idpad Link Status
        check_command           check_snmp!-C public -o ifOperStatus.$id -r 1 -m RFC1213-MIB
        }
define service{
        use                     generic-service
        host_name               $naghostname
        service_description     Port $idpad Bandwidth Usage
        check_command           check_local_mrtgtraf!/usr/local/www/mrtg/${naghostname_ip}_${id}.log!AVG!1000000,1000000!5000000,5000000!10
        }
define servicedependency{
	host_name			$naghostname
	service_description		Port $idpad Link Status
	dependent_host_name		$naghostname
	dependent_service_description	Port $idpad Bandwidth Usage
	execution_failure_criteria	w,c,u
	notification_failure_criteria	w,c,u
	}" >> $naghostname.cfg

# this only worked if port 1 was up ;)
if [ -z $all_port_services ]
 then 
   all_port_services="Port $idpad Link Status, Port $idpad Bandwidth Usage"
 else
   all_port_services="${all_port_services},Port $idpad Link Status, Port $idpad Bandwidth Usage"
fi


fi


done
echo "define servicedependency{
        host_name                       $naghostname
        service_description             PING
        dependent_host_name             $naghostname
        dependent_service_description   $all_port_services
        execution_failure_criteria      w,c,u
        notification_failure_criteria   w,c,u
}" >> $naghostname.cfg

