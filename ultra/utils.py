#/usr/bin/env python

def replace_none(arg, val, alternate = None):
    if arg is None:
        return val
    else:
        if alternate is None:
            return arg
        else:
            return alternate