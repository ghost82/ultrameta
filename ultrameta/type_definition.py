#/usr/bin/env python

import containers

_container_definitions = {  
    type(None) : (None, 'leaf') ,
    tuple : (containers.tuple_proxy, 'tuple'), 
    list : (containers.list_proxy, 'sequence'),
    dict : (containers.dictionary_proxy, 'mapping') }
    
_type_match = {
    'leaf':     lambda self, val: isinstance(val, self._type),
    'tuple':    lambda self, val: (isinstance(val, self._container) and
                    all(self.contents_match(i, pos) for pos, i in enumerate(val)) and
                    len(val) == len(self._tuple_contents)),
    'sequence': lambda self, val: (isinstance(val, self._container) and
                    all(self.contents_match(i) for i in val)),
    'mapping':  lambda self, val: (isinstance(val, self._container) and 
                    all(self.contents_match(v, k) for (k, v) in val.items())) }
            
_contents_match = {
    'sequence': lambda self, val, key: self._contents.type_match(val),
    'tuple':    lambda self, val, key: self._tuple_contents[key].type_match(val),
    'mapping':  lambda self, val, key: (self._key_contents.type_match(key) and 
                    self._value_contents.type_match(val)),
    'leaf':     lambda self, val, key: None }

class specification(object):

    def __init__(self, prototype, **restrictions):
        self.prototype = prototype
        self.restrictions = restrictions
        
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
            if self._category == 'sequence':
                self._contents = _type_definition(prototype[0])
            elif self._category == 'mapping':
                self._key_contents = _type_definition(prototype.keys()[0])
                self._value_contents = _type_definition(prototype.values()[0])
            elif self._category == 'tuple':
                self._tuple_contents = tuple(_type_definition(i) for i in prototype)
        else:
            self._category = 'leaf'
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

    def proxy(self, val):
        if self._category == 'leaf':
            return val
        else:
            return self._proxy(val).withtype(self)

    def _type_repr(self):
        if self._category == 'leaf':
            return '%s' % self._type.__name__
        elif self._category == 'tuple':
            return '(%s)' % ', '.join([i._type_repr() for i in self._tuple_contents])
        elif self._category == 'sequence':
            return '[%s]' % self._contents._type_repr()
        else:
            return '{%s: %s}' % (self._key_contents._type_repr(), self._value_contents._type_repr())
            
    def __repr__(self):
        return 'ultra._type_description(' + self._type_repr() + ')'


if __name__ == '__main__':
    
    import unittest
    import validators
    
    class Tests(unittest.TestCase):
        
        tlc = specification(str, validation=validators.value(3))
        small = specification(int, validation=validators.bounds(minimum = 0, maximum = 8))
        
        def test_atom(self):
            atom_type = _type_definition(str)
            restriction_str = _type_definition(self.tlc)
            restriction_int = _type_definition(self.small)
            
            self.assertEqual(atom_type.type_match(12), False)
            self.assertEqual(atom_type.type_match('any string'), True)
            
            self.assertEqual(restriction_str.type_match('foo'), True)
            self.assertEqual(restriction_str.type_match('foobar'), False)
            
            self.assertEqual(restriction_int.type_match(3), True)
            self.assertEqual(restriction_int.type_match(10), False)

        def test_list(self):
            list_type = _type_definition([int])
            restriction_list = _type_definition([self.tlc])
            
            self.assertEqual(list_type.type_match(4), False)
            self.assertEqual(list_type.type_match([4]), True)
            self.assertEqual(restriction_list.type_match(['foo', 'bar']), True)
            self.assertEqual(restriction_list.type_match(['foobar', 'a']), False)

        def test_map(self):
            map_type = _type_definition({int: str})
            restriction_map_key = _type_definition({self.tlc: int})
            restriction_map_val = _type_definition({int: self.tlc})
            
            self.assertEqual(map_type.type_match({1: 'a', 2: 'bb', 3: 'cccc'}), True)
            self.assertEqual(map_type.type_match({1: 'a', 'a': 1}), False)
            
            self.assertEqual(restriction_map_key.type_match({'abc': 123}), True)
            self.assertEqual(restriction_map_key.type_match({'a': 123}), False)
            
            self.assertEqual(restriction_map_val.type_match({1: 'abc'}), True)
            self.assertEqual(restriction_map_val.type_match({1: 'a'}), False)
            
        def test_others(self):
            tuple_type = _type_definition((int, str, float))
            mixed_type = _type_definition([{(int, int): str}])
            
            self.assertEqual(tuple_type.type_match((1, 'a', 4.5)), True)
            self.assertEqual(tuple_type.type_match((1, 'abc')), False)
            
            self.assertEqual(mixed_type.type_match([{(1, 3) : 'onethree', (0, 1) : 'zeroone'},
                { (0, 0) : 'done' }]), True)
            
            
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)
