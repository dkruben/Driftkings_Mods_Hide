# -*- coding: utf-8 -*-
from collections import namedtuple


def tuple_to_dict(dictionary):
    return {x: getattr(dictionary, x) for x in dictionary._fields}


def convert(name, dictionary):
    for key, value in dictionary.iteritems():
        if isinstance(value, dict):
            dictionary[key] = convert(name, value)
    return namedtuple(name, dictionary.keys())(**dictionary)
