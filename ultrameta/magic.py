#/usr/bin/env python

import type_definition
from types import FunctionType
from utils import replace_none
    
class _descriptor(object):

    def __init__(self, reader, writer):
        self._reader = reader
        self._writer = writer
        
    def __get__(self, instance, owner):
        if instance is not None:
            return self._reader(instance)
        else:
            return self
            
    def __set__(self, instance, value):
        self._writer(instance, value)
        
    def __delete__(self, instance):
        pass

class _property(object):

    order = 0

    def __init__(self, prototype):
        self._type_definition = type_definition._type_definition(prototype)
        self._order = _property.order
        
        _property.order = _property.order + 1
        
    @property
    def meta_data(self):
        return [self._order, self._type_definition]
        
    def create_default_read_method(self, attr):

        def read_method(instance):
            return instance.__dict__[attr]
            
        return read_method

    def create_default_write_method(self, attr):
    
        def write_method(instance, val):
            if self._type_definition.type_match(val):
                instance.__dict__[attr] = self._type_definition.proxy(val, 
                    instance.__ultra_do_invariant_checks__)
            else:
                raise TypeError('%s is type %s not %s' % (val, type(val), self._type_definition))
            if getattr(instance, '__ultra_invariant_checks__', False):
                instance.__ultra_do_invariant_checks__()
                
        return write_method
        
    def create_property(self, attr):
        reader = self.create_default_read_method(attr)
        writer = self.create_default_write_method(attr)
        return _descriptor(reader, writer)
        
class _identity(_property):

    def __init__(self, prototype):
        super(_identity, self).__init__(prototype)
        
    def create_eq(self, attr):
        def eq(self, other):
            return getattr(self, attr) == getattr(other, attr)
        return eq
        
    def create_ne(self, attr):
        def ne(self, other):
            return getattr(self, attr) != getattr(other, attr)
        return ne
        
    def create_hash(self, attr):
        def hash(self):
            return self.attr.__hash__()
        return hash

### move the various invariant check functions to the property objects
### not the main instance.
        
def _invariant(boolean_op):
    boolean_op.__is_an_invariant__ = True
    return boolean_op

def _invariant_checked(method):
    def invariants_checked(*args, **kwargs):
        if isinstance(args[0], _object):
            try:
                args[0].__ultra_invariant_checks__ = False
                t = method(*args, **kwargs)
            finally:
                args[0].__ultra_invariant_checks__ = True
                args[0].__ultra_do_invariant_checks__()
            return t
        else:
            return method(*args, **kwargs)
    return invariants_checked

class _meta(type):

    def __new__(cls, name, bases, dict):

        mods = {}
        id = None
        invariants = []
        for k, v in dict.iteritems():
            if isinstance(v, _property):
                mods[k] = v.create_property(k)
                if isinstance(v, _identity):
                    if id is None:
                        id = (v, k)
                    else:
                        ValueError("Multiple identities not allowed.")
            if getattr(v, '__is_an_invariant__', False) == True:
                invariants.append(v)
                
        if len(invariants) > 0:
            for k, v in dict.iteritems():
                if isinstance(v, FunctionType):
                    dict[k] = _invariant_checked(v)
                
        if len(mods) > 0:
            dict.setdefault('__ultra__', {})
            for k, v in mods.iteritems():
                dict['__ultra__'][k] = dict[k].meta_data
                dict[k] = v
            lowest_property = min(i[0] for i in dict['__ultra__'].values())
            for k in dict['__ultra__']:
                dict['__ultra__'][k][0] = dict['__ultra__'][k][0] - lowest_property
            _property.order = 0

        if id is not None:
            v, k = id
            dict['__eq__'] = v.create_eq(k)
            dict['__ne__'] = v.create_ne(k)
            dict['__hash__'] = v.create_hash(k)
            
        dict['__ultra_invariants__'] = invariants
        
        t = super(_meta, cls).__new__(cls, name, bases, dict)
        return t

class _object(object):
    __metaclass__ = _meta
    
    def __ultra_do_invariant_checks__(self):
        if getattr(self, '__ultra_invariant_checks__', False):
            for invariant in self.__class__.__ultra_invariants__:
                if not invariant(self):
                    raise ValueError('Invariant has been violated')
    
    @classmethod
    def _sorted_properties(cls):
        properties = cls.__ultra__.items()
        properties.sort(key=lambda x: x[1][0])
        return [(i[0], i[1][1]) for i in properties]
                
if __name__ == '__main__':

    import unittest

    class Tests(unittest.TestCase):
    
        def test_property(self):
            p = _property(int)
                    
        def test_object(self):
            
            class u(_object):
                a = _property(int)
                
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
            
            class u(_object):
                b = _property(int)
                a = _property(str)
                
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
            
            class u(_object):
                a = _identity(str)
                b = _property(int)

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
            
            class u(_object):
                a = _property([int])
                
                def __init__(self, init_a = None):
                    super(u, self).__init__()
                    self.a = replace_none(init_a, [])
                        
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
            
            class u(_object):
                a = _property({int:str})
                
                def __init__(self, init_a = None):
                    super(u, self).__init__()
                    self.a = replace_none(init_a, {})
                        
            i = u()
            
            self.assertEqual(i.a, {})
            i.a = { 1 : 'one', 2 : 'two' }
            self.assertEqual(i.a, { 1 : 'one', 2 : 'two' })
            self.assertRaises(TypeError, setattr, i, 'a', { 1 : 1.0, 2 : 2.0 })
            i.a[3] = 'three'
            print type(i.a)
            self.assertEqual(i.a[3], 'three')
            self.assertRaises(TypeError, i.a.__setitem__, 3, 3.0)
            
        def test_depth(self):
        
            class u(_object):
                a = _property([[int]])
                
                def __init__(self, init_a = None):
                    super(u, self).__init__()
                    self.a = replace_none(init_a, [])
                        
            i = u()
            i.a = [[1, 2], [3, 4]]
            self.assertEqual(i.a, [[1, 2], [3, 4]])
            self.assertRaises(TypeError, i.a.append, 4)
            self.assertRaises(TypeError, i.a.append, ['a', 'b'])
            
        def test_invariant(self):
            
            class u(_object):
                a = _property(int)
                b = _property([str])
                
                def __init__(self, a = 0, b = None):
                    super(u, self).__init__()
                    self.a = a
                    self.b = replace_none(b, [])
                    
                @_invariant
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
            
            
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)
    
        
            