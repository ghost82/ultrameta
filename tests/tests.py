import unittest

import ultrameta.containers
import type_definition
import validators
import magic
import utils

class ContainerTests(unittest.TestCase):
    

    def append(list, val):
        list.append(val)
        
    def assign(map, key, val):
        map[key] = val
    
    def test_list_of_int(self):
        type_def = type_definition.TypeDefinition([int])
        test_list = containers.ListProxy([1, 2, 3]).withtype(type_def)
        self.assertEqual(test_list, [1, 2, 3])
        self.assertEqual(test_list[1], 2)
        self.assertEqual(len(test_list), 3)
       
    def test_type_safe_list_of_int(self):
        type_def = type_definition.TypeDefinition([int])
        test_list = containers.ListProxy([]).withtype(type_def)
        self.assertRaises(TypeError, self.append, test_list, 'a')
        
    def test_map_from_str_to_int(self):
        type_def = type_definition.TypeDefinition({str:int})
        test_map = containers.DictionaryProxy({'a' : 1, 'b' : 2}).withtype(type_def)
        self.assertEqual(test_map['a'], 1)
        test_map = containers.DictionaryProxy({'a' : 1, 'b' : 'c'})
        self.assertRaises(TypeError, test_map.withtype, type_def)
        
    def test_type_safe_map_from_str_to_int(self):
        type_def = type_definition.TypeDefinition({str:int})
        test_map = containers.DictionaryProxy({}).withtype(type_def)
        self.assertRaises(TypeError, self.assign, test_map, 1, 1)
        self.assertRaises(TypeError, self.assign, test_map, 'a', 'a')
        
    def test_tuple_int_int_str_int(self):
        type_def = type_definition.TypeDefinition((int, int, str, int))
        test_tuple = containers.TupleProxy((1, 2, 'c', 3)).withtype(type_def)
        self.assertEqual(test_tuple, (1, 2, 'c', 3))
        self.assertEqual(test_tuple[1], 2)
        self.assertRaises(TypeError, self.assign, test_tuple, 2, 4)
        
    def test_tuple_type_safety(self):
        type_def = type_definition.TypeDefinition((int, int, str, int))
        test_tuple = containers.TupleProxy((1, 2, 3))
        self.assertRaises(TypeError, test_tuple.withtype, type_def)
        
class TypeDefinitionTests(unittest.TestCase):

    def setUp(self):
        self.tlc = type_definition.Specification(str, validation=validators.length(3))
        self.small = type_definition.Specification(int, validation=validators.bounds(minimum = 0, maximum = 8))
        
        self.atom_type = type_definition.TypeDefinition(str)
        self.restriction_str = type_definition.TypeDefinition(self.tlc)
        self.restriction_int = type_definition.TypeDefinition(self.small)
        
        self.list_type = type_definition.TypeDefinition([int])
        self.restriction_list = type_definition.TypeDefinition([self.tlc])
        
        self.map_type = type_definition.TypeDefinition({int: str})
        self.restriction_map_key = type_definition.TypeDefinition({self.tlc: int})
        self.restriction_map_val = type_definition.TypeDefinition({int: self.tlc})

        self.tuple_type = type_definition.TypeDefinition((int, str, float))
        self.mixed_type = type_definition.TypeDefinition([{(int, int): str}])
    
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

