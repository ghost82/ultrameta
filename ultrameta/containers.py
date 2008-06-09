#/usr/bin/env python

from utils import replace_none
from itertools import izip

def _invariant_checked(self, func):
    
    def wrapper(val):
        func(val)
        self._invariant_checks()
        
    return wrapper
    
class _withMixin(object):

    def _with(self, type_definition = None, invariant_checks = None):
        self._type_definition = replace_none(getattr(self, '_type_definition', None), type_definition)
        self._invariant_checks = replace_none(getattr(self, '_invariant_checks', None), invariant_checks)
        
        methods, proxies = self.proxy_definitions()
        if self._type_definition:
            for method, proxy in izip(methods, proxies):
                setattr(self, method, proxy)
        if self._invariant_checks:
            for method in methods:
                setattr(self, method, _invariant_checked(self, getattr(self, method)))

        return self             

    def withtype(self, type_definition):
        if not type_definition.type_match(self):
            raise TypeError()
        return self._with(type_definition = type_definition)
        
    def withinvariants(self, invariant_checks):
        invariant_checks()
        return self._with(invariant_checks = invariant_checks)
        
    def proxy_definitions(self):
        # this is meant to be overridden
        return [], []

class list_proxy(list, _withMixin):

    def proxy_definitions(self):
        methods = ['append', '__setslice__']
        proxies = [self._append_type_safe, self._setslice_type_safe]
        return methods, proxies

    def _append_type_safe(self, val):
        if self._type_definition.contents_match(val, None):
            super(list_proxy, self).append(val)
        else:
            raise TypeError('%s is a %s and cannot be appended to a %s' % 
                (val, type(val), self._type_definition))

    def _setslice_type_safe(self, i, j, val):
        if self._type_definition.type_match(val):
            return super(list_proxy, self).__setslice__(i, j, val)
        else:
            raise TypeError('%s is not a %s' % (val, self._type_definition))        

            
class tuple_proxy(tuple, _withMixin):
    pass
    
class dictionary_proxy(dict, _withMixin):

    def proxy_definitions(self):
        methods = ['__setitem__']
        proxies = [self._setitem_type_safe]
        return methods, proxies

    def _setitem_type_safe(self, key, val):
        if self._type_definition.contents_match(val, key):
            super(dictionary_proxy, self).__setitem__(key, val)
        else:
            raise TypeError('%s is not a %s' % ((key, val), self._type_definition))
        
if __name__ == '__main__':
    import unittest
    from type_definition import _type_definition
    
    class Tests(unittest.TestCase):
        
        def append(list, val):
            list.append(val)
            
        def assign(map, key, val):
            map[key] = val
        
        def test_list_of_int(self):
            type_definition = _type_definition([int])
            test_list = list_proxy([1, 2, 3]).withtype(type_definition)
            self.assertEqual(test_list, [1, 2, 3])
            self.assertEqual(test_list[1], 2)
            self.assertEqual(len(test_list), 3)
           
        def test_type_safe_list_of_int(self):
            type_definition = _type_definition([int])
            test_list = list_proxy([]).withtype(type_definition)
            self.assertRaises(TypeError, self.append, test_list, 'a')
            
        def test_map_from_str_to_int(self):
            type_definition = _type_definition({str:int})
            test_map = dictionary_proxy({'a' : 1, 'b' : 2}).withtype(type_definition)
            self.assertEqual(test_map['a'], 1)
            test_map = dictionary_proxy({'a' : 1, 'b' : 'c'})
            self.assertRaises(TypeError, test_map.withtype, type_definition)
            
        def test_type_safe_map_from_str_to_int(self):
            type_definition = _type_definition({str:int})
            test_map = dictionary_proxy({}).withtype(type_definition)
            self.assertRaises(TypeError, self.assign, test_map, 1, 1)
            self.assertRaises(TypeError, self.assign, test_map, 'a', 'a')
            
        def test_tuple_int_int_str_int(self):
            type_definition = _type_definition((int, int, str, int))
            test_tuple = tuple_proxy((1, 2, 'c', 3)).withtype(type_definition)
            self.assertEqual(test_tuple, (1, 2, 'c', 3))
            self.assertEqual(test_tuple[1], 2)
            self.assertRaises(TypeError, self.assign, test_tuple, 2, 4)
            
        def test_tuple_type_safety(self):
            type_definition = _type_definition((int, int, str, int))
            test_tuple = tuple_proxy((1, 2, 3))
            self.assertRaises(TypeError, test_tuple.withtype, type_definition)
            
            
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)

                        
            
