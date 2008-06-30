#/usr/bin/env python

import containers
from utils import replace_none

leaf_name = 'leaf'
tuple_name = 'tuple'
sequence_name = 'sequence'
mapping_name = 'mapping'

container_definitions = {  
    type(None) : (None, leaf_name) ,
    tuple : (containers.TupleProxy, tuple_name), 
    list : (containers.ListProxy, sequence_name),
    dict : (containers.DictionaryProxy, mapping_name) }
    
type_match_definitions = {
    leaf_name: lambda self, val: self._type is None or isinstance(val, self._type),

    tuple_name: lambda self, val: (isinstance(val, self._container) and
                    all(self.contents_match(i, pos) for pos, i in enumerate(val)) and
                    len(val) == len(self._tuple_contents)),

    sequence_name: lambda self, val: (isinstance(val, self._container) and
                    all(self.contents_match(i) for i in val)),

    mapping_name: lambda self, val: (isinstance(val, self._container) and 
                    all(self.contents_match(v, k) for (k, v) in val.items())) }
            
contents_match_definitions = {
    sequence_name: lambda self, val, key: self._contents.type_match(val),
    
    tuple_name: lambda self, val, key: self._tuple_contents[key].type_match(val),
    
    mapping_name: lambda self, val, key: (self._key_contents.type_match(key) and 
                    self._value_contents.type_match(val)),
    
    leaf_name: lambda self, val, key: None }

class Specification(object):

    def __init__(self, prototype, invariants = None, **restrictions):
        self.prototype = prototype
        self.restrictions = restrictions
        self.invariants = replace_none(invariants, [])
        
class TypeDefinition(object):

    def __init__(self, argument, **kwargs):
        if isinstance(argument, Specification):
            prototype = argument.prototype
            self.restrictions = argument.restrictions
        else:
            prototype = argument
            self.restrictions = kwargs
        
        if prototype is not None and type(prototype) in container_definitions:
            self._container = type(prototype)
            self._proxy, self._category = container_definitions[type(prototype)]
            if self._category == sequence_name:
                self._contents = TypeDefinition(prototype[0])
            elif self._category == mapping_name:
                self._key_contents = TypeDefinition(prototype.keys()[0])
                self._value_contents = TypeDefinition(prototype.values()[0])
            elif self._category == tuple_name:
                self._tuple_contents = tuple(TypeDefinition(i) for i in prototype)
        else:
            self._category = leaf_name
            self._type = prototype

    def subhandler(self, *args, **kwargs):
        return kwargs[self._category](self, *args, **kwargs)

    def type_match(self, val):
        if 'validation' in self.restrictions:
            return type_match_definitions[self._category](self, val) and self.restrictions['validation'](val)
        else:
            return type_match_definitions[self._category](self, val)
        
    def contents_match(self, val, key = None):
        return contents_match_definitions[self._category](self, val, key)

    def proxy(self, val, do_invariant_checks):
        if self._category == leaf_name:
            return val
        else:
            return self._proxy(val).withtype(self).withinvariants(do_invariant_checks)

    def _type_repr(self):
        if self._category == leaf_name:
            if self._type is not None:
                return '%s' % self._type.__name__
            else:
                return ''
        elif self._category == tuple_name:
            return '(%s)' % ', '.join([i._type_repr() for i in self._tuple_contents])
        elif self._category == sequence_name:
            return '[%s]' % self._contents._type_repr()
        else:
            return '{%s: %s}' % (self._key_contents._type_repr(), self._value_contents._type_repr())
            
    def __repr__(self):
        return 'ultra._type_description(' + self._type_repr() + ')'
        
    def __str__(self):
        return self._type_repr()
    
