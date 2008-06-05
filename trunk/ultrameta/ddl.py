#/usr/bin/env python

from magic import _object

class _ddl(object):

    ddl_types = { int : 'INTEGER', str : 'VARCHAR(255)' }

    @classmethod
    def ddl(cls):
        rval = []
        rval.append('CREATE TABLE')
        for property_name, type_description in cls._sorted_properties():
            type_description.subhandler(
                rval,
                property_name,
                leaf = cls.leaf_ddl,
                sequence = cls.sequence_ddl,
                mapping = cls.mapping_ddl)
        return '\n'.join(rval)
        
    @classmethod
    def leaf_ddl(cls, type_description, rval, property_name, **kwargs):
        if isinstance(type_description._type, _object):
            pass
        elif type_description._type in cls.ddl_types:
            rval.append('%s %s' % (property_name, cls.ddl_types[type_description._type]))
        else:
            rval.append('%s VARCHAR(1024)' % property_name)
            
    @classmethod
    def sequence_ddl(cls, type_description, rval, property_name, **kwargs):
        pass
        
    @classmethod
    def mapping_ddl(cls, type_description, rval, property_name, **kwargs):
        pass
        
        
        

