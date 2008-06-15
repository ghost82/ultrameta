#/usr/bin/env python

from itertools import izip
from xml.etree import ElementTree
from magic import _object

class _xml(object):
    
    def to_xml(self, node = None):
        if node is None:
            node = ElementTree.Element(type(self).__name__,)
        else:
            node = ElementTree.SubElement(node, type(self).__name__)

        for property_name, type_description in type(self)._sorted_properties():
            type_description.subhandler(
                ElementTree.SubElement(node, property_name, type=str(type_description)),
                getattr(self, property_name),
                leaf = _xml._to_leaf_xml,
                tuple = _xml._to_tuple_xml,
                sequence = _xml._to_sequence_xml,
                mapping = _xml._to_mapping_xml
                )

        return node
        
    @staticmethod
    def child_node(node, val, val_type):
        if not isinstance(val, _object):
            tag = val_type.subhandler(
                leaf = lambda type_description, **kwargs: 'item', 
                tuple = lambda type_description, **kwargs: 'tuple',
                sequence = lambda type_description, **kwargs: 'sequence',
                mapping = lambda type_description, **kwargs: 'mapping')
            return ElementTree.SubElement(node, tag, type=str(val_type))
        else:
            return node
                
    @staticmethod
    def _to_leaf_xml(type_description, node, val, **kwargs):
        if isinstance(val, _object):
            val.to_xml(node)
        else:
            node.text = str(val)
        
    @staticmethod
    def _to_sequence_xml(type_description, node, val, **kwargs):
        contents = type_description._contents
        for item in val:
            child = _xml.child_node(node, item, contents)
            contents.subhandler(child, item, **kwargs)
            
    @staticmethod
    def _to_mapping_xml(type_description, node, val, **kwargs):
        key_contents = type_description._key_contents
        value_contents = type_description._value_contents
        for key, value in val.items():
            key_node = _xml.child_node(node, key, key_contents)
            value_node = _xml.child_node(node, value, value_contents)
            key_contents.subhandler(key_node, key, **kwargs)
            value_contents.subhandler(value_node, value, **kwargs)
            
    @staticmethod
    def _to_tuple_xml(type_description, node, val, **kwargs):
        contents = type_description._tuple_contents
        for value_type, value in izip(contents, val):
            child = _xml.child_node(node, value, value_type)
            value_type.subhandler(child, value, **kwargs)
        
    @staticmethod
    def _from_leaf_xml(type_description, self, node, **kwargs):
        if len(node) == 0:
            return type_description._type(node.text)
        else:
            return type_description._type.from_xml(node)
            
    @staticmethod
    def _from_sequence_xml(type_description, self, node, **kwargs):
        return [type_description._contents.subhandler(self, item, **kwargs) for item in node]
            
    @staticmethod
    def _from_mapping_xml(type_description, self, node, **kwargs):
        key_list = [y for x, y in enumerate(node) if (x % 2) == 0]
        value_list = [y for x, y in enumerate(node) if (x % 2) == 1]
        keys = [type_description._key_contents.subhandler(self, item, **kwargs) 
            for item in key_list]
        values = [type_description._value_contents.subhandler(self, item, **kwargs)
            for item in value_list]
        return dict([(key, value) for key, value in izip(keys, values)])
        
    @staticmethod
    def _from_tuple_xml(type_description, self, node, **kwargs):
        return tuple([child_type.subhandler(self, child, **kwargs) 
            for child, child_type in izip(node, type_description._tuple_contents)])
        
    @classmethod
    def from_xml(cls, node):
        rval = cls()
        for child in node:
            type_description = cls.__ultra__[child.tag][1]
            val = type_description.subhandler(
                rval, 
                child,
                leaf = _xml._from_leaf_xml,
                tuple = _xml._from_tuple_xml,
                sequence = _xml._from_sequence_xml,
                mapping = _xml._from_mapping_xml)
            
            setattr(rval, child.tag, val)
        return rval


if __name__ == '__main__':
    
    import unittest
    from magic import _property
    
    class a(_object, _xml):
        
        first = _property(int)
        second = _property(str)
        third = _property(float)
        
        def __init__(self, i_first=0, i_second='', i_third=0.0):
            super(a, self).__init__()
            self.first = i_first
            self.second = i_second
            self.third = i_third
            
    class b(_object, _xml):
        
        first = _property([int])
        second = _property({int: int})
        third = _property((str, int, float))
        
        def __init__(self):
            super(b, self).__init__()
            self.first = [1, 2, 3]
            self.second = {0: 1, 1: 3}
            self.third = ('a', 0, 1.0)
            
    class c(_object, _xml):
        
        first = _property([a])
        
        def __init__(self, a_i = None):
            super(c, self).__init__()
            if a_i is not None:
                self.first = [a_i]
            else:
                self.first = []
                
    class d(_object, _xml):
        
        first = _property([[int]])
        
        def __init__(self, first = None):
            super(d, self).__init__()
            if first is not None:
                self.first = first
            else:
                self.first = []
    
    class Tests(unittest.TestCase):
    
        def setUp(self):
            self.test_a = a(4, 'four', 4.01)
            self.test_b = b()
            self.test_c = c(self.test_a)
            self.test_d = d([[2, 4, 6], [1, 3, 5]])
                    
        def test_atoms(self):
            xml = self.test_a.to_xml()
            self.assertEqual(xml.tag, 'a')
            self.assertEqual(xml.find('first').text, '4')
            self.assertEqual(xml.find('second').text, 'four')
            self.assertEqual(xml.find('third').text, '4.01')
            self.assertEqual(ElementTree.tostring(xml), '<a><first type="int">4</first><second type="str">four</second><third type="float">4.01</third></a>')
            
        def test_roundtrip(self):
            test_a2 = a.from_xml(self.test_a.to_xml())
            self.assertEqual(self.test_a.first, test_a2.first)
            self.assertEqual(self.test_a.second, test_a2.second)
            self.assertEqual(self.test_a.third, test_a2.third)
            
        def test_types(self):
            test_b2 = b.from_xml(self.test_b.to_xml())
            self.assertEqual(test_b2.first, self.test_b.first)
            self.assertEqual(test_b2.second, self.test_b.second)
            self.assertEqual(test_b2.third, self.test_b.third)
            
        def test_containment(self):
            test_c2 = c.from_xml(self.test_c.to_xml())
            self.assertEqual(test_c2.first[0].first, self.test_c.first[0].first)
            
        def test_nesting(self):
            test_d2 = d.from_xml(self.test_d.to_xml())
            self.assertEqual(test_d2.first[0][1], self.test_d.first[0][1])
                
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)
