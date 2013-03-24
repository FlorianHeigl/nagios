#!/usr/bin/env python
# coding: utf-8
import requests
from requests.exceptions import ConnectionError
from argparse import ArgumentParser


# constants
NAME_FIELD = "service_description"
STATE_FIELD = "service_state"
OUTPUT_FIELD = "svc_plugin_output"
STATE_VALUES = set(["OK", "WARN", "WARNING", "CRITICAL",
                    "CRIT", "UNKNOWN", "UNKN", "PENDING", "PEND"])
# masks
error_mask = set(["OK", "PENDING", "PEND"])
critical_mask = set(["OK", "WARN", "WARNING", "UNKNOWN",
                    "UNKN", "PENDING", "PEND"])
all_mask = set([])
masks = {'all': all_mask,
         'error': error_mask,
         'critical': critical_mask}


def bind(mv, mf, *args, **kwargs):
    """
    Service function. If there is any error - returns value and error
    Otherwise return the result of application mf function to value
    """
    value = mv[0]
    error = mv[1]
    if not error:
        return mf(value, *args, **kwargs)
    return mv


def make_request(hostname, params):
    """
    Makes a request to the hostname with given params
    """
    params['output_format'] = 'JSON'
    try:
        r = requests.get(hostname, params=params)
    except ConnectionError as e:
        return ({}, str(e))
    if r.status_code != 200:
        return ({}, "")
    try:
        return (r.json(), '')
    except ValueError as e:
        return ({}, str(e))


def struturize(data):
    """
    Structurize the response from the server in a way that
    it is easier to process
    """
    names = dict((field, data[0].index(field)) for field in fields)
    struct = dict((field, [val[index] for val in data[1:]])
                  for field, index in names.iteritems())
    return (struct, '')


def validate(data):
    """
    Performs validation on data
    """
    if any(len(v) == 0 for v in data.itervalues()):
        return ({}, "No data in view.")
    # validate number of elements in each array
    if len(set([len(x) for x in data.itervalues()])) != 1:
        return (data, "Arrays are incomplete")

    for field in data:
        # validate that every item is a string or unicode
        if not all(isinstance(val, (str, unicode)) for val in data[field]):
            return (data, "Every data item should be a string")
        if field == STATE_FIELD:
            # validate that each state in possible state
            if not all(state in STATE_VALUES for state in data[field]):
                return(data, "Invalid state")
    return (data, '')


def maskify(data, mask=all_mask):
    """
    Remove the part of the data by given mask
    """
    idx = [i for i, state in enumerate(data[STATE_FIELD]) if state in mask]
    for field in data:
        data[field] = [d for i, d in enumerate(data[field]) if i not in idx]
    return (data, '')


def prettify(data):
    """
    Prepares the data to be printed
    """
    if all(x in fields for x in (STATE_FIELD, OUTPUT_FIELD)):
        for i, f in enumerate(data[OUTPUT_FIELD]):
            data[OUTPUT_FIELD][i] = ''.join(f.split('-')[1:])
    max_lens = dict((k, len(max(v, key=len))) for k, v in data.iteritems())
    for field in data:
        if field != fields[-1]:
            data[field] = [val.ljust(max_lens[field]) for val in data[field]]
    strings = []
    for i in xrange(len(data.itervalues().next())):
        s = " | ".join([data[f][i] for f in fields])
        strings.append(s)
    return (strings, '')


def process(hostname, params, mask_name):
    """
    Main function. Gets the hostname, params and mask, returns the
    output string.
    """
    data = make_request(hostname, params)
    structured_data = bind(data, struturize)
    validated_data = bind(structured_data, validate)
    masked_data = bind(validated_data, maskify, masks[mask_name])
    if any(len(x) == 0 for x in masked_data[0].itervalues()):
        return None
    output = bind(masked_data, prettify)
    if output[1]:
        return output[1]
    return '\n'.join(output[0])


if __name__ == "__main__":
    parser = ArgumentParser()
    # Host can fallback to os.hostname or something. if you don't have 
    # matching names in nagios you're just creating extra effort.
    parser.add_argument("--host", type=str, required=True)
    parser.add_argument("--view", type=str, required=True)
    parser.add_argument("--username", type=str, required=True)
    parser.add_argument("--password", type=str, required=True)
    parser.add_argument("--mask", type=str, default="all",
                        choices=masks.keys())
    opt = parser.parse_args()
    fields = [STATE_FIELD, NAME_FIELD, OUTPUT_FIELD]
    params = {'host': opt.host,
              'view_name': opt.view,
              '_username': opt.username,
              '_secret': opt.password
              }
    # we gotta make that configurable my server doesn't know yours :)
    # servername and maybe a /etc/check_mk/cli.cfg (root 400) 
    # to keep the auth key and stuff
    hostname = 'http://xen02.xenvms.de/mon1git/check_mk/view.py'
    p = process(hostname, params, opt.mask)
    if p:
        print p
