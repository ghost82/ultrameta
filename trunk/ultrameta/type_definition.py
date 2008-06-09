#/usr/bin/env python

# TODO:

# understand what int or None type would be and how to represent it.

import containers
from utils import replace_none

leaf_name = 'leaf'
tuple_name = 'tuple'
sequence_name = 'sequence'
mapping_name = 'mapping'

_container_definitions = {  
    type(None) : (None, leaf_name) ,
    tuple : (containers.tuple_proxy, tuple_name), 
    list : (containers.list_proxy, sequence_name),
    dict : (containers.dictionary_proxy, mapping_name) }
    
_type_match = {
    leaf_name: lambda self, val: self._type is None or isinstance(val, self._type),

    tuple_name: lambda self, val: (isinstance(val, self._container) and
                    all(self.contents_match(i, pos) for pos, i in enumerate(val)) and
                    len(val) == len(self._tuple_contents)),

    sequence_name: lambda self, val: (isinstance(val, self._container) and
                    all(self.contents_match(i) for i in val)),

    mapping_name: lambda self, val: (isinstance(val, self._container) and 
                    all(self.contents_match(v, k) for (k, v) in val.items())) }
            
_contents_match = {
    sequence_name: lambda self, val, key: self._contents.type_match(val),
    
    tuple_name: lambda self, val, key: self._tuple_contents[key].type_match(val),
    
    mapping_name: lambda self, val, key: (self._key_contents.type_match(key) and 
                    self._value_contents.type_match(val)),
    
    leaf_name: lambda self, val, key: None }

class specification(object):

    def __init__(self, prototype, invariants = None, **restrictions):
        self.prototype = prototype
        self.restrictions = restrictions
        self.invariants = replace_none(invariants, [])
        
class _type_definition(object):

    def __init__(self, argument, **kwargs):
        if isinstance(argument, specification):
            prototype = argument.prototype
            self.restrictions = argument.restrictions
        else:
            prototype = argument
            self.restrictions = kwargs
        
        if prototype is not None and type(prototype) in _container_definitions:
            self._container = type(prototype)
            self._proxy, self._category = _container_definitions[type(prototype)]
            if self._category == sequence_name:
                self._contents = _type_definition(prototype[0])
            elif self._category == mapping_name:
                self._key_contents = _type_definition(prototype.keys()[0])
                self._value_contents = _type_definition(prototype.values()[0])
            elif self._category == tuple_name:
                self._tuple_contents = tuple(_type_definition(i) for i in prototype)
        else:
            self._category = leaf_name
            self._type = prototype

    def subhandler(self, *args, **kwargs):
        return kwargs[self._category](self, *args, **kwargs)

    def type_match(self, val):
        if 'validation' in self.restrictions:
            return _type_match[self._category](self, val) and self.restrictions['validation'](val)
        else:
            return _type_match[self._category](self, val)
        
    def contents_match(self, val, key = None):
        return _contents_match[self._category](self, val, key)

    def proxy(self, val, do_invariant_checks):
        if self._category == leaf_name:
            return val
        else:
            return self._proxy(val).withtype(self).withinvariants(do_invariant_checks)

    def _type_repr(self):
        if self._category == leaf_name:
            return '%s' % self._type.__name__
        elif self._category == tuple_name:
            return '(%s)' % ', '.join([i._type_repr() for i in self._tuple_contents])
        elif self._category == sequence_name:
            return '[%s]' % self._contents._type_repr()
        else:
            return '{%s: %s}' % (self._key_contents._type_repr(), self._value_contents._type_repr())
            
    def __repr__(self):
        return 'ultra._type_description(' + self._type_repr() + ')'


if __name__ == '__main__':
    
    import unittest
    import validators
    
    class Tests(unittest.TestCase):
    
        def setUp(self):
            self.tlc = specification(str, validation=validators.length(3))
            self.small = specification(int, validation=validators.bounds(minimum = 0, maximum = 8))
            
            self.atom_type = _type_definition(str)
            self.restriction_str = _type_definition(self.tlc)
            self.restriction_int = _type_definition(self.small)
            
            self.list_type = _type_definition([int])
            self.restriction_list = _type_definition([self.tlc])
            
            self.map_type = _type_definition({int: str})
            self.restriction_map_key = _type_definition({self.tlc: int})
            self.restriction_map_val = _type_definition({int: self.tlc})

            self.tuple_type = _type_definition((int, str, float))
            self.mixed_type = _type_definition([{(int, int): str}])
        
        def test_atom(self):
            self.assertEqual(self.atom_type.type_match(12), False)
            self.assertEqual(self.atom_type.type_match('any string'), True)
            
        def test_restriction(self):
            self.assertEqual(self.restriction_str.type_match('foo'), True)
            self.assertEqual(self.restriction_str.type_match('foobar'), False)
            
        def test_range(self):
            self.assertEqual(self.restriction_int.type_match(3), True)
            self.assertEqual(self.restriction_int.type_match(10), False)

        def test_list(self):
            self.assertEqual(self.list_type.type_match(4), False)
            self.assertEqual(self.list_type.type_match([4]), True)
            
        def test_list_restriction(self):
            self.assertEqual(self.restriction_list.type_match(['foo', 'bar']), True)
            self.assertEqual(self.restriction_list.type_match(['foobar', 'a']), False)

        def test_map(self):
            self.assertEqual(self.map_type.type_match({1: 'a', 2: 'bb', 3: 'cccc'}), True)
            self.assertEqual(self.map_type.type_match({1: 'a', 'a': 1}), False)
            
        def test_map_restriction_key(self):
            self.assertEqual(self.restriction_map_key.type_match({'abc': 123}), True)
            self.assertEqual(self.restriction_map_key.type_match({'a': 123}), False)
            
        def test_map_restriction_value(self):
            self.assertEqual(self.restriction_map_val.type_match({1: 'abc'}), True)
            self.assertEqual(self.restriction_map_val.type_match({1: 'a'}), False)
            
        def test_others(self):
            self.assertEqual(self.tuple_type.type_match((1, 'a', 4.5)), True)
            self.assertEqual(self.tuple_type.type_match((1, 'abc')), False)
            
        def test_mixed(self):
            self.assertEqual(self.mixed_type.type_match([{(1, 3) : 'onethree', (0, 1) : 'zeroone'},
                { (0, 0) : 'done' }]), True)
            
            
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)
