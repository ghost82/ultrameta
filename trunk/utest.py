#/usr/bin/env python

import unittest
import ultrameta

class magic_tests(unittest.TestCase):

        def test_circular(self):
        
            class u(ultrameta.object, ultrameta.xmlmixin, ultrameta.ddlmixin):
                a = ultrameta.property([int])
                
                def __init__(self, init_a = None):
                    super(u, self).__init__()
                    if init_a is None:
                        self.a = []
                    else:
                        self.a = init_a
                        
            class u2(ultrameta.object, ultrameta.xmlmixin, ultrameta.ddlmixin):
                b = ultrameta.property(int)
                c = ultrameta.property([u])
                
                def __init__(self, init_b = None, init_c = None):
                    super(u2, self).__init__()
                    if init_c is None:
                        self.c = []
                    else:
                        self.c = init_c
                    if init_b is None:
                        self.b = 0
                    else:
                        self.b = init_b
                        
                def __repr__(self):
                    return 'b: %s, c: %s' % (self.b, self.c)
                        
            i = u([3, 1, 2, 3])
            i2 = u2(3, [i, i])
            
            self.assertEqual(i2.c[0], i)
            
            i3 = u2.from_xml(i2.to_xml())
            
            self.assertEqual(i3.b, i2.b)
            self.assertEqual(i3.c[1].a[0], i2.c[1].a[0])
            
            print i2.ddl()
        
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(magic_tests)
    unittest.TextTestRunner(verbosity=2).run(suite)
    

