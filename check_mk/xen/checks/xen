#
#  check_mk plugin for xen
#  
#  This file is the Check plugin file and is to be kept at local/lib/check_mk/base/plugins/agent_based/ directory of the Checkmk server. Filename should end with py. 
#  This works along with the agent plugin file named xen_vms which is to be kept at  /usr/lib/check_mk_agent/plugins/ folder of the xen base server which is to be monitored.
#

from .agent_based_api.v1 import *

#def discover_xen_vms(section):
#    (Service(item="VM %s" % line[1], parameters={}) for line in section if line[0] == "vm")

def discover_xen_vms(section):
    for line in section:
        if line[0] == "vm":
              yield Service(item=line[1])

def check_xen_vms(item, section):
    for line in section:
        xentype = line[0]
        if xentype == "vm":
            xentype, vmname, status = line
            if vmname == item:
                    if status == "running":
                        yield Result(state=State.OK, summary="OK - VM %s status is %s" % (item, status))
                        return
                    elif status == "paused":
                        yield Result(state=State.WARN, summary="WARN - VM %s status is %s" % (item, status))
                        return
                    elif status == "crashed":
                        yield Result(state=State.CRIT, summary="CRIT - VM %s status is %s" % (item, status))
                        return
                    else:
                        yield Result(state=State.UNKNOWN, summary="UNKNOWN - VM %s status unknown" % (item, status))
                        return


register.check_plugin(
    name = "xen_vms",
    service_name = "VM %s",
    discovery_function = discover_xen_vms,
    check_function = check_xen_vms,
)
