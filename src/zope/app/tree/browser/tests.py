##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Static Tree Tests

"""

import unittest

import zope.component
import zope.component.interfaces
import zope.interface
from zope.component import getMultiAdapter
from zope.interface import alsoProvides
from zope.location.traversing import LocationPhysicallyLocatable
from zope.publisher.browser import TestRequest
from zope.traversing.interfaces import IContainmentRoot

from zope.app.tree.browser import StatefulTreeView
from zope.app.tree.browser.cookie import CookieTreeView
from zope.app.tree.tests import basetest as ztapi
from zope.app.tree.tests.basetest import BaseTestCase
from zope.app.tree.utils import TreeStateEncoder


class StatefulTreeViewTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.makeItems()
        # provide the view for all objects (None)
        ztapi.browserView(None, 'stateful_tree', StatefulTreeView)
        self.request = None

    # TODO: test stateful tree view


class CookieTreeViewTest(StatefulTreeViewTest):

    def setUp(self):
        super().setUp()
        ztapi.browserView(None, 'cookie_tree', CookieTreeView)
        zope.component.provideAdapter(LocationPhysicallyLocatable,
                                      (zope.interface.Interface,))

    def makeRequestWithVar(self):
        varname = CookieTreeView.request_variable
        encoder = TreeStateEncoder()
        tree_state = encoder.encodeTreeState(self.expanded_nodes)
        environ = {varname: tree_state}
        request = TestRequest(environ=environ)
        return request

    def test_cookie_tree_pre_expanded(self):
        request = self.makeRequestWithVar()
        view = getMultiAdapter((self.root_obj, request),
                               name='cookie_tree')
        view.cookieTree()
        self.assertTrue(self.root_node.expanded)
        for node in self.root_node.getFlatNodes():
            self.assertEqual(node.expanded,
                             node.getId() in self.expanded_nodes)

    def test_cookie_tree_sets_cookie(self):
        request = self.makeRequestWithVar()
        view = getMultiAdapter((self.root_obj, request),
                               name='cookie_tree')
        view.cookieTree()
        self.assertIsNotNone(request.response.getCookie(view.request_variable))

    def test_cookie_tree_site_tree(self):
        request = self.makeRequestWithVar()
        alsoProvides(self.items['a'], IContainmentRoot)
        alsoProvides(self.items['c'], zope.component.interfaces.ISite)
        view = getMultiAdapter((self.items['f'], request),
                               name='cookie_tree')
        cookie_tree = view.siteTree()
        self.assertIs(cookie_tree.context, self.items['c'])

    def test_cookie_tree_root_tree(self):
        request = self.makeRequestWithVar()
        alsoProvides(self.items['c'], IContainmentRoot)
        view = getMultiAdapter((self.items['f'], request),
                               name='cookie_tree')
        cookie_tree = view.rootTree()
        self.assertIs(cookie_tree.context, self.items['c'])

    def test_virtualHostTree(self):
        request = self.makeRequestWithVar()
        alsoProvides(self.items['c'], IContainmentRoot)
        view = getMultiAdapter((self.items['f'], request),
                               name='cookie_tree')
        # No virtual host root
        self.assertEqual(view.virtualHostTree().getId(), 'c')

        # VHR set
        request.getVirtualHostRoot = lambda: self.items['a']
        self.assertEqual(view.virtualHostTree().getId(), 'a')


class TestConfiguration(BaseTestCase):

    def test_configuration(self):
        from zope.configuration import xmlconfig
        xmlconfig.string(r"""
        <configure xmlns="http://namespaces.zope.org/zope">
           <include package="zope.app.tree.browser" file="ftesting.zcml" />
        </configure>
        """)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