class MagicTests(unittest.TestCase):

    def test_property(self):
        p = magic.Property(int)
                
    def test_object(self):
        
        class u(magic.Object):
            a = magic.Property(int)
            
            def __init__(self, init_a):
                super(u, self).__init__()
                self.a = init_a
        
        i = u(2)
        self.assertEqual(i.a, 2)
        
        i.a = 3
        self.assertEqual(i.a, 3)
        
        self.assertRaises(TypeError, setattr, i, 'a', '4')

        j = u(0)
        j.a = 4
        self.assertEqual(j.a, 4)
        self.assertEqual(i.a, 3)
        
    def test_two_properties(self):
        
        class u(magic.Object):
            b = magic.Property(int)
            a = magic.Property(str)
            
            def __init__(self, init_a, init_b):
                super(u, self).__init__()
                self.a = init_a
                self.b = init_b
                
        i = u('one', 1)
        self.assertEqual(i.a, 'one')
        self.assertEqual(i.b, 1)
        self.assertEqual(type(i).__ultra__['a'][0], 1)
        self.assertEqual(type(i).__ultra__['b'][0], 0)
        
    def test_identity(self):
        
        class u(magic.Object):
            a = magic.Identity(str)
            b = magic.Property(int)

            def __init__(self, init_a, init_b):
                super(u, self).__init__()
                self.a = init_a
                self.b = init_b
                
        i = u('one', 1)
        self.assertEqual(i.a, 'one')
        self.assertEqual(i.b, 1)
        self.assertEqual(type(i).__ultra__['a'][0], 0)
        self.assertEqual(type(i).__ultra__['b'][0], 1)
        
        j = u('one', 2)
        self.assertEqual(i, j)
        j.a = 'two'
        self.assertNotEqual(i, j)
        
    def test_collections(self):
        
        class u(magic.Object):
            a = magic.Property([int])
            
            def __init__(self, init_a = None):
                super(u, self).__init__()
                self.a = utils.replace_none(init_a, [])
                    
        i = u()
        
        self.assertEqual(i.a, [])
        i.a = [1, 2, 3]
        self.assertEqual(i.a, [1, 2, 3])
        self.assertRaises(TypeError, setattr, i, 'a', [1, 2, 'three'])
        i.a.append(4)
        self.assertEqual(i.a, [1, 2, 3, 4])
        self.assertRaises(TypeError, i.a.append, 'four')
        i.a[1:3] = [5, 6]
        self.assertEqual(i.a, [1, 5, 6, 4])
        self.assertRaises(TypeError, i.a.__setslice__, 1, 3, ['one', 'two'])
        
    def test_mappings(self):
        
        class u(magic.Object):
            a = magic.Property({int:str})
            
            def __init__(self, init_a = None):
                super(u, self).__init__()
                self.a = utils.replace_none(init_a, {})
                    
        i = u()
        
        self.assertEqual(i.a, {})
        i.a = { 1 : 'one', 2 : 'two' }
        self.assertEqual(i.a, { 1 : 'one', 2 : 'two' })
        self.assertRaises(TypeError, setattr, i, 'a', { 1 : 1.0, 2 : 2.0 })
        i.a[3] = 'three'
        self.assertEqual(i.a[3], 'three')
        self.assertRaises(TypeError, i.a.__setitem__, 3, 3.0)
        
    def test_depth(self):
    
        class u(magic.Object):
            a = magic.Property([[int]])
            
            def __init__(self, init_a = None):
                super(u, self).__init__()
                self.a = utils.replace_none(init_a, [])
                    
        i = u()
        i.a = [[1, 2], [3, 4]]
        self.assertEqual(i.a, [[1, 2], [3, 4]])
        self.assertRaises(TypeError, i.a.append, 4)
        self.assertRaises(TypeError, i.a.append, ['a', 'b'])
        
    def test_invariant(self):
        
        class u(magic.Object):
            a = magic.Property(int)
            b = magic.Property([str])
            
            def __init__(self, a = 0, b = None):
                super(u, self).__init__()
                self.a = a
                self.b = utils.replace_none(b, [])
                
            @magic.Invariant
            def verify(self):
                return len(self.b) == self.a
                
            def modify(self, a, b):
                self.a = a
                self.b = b
                
            @classmethod
            def foo(cls, bar):
                pass
                
            @staticmethod
            def bar():
                pass
                
        i = u()
        i.modify(2, ['one', 'two'])
        self.assertRaises(ValueError, setattr, i, 'a', 3)
        i.a = 2
        self.assertRaises(ValueError, i.b.append, 'three')
        i.a = 3
        i.foo(4)
        i.bar()
        
    def test_derived(self):
        
        class u(magic.Object):
            b = magic.Property([str])
            
            def __init__(self, b = None):
                super(u, self).__init__()
                self.b = utils.replace_none(b, [])
                

            @magic.Derived
            def a(self):
                return len(self.b)

            @classmethod
            def foo(cls, bar):
                pass
                
            @staticmethod
            def bar():
                pass
                
        i = u(['one', 'two', 'three', 'four'])
        self.assertEqual(i.a, 4)
        i.foo(4)
        i.bar()
        
    def test_inheritance(self):
    
        class u(magic.Object):
            a = magic.Property(str)
            
            def __init__(self, a = None):
                super(u, self).__init__()
                self.a = utils.replace_none(a, '')

        class v(u):
            b = magic.Property(int)
            
            def __init__(self, a = None, b = None):
                super(v, self).__init__(a)
                self.b = utils.replace_none(b, 0)
                
        i = v('foo', 5)
        self.assertEqual(i.a, 'foo')
        self.assertEqual(i.b, 5)
        self.assertRaises(TypeError, setattr, i, 'a', 3)

if __name__ == '__main__':

    suite1 = unittest.TestLoader().loadTestsFromTestCase(ContainerTests)
    suite2 = unittest.TestLoader().loadTestsFromTestCase(TypeDefinitionTests)
    suite3 = unittest.TestLoader().loadTestsFromTestCase(MagicTests)
    master = unittest.TestSuite()
    master.addTests((suite1, suite2, suite3))
    unittest.TextTestRunner(verbosity=1).run(master)

    
