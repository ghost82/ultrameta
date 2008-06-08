#/usr/bin/env python

def replace_none(arg, val):
    if arg is None:
        return val
    else:
        return arg