#/usr/bin/env python

from utils import replace_none
from itertools import izip

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
            