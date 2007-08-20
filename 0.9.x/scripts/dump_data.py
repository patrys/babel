#!/usr/bin/env python
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

from pprint import pprint
import sys

from babel.localedata import load

if len(sys.argv) > 2:
    pprint(load(sys.argv[1]).get(sys.argv[2]))
else:
    pprint(load(sys.argv[1]))
