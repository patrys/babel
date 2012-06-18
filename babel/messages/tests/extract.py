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

import codecs
import doctest
from io import BytesIO, StringIO
import sys
import unittest

from babel.messages import extract


class ExtractPythonTestCase(unittest.TestCase):

    def test_nested_calls(self):
        buf = BytesIO(b"""\
msg1 = _(i18n_arg.replace(r'\"', '"'))
msg2 = ungettext(i18n_arg.replace(r'\"', '"'), multi_arg.replace(r'\"', '"'), 2)
msg3 = ungettext("Babel", multi_arg.replace(r'\"', '"'), 2)
msg4 = ungettext(i18n_arg.replace(r'\"', '"'), "Babels", 2)
msg5 = ungettext('bunny', 'bunnies', random.randint(1, 2))
msg6 = ungettext(arg0, 'bunnies', random.randint(1, 2))
msg7 = _(hello.there)
msg8 = gettext('Rabbit')
msg9 = dgettext('wiki', model.addPage())
msg10 = dngettext(getDomain(), 'Page', 'Pages', 3)
""")
        messages = list(extract.extract_python(buf,
                                               list(extract.DEFAULT_KEYWORDS.keys()),
                                               [], {}))
        self.assertEqual([
                (1, '_', None, []),
                (2, 'ungettext', (None, None, None), []),
                (3, 'ungettext', ('Babel', None, None), []),
                (4, 'ungettext', (None, 'Babels', None), []),
                (5, 'ungettext', ('bunny', 'bunnies', None), []),
                (6, 'ungettext', (None, 'bunnies', None), []),
                (7, '_', None, []),
                (8, 'gettext', 'Rabbit', []),
                (9, 'dgettext', ('wiki', None), []),
                (10, 'dngettext', (None, 'Page', 'Pages', None), [])],
                         messages)

    def test_nested_comments(self):
        buf = BytesIO(b"""\
msg = ngettext('pylon',  # TRANSLATORS: shouldn't be
               'pylons', # TRANSLATORS: seeing this
               count)
""")
        messages = list(extract.extract_python(buf, ('ngettext',),
                                               ['TRANSLATORS:'], {}))
        self.assertEqual([(1, 'ngettext', ('pylon', 'pylons', None), [])],
                         messages)

    def test_comments_with_calls_that_spawn_multiple_lines(self):
        buf = BytesIO(b"""\
# NOTE: This Comment SHOULD Be Extracted
add_notice(req, ngettext("Catalog deleted.",
                         "Catalogs deleted.", len(selected)))

# NOTE: This Comment SHOULD Be Extracted
add_notice(req, _("Locale deleted."))


# NOTE: This Comment SHOULD Be Extracted
add_notice(req, ngettext("Foo deleted.", "Foos deleted.", len(selected)))

# NOTE: This Comment SHOULD Be Extracted
# NOTE: And This One Too
add_notice(req, ngettext("Bar deleted.",
                         "Bars deleted.", len(selected)))
""")
        messages = list(extract.extract_python(buf, ('ngettext','_'), ['NOTE:'],

                                               {'strip_comment_tags':False}))
        self.assertEqual((6, '_', 'Locale deleted.',
                          ['NOTE: This Comment SHOULD Be Extracted']),
                         messages[1])
        self.assertEqual((10, 'ngettext', ('Foo deleted.', 'Foos deleted.',
                                           None),
                          ['NOTE: This Comment SHOULD Be Extracted']),
                         messages[2])
        self.assertEqual((3, 'ngettext',
                           ('Catalog deleted.',
                            'Catalogs deleted.', None),
                           ['NOTE: This Comment SHOULD Be Extracted']),
                         messages[0])
        self.assertEqual((15, 'ngettext', ('Bar deleted.', 'Bars deleted.',
                                           None),
                          ['NOTE: This Comment SHOULD Be Extracted',
                           'NOTE: And This One Too']),
                         messages[3])

    def test_declarations(self):
        buf = BytesIO(b"""\
class gettext(object):
    pass
def render_body(context,x,y=_('Page arg 1'),z=_('Page arg 2'),**pageargs):
    pass
def ngettext(y='arg 1',z='arg 2',**pageargs):
    pass
class Meta:
    verbose_name = _('log entry')
""")
        messages = list(extract.extract_python(buf,
                                               list(extract.DEFAULT_KEYWORDS.keys()),
                                               [], {}))
        self.assertEqual([(3, '_', 'Page arg 1', []),
                          (3, '_', 'Page arg 2', []),
                          (8, '_', 'log entry', [])],
                         messages)

    def test_multiline(self):
        buf = BytesIO(b"""\
msg1 = ngettext('pylon',
                'pylons', count)
msg2 = ngettext('elvis',
                'elvises',
                 count)
""")
        messages = list(extract.extract_python(buf, ('ngettext',), [], {}))
        self.assertEqual([(1, 'ngettext', ('pylon', 'pylons', None), []),
                          (3, 'ngettext', ('elvis', 'elvises', None), [])],
                         messages)

    def test_triple_quoted_strings(self):
        buf = BytesIO(b"""\
msg1 = _('''pylons''')
msg2 = ngettext(r'''elvis''', \"\"\"elvises\"\"\", count)
msg2 = ngettext(\"\"\"elvis\"\"\", 'elvises', count)
""")
        messages = list(extract.extract_python(buf,
                                               list(extract.DEFAULT_KEYWORDS.keys()),
                                               [], {}))
        self.assertEqual([(1, '_', ('pylons'), []),
                          (2, 'ngettext', ('elvis', 'elvises', None), []),
                          (3, 'ngettext', ('elvis', 'elvises', None), [])],
                         messages)

    def test_multiline_strings(self):
        buf = BytesIO(b"""\
_('''This module provides internationalization and localization
support for your Python programs by providing an interface to the GNU
gettext message catalog library.''')
""")
        messages = list(extract.extract_python(buf,
                                               list(extract.DEFAULT_KEYWORDS.keys()),
                                               [], {}))
        self.assertEqual(
            [(1, '_',
              'This module provides internationalization and localization\n'
              'support for your Python programs by providing an interface to '
              'the GNU\ngettext message catalog library.', [])],
            messages)

    def test_concatenated_strings(self):
        buf = BytesIO(b"""\
foobar = _('foo' 'bar')
""")
        messages = list(extract.extract_python(buf,
                                               list(extract.DEFAULT_KEYWORDS.keys()),
                                               [], {}))
        self.assertEqual('foobar', messages[0][2])

    def test_unicode_string_arg(self):
        buf = BytesIO(b"msg = _(u'Foo Bar')")
        messages = list(extract.extract_python(buf, ('_',), [], {}))
        self.assertEqual('Foo Bar', messages[0][2])

    def test_comment_tag(self):
        buf = BytesIO(b"""
# NOTE: A translation comment
msg = _(u'Foo Bar')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual('Foo Bar', messages[0][2])
        self.assertEqual(['NOTE: A translation comment'], messages[0][3])

    def test_comment_tag_multiline(self):
        buf = BytesIO(b"""
# NOTE: A translation comment
# with a second line
msg = _(u'Foo Bar')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual('Foo Bar', messages[0][2])
        self.assertEqual(['NOTE: A translation comment', 'with a second line'],
                         messages[0][3])

    def test_translator_comments_with_previous_non_translator_comments(self):
        buf = BytesIO(b"""
# This shouldn't be in the output
# because it didn't start with a comment tag
# NOTE: A translation comment
# with a second line
msg = _(u'Foo Bar')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual('Foo Bar', messages[0][2])
        self.assertEqual(['NOTE: A translation comment', 'with a second line'],
                         messages[0][3])

    def test_comment_tags_not_on_start_of_comment(self):
        buf = BytesIO(b"""
# This shouldn't be in the output
# because it didn't start with a comment tag
# do NOTE: this will not be a translation comment
# NOTE: This one will be
msg = _(u'Foo Bar')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual('Foo Bar', messages[0][2])
        self.assertEqual(['NOTE: This one will be'], messages[0][3])

    def test_multiple_comment_tags(self):
        buf = BytesIO(b"""
# NOTE1: A translation comment for tag1
# with a second line
msg = _(u'Foo Bar1')

# NOTE2: A translation comment for tag2
msg = _(u'Foo Bar2')
""")
        messages = list(extract.extract_python(buf, ('_',),
                                               ['NOTE1:', 'NOTE2:'], {}))
        self.assertEqual('Foo Bar1', messages[0][2])
        self.assertEqual(['NOTE1: A translation comment for tag1',
                          'with a second line'], messages[0][3])
        self.assertEqual('Foo Bar2', messages[1][2])
        self.assertEqual(['NOTE2: A translation comment for tag2'], messages[1][3])

    def test_two_succeeding_comments(self):
        buf = BytesIO(b"""
# NOTE: one
# NOTE: two
msg = _(u'Foo Bar')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual('Foo Bar', messages[0][2])
        self.assertEqual(['NOTE: one', 'NOTE: two'], messages[0][3])

    def test_invalid_translator_comments(self):
        buf = BytesIO(b"""
# NOTE: this shouldn't apply to any messages
hello = 'there'

msg = _(u'Foo Bar')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual('Foo Bar', messages[0][2])
        self.assertEqual([], messages[0][3])

    def test_invalid_translator_comments2(self):
        buf = BytesIO(b"""
# NOTE: Hi!
hithere = _('Hi there!')

# NOTE: you should not be seeing this in the .po
rows = [[v for v in range(0,10)] for row in range(0,10)]

# this (NOTE:) should not show up either
hello = _('Hello')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual('Hi there!', messages[0][2])
        self.assertEqual(['NOTE: Hi!'], messages[0][3])
        self.assertEqual('Hello', messages[1][2])
        self.assertEqual([], messages[1][3])

    def test_invalid_translator_comments3(self):
        buf = BytesIO(b"""
# NOTE: Hi,

# there!
hithere = _('Hi there!')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual('Hi there!', messages[0][2])
        self.assertEqual([], messages[0][3])

    def test_comment_tag_with_leading_space(self):
        buf = BytesIO(b"""
  #: A translation comment
  #: with leading spaces
msg = _(u'Foo Bar')
""")
        messages = list(extract.extract_python(buf, ('_',), [':'], {}))
        self.assertEqual('Foo Bar', messages[0][2])
        self.assertEqual([': A translation comment', ': with leading spaces'],
                         messages[0][3])

    def test_different_signatures(self):
        buf = BytesIO(b"""
foo = _('foo', 'bar')
n = ngettext('hello', 'there', n=3)
n = ngettext(n=3, 'hello', 'there')
n = ngettext(n=3, *messages)
n = ngettext()
n = ngettext('foo')
""")
        messages = list(extract.extract_python(buf, ('_', 'ngettext'), [], {}))
        self.assertEqual(('foo', 'bar'), messages[0][2])
        self.assertEqual(('hello', 'there', None), messages[1][2])
        self.assertEqual((None, 'hello', 'there'), messages[2][2])
        self.assertEqual((None, None), messages[3][2])
        self.assertEqual(None, messages[4][2])
        self.assertEqual(('foo'), messages[5][2])

    def test_utf8_message(self):
        buf = BytesIO("""
# NOTE: hello
msg = _('Bonjour à tous')
""".encode('utf-8'))
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'],
                                               {'encoding': 'utf-8'}))
        self.assertEqual('Bonjour à tous', messages[0][2])
        self.assertEqual(['NOTE: hello'], messages[0][3])

    def test_utf8_message_with_magic_comment(self):
        buf = BytesIO("""# -*- coding: utf-8 -*-
# NOTE: hello
msg = _('Bonjour à tous')
""".encode('utf-8'))
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual('Bonjour à tous', messages[0][2])
        self.assertEqual(['NOTE: hello'], messages[0][3])

    def test_utf8_message_with_utf8_bom(self):
        buf = BytesIO(codecs.BOM_UTF8 + """
# NOTE: hello
msg = _('Bonjour à tous')
""".encode('utf-8'))
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual('Bonjour à tous', messages[0][2])
        self.assertEqual(['NOTE: hello'], messages[0][3])

    def test_utf8_raw_strings_match_unicode_strings(self):
        buf = BytesIO(codecs.BOM_UTF8 + """
msg = _('Bonjour à tous')
msgu = _(u'Bonjour à tous')
""".encode('utf-8'))
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual('Bonjour à tous', messages[0][2])
        self.assertEqual(messages[0][2], messages[1][2])

    def test_extract_strip_comment_tags(self):
        buf = BytesIO(b"""\
#: This is a comment with a very simple
#: prefix specified
_('Servus')

# NOTE: This is a multiline comment with
# a prefix too
_('Babatschi')""")
        messages = list(extract.extract('python', buf, comment_tags=['NOTE:', ':'],
                                        strip_comment_tags=True))
        self.assertEqual('Servus', messages[0][1])
        self.assertEqual(['This is a comment with a very simple',
                          'prefix specified'], messages[0][2])
        self.assertEqual('Babatschi', messages[1][1])
        self.assertEqual(['This is a multiline comment with',
                          'a prefix too'], messages[1][2])


class ExtractJavaScriptTestCase(unittest.TestCase):

    def test_simple_extract(self):
        buf = BytesIO(b"""\
msg1 = _('simple')
msg2 = gettext('simple')
msg3 = ngettext('s', 'p', 42)
        """)
        messages = \
            list(extract.extract('javascript', buf, extract.DEFAULT_KEYWORDS,
                                 [], {}))

        self.assertEqual([(1, 'simple', [], None),
                          (2, 'simple', [], None),
                          (3, ('s', 'p'), [], None)], messages)

    def test_various_calls(self):
        buf = BytesIO(b"""\
msg1 = _(i18n_arg.replace(/"/, '"'))
msg2 = ungettext(i18n_arg.replace(/"/, '"'), multi_arg.replace(/"/, '"'), 2)
msg3 = ungettext("Babel", multi_arg.replace(/"/, '"'), 2)
msg4 = ungettext(i18n_arg.replace(/"/, '"'), "Babels", 2)
msg5 = ungettext('bunny', 'bunnies', parseInt(Math.random() * 2 + 1))
msg6 = ungettext(arg0, 'bunnies', rparseInt(Math.random() * 2 + 1))
msg7 = _(hello.there)
msg8 = gettext('Rabbit')
msg9 = dgettext('wiki', model.addPage())
msg10 = dngettext(domain, 'Page', 'Pages', 3)
""")
        messages = \
            list(extract.extract('javascript', buf, extract.DEFAULT_KEYWORDS, [],
                                 {}))
        self.assertEqual([(5, ('bunny', 'bunnies'), [], None),
                          (8, 'Rabbit', [], None),
                          (10, ('Page', 'Pages'), [], None)], messages)

    def test_message_with_line_comment(self):
        buf = BytesIO("""\
// NOTE: hello
msg = _('Bonjour à tous')
""".encode('utf-8'))
        messages = list(extract.extract_javascript(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual('Bonjour à tous', messages[0][2])
        self.assertEqual(['NOTE: hello'], messages[0][3])

    def test_message_with_multiline_comment(self):
        buf = BytesIO("""\
/* NOTE: hello
   and bonjour
     and servus */
msg = _('Bonjour à tous')
""".encode('utf-8'))
        messages = list(extract.extract_javascript(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual('Bonjour à tous', messages[0][2])
        self.assertEqual(['NOTE: hello', 'and bonjour', '  and servus'], messages[0][3])

    def test_ignore_function_definitions(self):
        buf = BytesIO(b"""\
function gettext(value) {
    return translations[language][value] || value;
}""")

        messages = list(extract.extract_javascript(buf, ('gettext',), [], {}))
        self.assertEqual(messages, [])

    def test_misplaced_comments(self):
        buf = BytesIO(b"""\
/* NOTE: this won't show up */
foo()

/* NOTE: this will */
msg = _('Something')

// NOTE: this will show up
// too.
msg = _('Something else')

// NOTE: but this won't
bar()

_('no comment here')
""")
        messages = list(extract.extract_javascript(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual('Something', messages[0][2])
        self.assertEqual(['NOTE: this will'], messages[0][3])
        self.assertEqual('Something else', messages[1][2])
        self.assertEqual(['NOTE: this will show up', 'too.'], messages[1][3])
        self.assertEqual('no comment here', messages[2][2])
        self.assertEqual([], messages[2][3])


class ExtractTestCase(unittest.TestCase):

    def test_invalid_filter(self):
        buf = BytesIO(b"""\
msg1 = _(i18n_arg.replace(r'\"', '"'))
msg2 = ungettext(i18n_arg.replace(r'\"', '"'), multi_arg.replace(r'\"', '"'), 2)
msg3 = ungettext("Babel", multi_arg.replace(r'\"', '"'), 2)
msg4 = ungettext(i18n_arg.replace(r'\"', '"'), "Babels", 2)
msg5 = ungettext('bunny', 'bunnies', random.randint(1, 2))
msg6 = ungettext(arg0, 'bunnies', random.randint(1, 2))
msg7 = _(hello.there)
msg8 = gettext('Rabbit')
msg9 = dgettext('wiki', model.addPage())
msg10 = dngettext(domain, 'Page', 'Pages', 3)
""")
        messages = \
            list(extract.extract('python', buf, extract.DEFAULT_KEYWORDS, [],
                                 {}))
        self.assertEqual([(5, ('bunny', 'bunnies'), [], None),
                          (8, 'Rabbit', [], None),
                          (10, ('Page', 'Pages'), [], None)], messages)

    def test_invalid_extract_method(self):
        buf = BytesIO(b'')
        self.assertRaises(ValueError, list, extract.extract('spam', buf))

    def test_different_signatures(self):
        buf = BytesIO(b"""
foo = _('foo', 'bar')
n = ngettext('hello', 'there', n=3)
n = ngettext(n=3, 'hello', 'there')
n = ngettext(n=3, *messages)
n = ngettext()
n = ngettext('foo')
""")
        messages = \
            list(extract.extract('python', buf, extract.DEFAULT_KEYWORDS, [],
                                 {}))
        self.assertEqual(len(messages), 2)
        self.assertEqual('foo', messages[0][1])
        self.assertEqual(('hello', 'there'), messages[1][1])

    def test_empty_string_msgid(self):
        buf = BytesIO(b"""\
msg = _('')
""")
        stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            messages = \
                list(extract.extract('python', buf, extract.DEFAULT_KEYWORDS,
                                     [], {}))
            self.assertEqual([], messages)
            assert 'warning: Empty msgid.' in sys.stderr.getvalue()
        finally:
            sys.stderr = stderr

    def test_warn_if_empty_string_msgid_found_in_context_aware_extraction_method(self):
        buf = BytesIO(b"\nmsg = pgettext('ctxt', '')\n")
        stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            messages = extract.extract('python', buf)
            self.assertEqual([], list(messages))
            assert 'warning: Empty msgid.' in sys.stderr.getvalue()
        finally:
            sys.stderr = stderr


def suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(extract))
    suite.addTest(unittest.makeSuite(ExtractPythonTestCase))
    suite.addTest(unittest.makeSuite(ExtractJavaScriptTestCase))
    suite.addTest(unittest.makeSuite(ExtractTestCase))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
