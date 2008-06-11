#/usr/bin/env python

import type_definition
from types import FunctionType
from utils import replace_none
    
class _descriptor(object):

    def __init__(self, reader = None, writer = None):
        self._reader = reader
        self._writer = writer
        
    def __get__(self, instance, owner):
        if instance is not None:
            if self._reader is None:
                raise TypeError('Attribute does not support read operations.')
            return self._reader(instance)
        else:
            return self
            
    def __set__(self, instance, value):
        if self._writer is None:
            raise TypeError('Attribute does not support assignment.')
        self._writer(instance, value)
        
    def __delete__(self, instance):
        pass

class _ordered_class_attr(object):
    order = 0
    
    def __init__(self):
        self._order = _ordered_class_attr.order
        _ordered_class_attr.order += 1
        
class _ultra_property(_ordered_class_attr):

    def __init__(self):
        super(_ultra_property, self).__init__()
        self._type_definition = type_definition._type_definition(None)
        
    @property
    def meta_data(self):
        return [self._order, self._type_definition]
        
    def create_read_method(self):
        raise NotImplementedError()
        
    def create_write_method(self):
        raise NotImplementedError()
        
    def create_property(self, attr):
        return _descriptor(self.create_read_method(attr), self.create_write_method(attr))
    

class _property(_ultra_property):

    def __init__(self, prototype):
        super(_property, self).__init__()
        self._type_definition = type_definition._type_definition(prototype)
        
    def create_read_method(self, attr):
        return lambda instance: instance.__dict__[attr]

    def create_write_method(self, attr):
        def writer(instance, val):
            if self._type_definition.type_match(val):
                instance.__dict__[attr] = self._type_definition.proxy(val, 
                    instance.__ultra_do_invariant_checks__)
            else:
                raise TypeError('%s is type %s not %s' % (val, type(val), self._type_definition))
            instance.__ultra_do_invariant_checks__()
        return writer
        
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

class _derived_property(_ultra_property):

    def __init__(self, func):
        super(_derived_property, self).__init__()
        self._func = func
        
    def create_property(self, attr):
        return _descriptor(lambda instance: self._func(instance))
        
def _derived(func):
    return _derived_property(func)

class _meta(type):

    def __new__(cls, name, bases, dict):

        mods = {}
        id = None
        invariants = []
        for k, v in dict.iteritems():
            if isinstance(v, _ultra_property):
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
            _ordered_class_attr.order = 0

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
            
        def test_derived(self):
            
            class u(_object):
                b = _property([str])
                
                def __init__(self, b = None):
                    super(u, self).__init__()
                    self.b = replace_none(b, [])
                    

                @_derived
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
        
            class u(_object):
                a = _property(str)
                
                def __init__(self, a = None):
                    super(u, self).__init__()
                    self.a = replace_none(a, '')

            class v(u):
                b = _property(int)
                
                def __init__(self, a = None, b = None):
                    super(v, self).__init__(a)
                    self.b = replace_none(b, 0)
                    
            i = v('foo', 5)
            self.assertEqual(i.a, 'foo')
            self.assertEqual(i.b, 5)
            self.assertRaises(TypeError, setattr, i, 'a', 3)
            
                    
           
            
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)
    
        
            