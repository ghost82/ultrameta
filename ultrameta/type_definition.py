#/usr/bin/env python

from itertools import izip
from utils import replace_none
import validators
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

class ContainerTests(unittest.TestCase):

    def append(list, val):
        list.append(val)
        
    def assign(map, key, val):
        map[key] = val
    
    def test_list_of_int(self):
        type_def = TypeDefinition([int])
        test_list = ListProxy([1, 2, 3]).withtype(type_def)
        self.assertEqual(test_list, [1, 2, 3])
        self.assertEqual(test_list[1], 2)
        self.assertEqual(len(test_list), 3)
       
    def test_type_safe_list_of_int(self):
        type_def = TypeDefinition([int])
        test_list = ListProxy([]).withtype(type_def)
        self.assertRaises(TypeError, self.append, test_list, 'a')
        
    def test_map_from_str_to_int(self):
        type_def = TypeDefinition({str:int})
        test_map = DictionaryProxy({'a' : 1, 'b' : 2}).withtype(type_def)
        self.assertEqual(test_map['a'], 1)
        test_map = DictionaryProxy({'a' : 1, 'b' : 'c'})
        self.assertRaises(TypeError, test_map.withtype, type_def)
        
    def test_type_safe_map_from_str_to_int(self):
        type_def = TypeDefinition({str:int})
        test_map = DictionaryProxy({}).withtype(type_def)
        self.assertRaises(TypeError, self.assign, test_map, 1, 1)
        self.assertRaises(TypeError, self.assign, test_map, 'a', 'a')
        
    def test_tuple_int_int_str_int(self):
        type_def = TypeDefinition((int, int, str, int))
        test_tuple = TupleProxy((1, 2, 'c', 3)).withtype(type_def)
        self.assertEqual(test_tuple, (1, 2, 'c', 3))
        self.assertEqual(test_tuple[1], 2)
        self.assertRaises(TypeError, self.assign, test_tuple, 2, 4)
        
    def test_tuple_type_safety(self):
        type_def = TypeDefinition((int, int, str, int))
        test_tuple = TupleProxy((1, 2, 3))
        self.assertRaises(TypeError, test_tuple.withtype, type_def)

def InvariantChecked(self, func):
    
    def wrapper(val):
        func(val)
        self._invariant_checks()
        
    return wrapper
    
class WithMixin(object):

    def __with(self, type_definition = None, invariant_checks = None):
        self._type_definition = replace_none(getattr(self, '_type_definition', None), type_definition)
        self._invariant_checks = replace_none(getattr(self, '_invariant_checks', None), invariant_checks)
        
        methods, proxies = self.proxy_definitions()
        if self._type_definition:
            for method, proxy in izip(methods, proxies):
                setattr(self, method, proxy)
        if self._invariant_checks:
            for method in methods:
                setattr(self, method, InvariantChecked(self, getattr(self, method)))

        return self             

    def withtype(self, type_definition):
        if not type_definition.type_match(self):
            raise TypeError()
        return self.__with(type_definition = type_definition)
        
    def withinvariants(self, invariant_checks):
        invariant_checks()
        return self.__with(invariant_checks = invariant_checks)
        
    def proxy_definitions(self):
        raise NotImplementedError()
        
class ListProxy(list, WithMixin):

    def proxy_definitions(self):
        return ['append', '__setslice__'], [self.__append_type_safe, self.__setslice_type_safe]

    def __append_type_safe(self, val):
        if self._type_definition.contents_match(val, None):
            super(ListProxy, self).append(val)
        else:
            raise TypeError('%s is a %s and cannot be appended to a %s' % 
                (val, type(val), self._type_definition))

    def __setslice_type_safe(self, i, j, val):
        if self._type_definition.type_match(val):
            return super(ListProxy, self).__setslice__(i, j, val)
        else:
            raise TypeError('%s is not a %s' % (val, self._type_definition))        

            
class TupleProxy(tuple, WithMixin):

    def proxy_definitions(self):
        return [], []
    
class DictionaryProxy(dict, WithMixin):

    def proxy_definitions(self):
        return ['__setitem__'], [self.__setitem_type_safe]

    def __setitem_type_safe(self, key, val):
        if self._type_definition.contents_match(val, key):
            super(DictionaryProxy, self).__setitem__(key, val)
        else:
            raise TypeError('%s is not a %s' % ((key, val), self._type_definition))

leaf_name = 'leaf'
tuple_name = 'tuple'
sequence_name = 'sequence'
mapping_name = 'mapping'

container_definitions = {  
    type(None) : (None, leaf_name) ,
    tuple : (TupleProxy, tuple_name), 
    list : (ListProxy, sequence_name),
    dict : (DictionaryProxy, mapping_name) }
    
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
    suite1 = unittest.TestLoader().loadTestsFromTestCase(TypeDefinitionTests)
    suite2 = unittest.TestLoader().loadTestsFromTestCase(ContainerTests)
    master = unittest.TestSuite()
    master.addTests((suite1, suite2))
    unittest.TextTestRunner(verbosity=2).run(master) 
    
