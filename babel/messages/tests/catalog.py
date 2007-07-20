# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://babel.edgewall.org/wiki/License.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://babel.edgewall.org/log/.

import doctest
import unittest

from babel.messages import catalog


class MessageTestCase(unittest.TestCase):

    def test_python_format(self):
        assert catalog.PYTHON_FORMAT.search('foo %d bar')
        assert catalog.PYTHON_FORMAT.search('foo %s bar')
        assert catalog.PYTHON_FORMAT.search('foo %r bar')
        assert catalog.PYTHON_FORMAT.search('foo %(name).1f')
        assert catalog.PYTHON_FORMAT.search('foo %(name)3.3f')
        assert catalog.PYTHON_FORMAT.search('foo %(name)3f')
        assert catalog.PYTHON_FORMAT.search('foo %(name)06d')
        assert catalog.PYTHON_FORMAT.search('foo %(name)Li')
        assert catalog.PYTHON_FORMAT.search('foo %(name)#d')
        assert catalog.PYTHON_FORMAT.search('foo %(name)-4.4hs')
        assert catalog.PYTHON_FORMAT.search('foo %(name)*.3f')
        assert catalog.PYTHON_FORMAT.search('foo %(name).*f')
        assert catalog.PYTHON_FORMAT.search('foo %(name)3.*f')
        assert catalog.PYTHON_FORMAT.search('foo %(name)*.*f')

    def test_translator_comments(self):
        mess = catalog.Message('foo', user_comments=['Comment About `foo`'])
        self.assertEqual(mess.user_comments, ['Comment About `foo`'])
        mess = catalog.Message('foo',
                               auto_comments=['Comment 1 About `foo`',
                                         'Comment 2 About `foo`'])
        self.assertEqual(mess.auto_comments, ['Comment 1 About `foo`',
                                         'Comment 2 About `foo`'])


class CatalogTestCase(unittest.TestCase):

    def test_two_messages_with_same_singular(self):
        cat = catalog.Catalog()
        cat.add('foo')
        cat.add(('foo', 'foos'))
        self.assertEqual(1, len(cat))

    def test_duplicate_auto_comment(self):
        msg = catalog.Message('foo', auto_comments=['A comment', 'A comment'])
        self.assertEqual(['A comment'], msg.auto_comments)

    def test_duplicate_user_comment(self):
        msg = catalog.Message('foo', user_comments=['A comment', 'A comment'])
        self.assertEqual(['A comment'], msg.user_comments)

    def test_update_message_updates_comments(self):
        cat = catalog.Catalog()
        cat[u'foo'] = catalog.Message('foo', locations=[('main.py', 5)])
        self.assertEqual(cat[u'foo'].auto_comments, [])
        self.assertEqual(cat[u'foo'].user_comments, [])
        # Update cat[u'foo'] with a new location and a comment
        cat[u'foo'] = catalog.Message('foo', locations=[('main.py', 7)],
                                      user_comments=['Foo Bar comment 1'])
        self.assertEqual(cat[u'foo'].user_comments, ['Foo Bar comment 1'])
        # now add yet another location with another comment
        cat[u'foo'] = catalog.Message('foo', locations=[('main.py', 9)],
                                      auto_comments=['Foo Bar comment 2'])
        self.assertEqual(cat[u'foo'].auto_comments, ['Foo Bar comment 2'])

    def test_update_fuzzy_matching_with_case_change(self):
        cat = catalog.Catalog()
        cat.add('foo', 'Voh')
        cat.add('bar', 'Bahr')
        tmpl = catalog.Catalog()
        tmpl.add('Foo')
        cat.update(tmpl)
        self.assertEqual(1, len(cat.obsolete))
        assert 'foo' not in cat

        self.assertEqual('Voh', cat['Foo'].string)
        self.assertEqual(True, cat['Foo'].fuzzy)

    def test_update_fuzzy_matching_with_char_change(self):
        cat = catalog.Catalog()
        cat.add('fo', 'Voh')
        cat.add('bar', 'Bahr')
        tmpl = catalog.Catalog()
        tmpl.add('foo')
        cat.update(tmpl)
        self.assertEqual(1, len(cat.obsolete))
        assert 'fo' not in cat

        self.assertEqual('Voh', cat['foo'].string)
        self.assertEqual(True, cat['foo'].fuzzy)

    def test_update_without_fuzzy_matching(self):
        cat = catalog.Catalog()
        cat.add('fo', 'Voh')
        cat.add('bar', 'Bahr')
        tmpl = catalog.Catalog()
        tmpl.add('foo')
        cat.update(tmpl, no_fuzzy_matching=True)
        self.assertEqual(2, len(cat.obsolete))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(catalog, optionflags=doctest.ELLIPSIS))
    suite.addTest(unittest.makeSuite(MessageTestCase))
    suite.addTest(unittest.makeSuite(CatalogTestCase))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
