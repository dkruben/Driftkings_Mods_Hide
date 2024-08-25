# -*- coding: utf-8 -*-
from collections import namedtuple


def tuple_to_dict(dictionary):
    return {x: getattr(dictionary, x) for x in dictionary._fields}


def convert(name, dictionary):
    for key, value in dictionary.iteritems():
        if isinstance(value, dict):
            dictionary[key] = convert(name, value)
    return namedtuple(name, dictionary.keys())(**dictionary)


def convert_dict_to_namedtuple(dictionary, tuple_name="DictTuple"):
    return namedtuple(tuple_name, dictionary.keys())(**dictionary)

def convertDictToNamedtuple(dictionary):
    return namedtuple('Person', dictionary.keys())(**dictionary)

my_dict = {"name": "John", "age": 30, "city": "New York"}
my_tuple = convert_dict_to_namedtuple(my_dict, "Person")

Person = namedtuple('Person', ('city', 'age', 'name'))
default = Person('New York', 30, 'John')

print default
