#/usr/bin/env python

from xml.etree import ElementTree
from magic import _object

class _xml(object):
    
    def to_xml(self, node = None):
        if node is None:
            node = ElementTree.Element(type(self).__name__)

        for property_name, type_description in type(self)._sorted_properties():
            type_description.subhandler(
                ElementTree.SubElement(node, property_name),
                getattr(self, property_name),
                leaf = _xml._to_leaf_xml,
                sequence = _xml._to_sequence_xml,
                mapping = _xml._to_mapping_xml
                )

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
        for position, item in enumerate(val):
            child = ElementTree.SubElement(node, 'item')
            contents.subhandler(child, item, **kwargs)
            
    @staticmethod
    def _to_mapping_xml(type_description, node, val, **kwargs):
        key_contents = type_description._key_contents
        value_contents = type_description._value_contents
        for key, val in val.items():
            child = ElementTree.SubElement(node, 'element')
            key_node = ElementTree.SubElement(node, 'key')
            value_node = ElementTree.SubElement(node, 'value')
            self._to_subhander(key_contents, key_node, key, **kwargs)
            self._to_subhander(value_contents, value_node, value, **kwargs)
            
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
        # this is wrong
        return {}
     
    @classmethod
    def from_xml(cls, node):
        rval = cls()
        for child in node:
            type_description = cls.__ultra__[child.tag][1]
            val = type_description.subhandler(
                rval, 
                child,
                leaf = _xml._from_leaf_xml,
                sequence = _xml._from_sequence_xml,
                mapping = _xml._from_mapping_xml)
                
            setattr(rval, child.tag, val)
        return rval
        