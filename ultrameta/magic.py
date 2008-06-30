#/usr/bin/env python

import type_definition
from types import FunctionType
from utils import replace_none
    
class Descriptor(object):

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

class OrderedClassAttribute(object):
    order = 0
    
    def __init__(self):
        self._order = OrderedClassAttribute.order
        OrderedClassAttribute.order += 1
        
class UltraProperty(OrderedClassAttribute):

    def __init__(self):
        super(UltraProperty, self).__init__()
        self._type_definition = type_definition.TypeDefinition(None)
        
    @property
    def meta_data(self):
        return [self._order, self._type_definition]
        
    def create_read_method(self):
        raise NotImplementedError()
        
    def create_write_method(self):
        raise NotImplementedError()
        
    def create_property(self, attr):
        return Descriptor(self.create_read_method(attr), self.create_write_method(attr))
    

class Property(UltraProperty):

    def __init__(self, prototype):
        super(Property, self).__init__()
        self._type_definition = type_definition.TypeDefinition(prototype)
        
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
        
class Identity(Property):

    def __init__(self, prototype):
        super(Identity, self).__init__(prototype)
        
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

def Invariant(boolean_op):
    boolean_op.__is_an_invariant__ = True
    return boolean_op
    
def InvariantChecked(method):
    def invariants_checked(*args, **kwargs):
        if isinstance(args[0], Object):
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

class DerivedProperty(UltraProperty):

    def __init__(self, func):
        super(DerivedProperty, self).__init__()
        self._func = func
        
    def create_property(self, attr):
        return Descriptor(lambda instance: self._func(instance))
        
def Derived(func):
    return DerivedProperty(func)

class Meta(type):

    def __new__(cls, name, bases, dict):

        mods = {}
        id = None
        invariants = []
        for k, v in dict.iteritems():
            if isinstance(v, UltraProperty):
                mods[k] = v.create_property(k)
                if isinstance(v, Identity):
                    if id is None:
                        id = (v, k)
                    else:
                        ValueError("Multiple identities not allowed.")
            if getattr(v, '__is_an_invariant__', False) == True:
                invariants.append(v)
                
        if len(invariants) > 0:
            for k, v in dict.iteritems():
                if isinstance(v, FunctionType):
                    dict[k] = InvariantChecked(v)
                
        if len(mods) > 0:
            dict.setdefault('__ultra__', {})
            for k, v in mods.iteritems():
                dict['__ultra__'][k] = dict[k].meta_data
                dict[k] = v
            lowest_property = min(i[0] for i in dict['__ultra__'].values())
            for k in dict['__ultra__']:
                dict['__ultra__'][k][0] = dict['__ultra__'][k][0] - lowest_property
            OrderedClassAttribute.order = 0

        if id is not None:
            v, k = id
            dict['__eq__'] = v.create_eq(k)
            dict['__ne__'] = v.create_ne(k)
            dict['__hash__'] = v.create_hash(k)
            
        dict['__ultra_invariants__'] = invariants
        
        t = super(Meta, cls).__new__(cls, name, bases, dict)
        return t

class Object(object):
    __metaclass__ = Meta
    
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
                
