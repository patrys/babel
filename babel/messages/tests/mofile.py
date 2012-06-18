# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011 Edgewall Software
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
import gettext
import os
import unittest
from io import BytesIO

from babel.messages import mofile, Catalog


class ReadMoTestCase(unittest.TestCase):

    def setUp(self):
        self.datadir = os.path.join(os.path.dirname(__file__), 'data')

    def test_basics(self):
        mo_file = open(os.path.join(self.datadir, 'project', 'i18n', 'de',
                                    'LC_MESSAGES', 'messages.mo'), 'rb')
        try:
            catalog = mofile.read_mo(mo_file)
            self.assertEqual(2, len(catalog))
            self.assertEqual('TestProject', catalog.project)
            self.assertEqual('0.1', catalog.version)
            self.assertEqual('Stange', catalog['bar'].string)
            self.assertEqual(['Fuhstange', 'Fuhstangen'],
                             catalog['foobar'].string)
        finally:
            mo_file.close()


class WriteMoTestCase(unittest.TestCase):

    def test_sorting(self):
        # Ensure the header is sorted to the first entry so that its charset
        # can be applied to all subsequent messages by GNUTranslations
        # (ensuring all messages are safely converted to unicode)
        catalog = Catalog(locale='en_US')
        catalog.add('', '''\
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n''')
        catalog.add('foo', 'Voh')
        catalog.add(('There is', 'There are'), ('Es gibt', 'Es gibt'))
        catalog.add('Fizz', '')
        catalog.add(('Fuzz', 'Fuzzes'), ('', ''))
        buf = BytesIO()
        mofile.write_mo(buf, catalog)
        buf.seek(0)
        translations = gettext.GNUTranslations(fp=buf)
        self.assertEqual('Voh', translations.gettext('foo'))
        assert isinstance(translations.gettext('foo'), str)
        self.assertEqual('Es gibt', translations.ngettext('There is', 'There are', 1))
        assert isinstance(translations.ngettext('There is', 'There are', 1), str)
        self.assertEqual('Fizz', translations.gettext('Fizz'))
        assert isinstance(translations.gettext('Fizz'), str)
        self.assertEqual('Fuzz', translations.gettext('Fuzz'))
        assert isinstance(translations.gettext('Fuzz'), str)
        self.assertEqual('Fuzzes', translations.gettext('Fuzzes'))
        assert isinstance(translations.gettext('Fuzzes'), str)

    def test_more_plural_forms(self):
        catalog2 = Catalog(locale='ru_RU')
        catalog2.add(('Fuzz', 'Fuzzes'), ('', '', ''))
        buf = BytesIO()
        mofile.write_mo(buf, catalog2)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(mofile, optionflags=doctest.ELLIPSIS))
    suite.addTest(unittest.makeSuite(ReadMoTestCase))
    suite.addTest(unittest.makeSuite(WriteMoTestCase))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
