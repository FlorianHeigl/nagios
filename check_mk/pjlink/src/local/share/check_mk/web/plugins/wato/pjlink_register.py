#!/usr/bin/python

#import required to register agent
from cmk.gui.plugins.wato import (
    RulespecGroup,
    monitoring_macro_help,
    rulespec_group_registry,
    rulespec_registry,
    HostRulespec,
)
#import structure where special agent will be registered
from cmk.gui.plugins.wato.datasource_programs import RulespecGroupDatasourcePrograms

#Some WATO form definition, to ask user for port number
def _valuespec_special_agent_pjlink():
    return Dictionary(
        title=_("PJ-Link Special Agent"),
        help=_("This agent is responsible for check if something response on given http port"),
        optional_keys=[],
        elements=[
            ("port", TextAscii(title=_("Lamp Lifetime in hours"), allow_empty=True)),
        ],
    )


#In that piece of code we registering Special Agent
rulespec_registry.register(
    HostRulespec(
        group=RulespecGroupDatasourcePrograms,
        #IMPORTANT, name must follow special_agents:<name>, 
        #where filename of our special agent located in path local/share/check_mk/agents/special/ is  agent_<name>
        name="special_agents:pjlink",
        valuespec=_valuespec_special_agent_pjlink,
    ))

