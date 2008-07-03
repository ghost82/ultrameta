#/usr/bin/env python

from utils import replace_none
import containers
import unittest

class TypeDefinitionTests(unittest.TestCase):
    
    def setUp(self):
        self.tlc = Specification(str, validation=validators.length(3))
        self.small = Specification(int, validation=validators.bounds(minimum = 0, maximum = 8))
        
        self.atom_type = TypeDefinition(str)
        self.restriction_str = TypeDefinition(self.tlc)
        self.restriction_int = TypeDefinition(self.small)
        
        self.list_type = TypeDefinition([int])
        self.restriction_list = TypeDefinition([self.tlc])
        
        self.map_type = TypeDefinition({int: str})
        self.restriction_map_key = TypeDefinition({self.tlc: int})
        self.restriction_map_val = TypeDefinition({int: self.tlc})

        self.tuple_type = TypeDefinition((int, str, float))
        self.mixed_type = TypeDefinition([{(int, int): str}])
    
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
    
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(unittest.TestLoader().loadTestsFromTestCase(TypeDefinitionTests))        
