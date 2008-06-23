#/usr/bin/env python

from itertools import izip
from xml.etree import ElementTree
from magic import _object

class _xmlbehavior(object):

    _default_metanames = {  'item' : 'item', 'tuple' : 'tuple', 
                            'sequence' : 'sequence', 'mapping' : 'mapping' }

    def __init__(self, tag_name_editor = None, display_attributes = True, metanames = None):
        self.tag_name_editor = tag_name_editor
        self.display_attributes = display_attributes
        if metanames is None:
            self.metanames = _xmlbehavior._default_metanames
        else:
            self.metanames = metanames
        
    def rename(self, tag):
        if self.tag_name_editor is not None:
            return self.tag_name_editor(tag)
        else:
            return tag
            
    def unrename(self, tag):
        if self.tag_name_editor is not None:
            return (tag, self.tag_name_editor(tag, reverse=True))
        else:
            return (tag, )
    
    @property
    def description(self):
        rval = {}
        if self.display_attributes == False:
            rval['display_attributes'] = 'false'
        if self.metanames != _xmlbehavior._default_metanames:
            rval['metanames'] = self.metanames
        if self.tag_name_editor is not None:
            rval['tag_name_editor'] = self.tag_name_editor.__name__
        return rval
            
class _xml(object):
    
    def to_xml(self, node = None, behavior = _xmlbehavior()):
        if node is None:
            node = ElementTree.Element(behavior.rename(type(self).__name__))
        else:
            node = ElementTree.SubElement(node, behavior.rename(type(self).__name__))
        for k, v in behavior.description.items():
            node.set(k, str(v))
        for property_name, type_description in type(self)._sorted_properties():
            child = ElementTree.SubElement(node, behavior.rename(property_name))
            if behavior.display_attributes:
                child.set('type', str(type_description))
            type_description.subhandler(
                child,
                getattr(self, property_name),
                behavior,
                leaf = _xml._to_leaf_xml,
                tuple = _xml._to_tuple_xml,
                sequence = _xml._to_sequence_xml,
                mapping = _xml._to_mapping_xml
                )

        return node
        
    @staticmethod
    def child_node(node, val, val_type, behavior):
        if not isinstance(val, _object):
            tag = val_type.subhandler(
                leaf = lambda type_description, **kwargs: behavior.rename(behavior.metanames['item']), 
                tuple = lambda type_description, **kwargs: behavior.rename(behavior.metanames['tuple']),
                sequence = lambda type_description, **kwargs: behavior.rename(behavior.metanames['sequence']),
                mapping = lambda type_description, **kwargs: behavior.rename(behavior.metanames['mapping']))
            child = ElementTree.SubElement(node, tag)
            if behavior.display_attributes:
                child.set('type', str(val_type))
            return child
        else:
            return node
                
    @staticmethod
    def _to_leaf_xml(type_description, node, val, behavior, **kwargs):
        if isinstance(val, _object):
            val.to_xml(node)
        else:
            node.text = str(val)
        
    @staticmethod
    def _to_sequence_xml(type_description, node, val, behavior, **kwargs):
        contents = type_description._contents
        for item in val:
            child = _xml.child_node(node, item, contents, behavior)
            contents.subhandler(child, item, behavior, **kwargs)
            
    @staticmethod
    def _to_mapping_xml(type_description, node, val, behavior, **kwargs):
        key_contents = type_description._key_contents
        value_contents = type_description._value_contents
        for key, value in val.items():
            key_node = _xml.child_node(node, key, key_contents, behavior)
            value_node = _xml.child_node(node, value, value_contents, behavior)
            key_contents.subhandler(key_node, key, behavior, **kwargs)
            value_contents.subhandler(value_node, value, behavior, **kwargs)
            
    @staticmethod
    def _to_tuple_xml(type_description, node, val, behavior, **kwargs):
        contents = type_description._tuple_contents
        for value_type, value in izip(contents, val):
            child = _xml.child_node(node, value, value_type, behavior)
            value_type.subhandler(child, value, behavior, **kwargs)
        
    @staticmethod
    def _from_leaf_xml(type_description, self, node, behavior, **kwargs):
        if len(node) == 0:
            return type_description._type(node.text)
        else:
            return type_description._type.from_xml(node)
            
    @staticmethod
    def _from_sequence_xml(type_description, self, node, behavior, **kwargs):
        return [type_description._contents.subhandler(self, item, behavior, **kwargs) for item in node]
            
    @staticmethod
    def _from_mapping_xml(type_description, self, node, behavior, **kwargs):
        key_list = [y for x, y in enumerate(node) if (x % 2) == 0]
        value_list = [y for x, y in enumerate(node) if (x % 2) == 1]
        keys = [type_description._key_contents.subhandler(self, item, behavior, **kwargs) 
            for item in key_list]
        values = [type_description._value_contents.subhandler(self, item, behavior, **kwargs)
            for item in value_list]
        return dict([(key, value) for key, value in izip(keys, values)])
        
    @staticmethod
    def _from_tuple_xml(type_description, self, node, behavior, **kwargs):
        return tuple([child_type.subhandler(self, child, behavior, **kwargs) 
            for child, child_type in izip(node, type_description._tuple_contents)])
        
    @classmethod
    def from_xml(cls, node, behavior = None):
        rval = cls()
        if behavior is None:
            behavior = _xmlbehavior()
        for child in node:
            unrenamed_tag_choices = behavior.unrename(child.tag)
            tag = None
            for tag_name in behavior.unrename(child.tag):
                if tag_name in cls.__ultra__:
                    if tag is None:
                        tag = tag_name
                    else:
                        raise ValueError()
            type_description = cls.__ultra__[tag][1]
            val = type_description.subhandler(
                rval, 
                child,
                behavior,
                leaf = _xml._from_leaf_xml,
                tuple = _xml._from_tuple_xml,
                sequence = _xml._from_sequence_xml,
                mapping = _xml._from_mapping_xml)
            
            setattr(rval, tag, val)
        return rval


if __name__ == '__main__':
    
    import unittest
    from magic import _property
    import tagnameeditors
    
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
        
        first_slot = _property([[int]])
        
        def __init__(self, first = None):
            super(d, self).__init__()
            if first is not None:
                self.first_slot = first
            else:
                self.first_slot = []
    
    class Tests(unittest.TestCase):
    
        def setUp(self):
            self.test_a = a(4, 'four', 4.01)
            self.test_b = b()
            self.test_c = c(self.test_a)
            self.test_d = d([[2, 4, 6], [1, 3, 5]])
                    
        def test_atoms(self):
            xml = self.test_a.to_xml(behavior = _xmlbehavior(tag_name_editor = tagnameeditors.capitalize,
                display_attributes = False))
            print ElementTree.tostring(xml)
            self.assertEqual(xml.tag, 'A')
            self.assertEqual(xml.find('First').text, '4')
            self.assertEqual(xml.find('Second').text, 'four')
            self.assertEqual(xml.find('Third').text, '4.01')
            self.assertEqual(ElementTree.tostring(xml), '<A display_attributes="false" tag_name_editor="capitalize"><First>4</First><Second>four</Second><Third>4.01</Third></A>')
            
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
            test_d2 = d.from_xml(self.test_d.to_xml(behavior = _xmlbehavior(tagnameeditors.capitalize)),
                        behavior = _xmlbehavior(tagnameeditors.capitalize))
            print test_d2.first_slot
            self.assertEqual(test_d2.first_slot[0][1], self.test_d.first_slot[0][1])
                
    suite = unittest.TestLoader().loadTestsFromTestCase(Tests)
    unittest.TextTestRunner(verbosity=2).run(suite)
