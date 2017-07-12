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
"""Test tree node code.

"""
from __future__ import absolute_import
import unittest
from zope.app.tree.tests.basetest import BaseTestCase
from zope.interface import implementer
from zope.container.interfaces import IObjectFindFilter
from zope.app.tree.node import Node


@implementer(IObjectFindFilter)
class FilterByObject(object):
    """Simple filter that filters out any objects that wasn't passed
    in as a valid object before
    """

    def __init__(self, *tree):
        # Flatten recursive list
        self.objects = []
        tree = list(tree)
        while tree:
            candidate = tree.pop()
            if isinstance(candidate, list):
                tree.extend(candidate)
            else:
                self.objects.append(candidate)

    def matches(self, obj):
        return obj in self.objects


class NodeTestCase(BaseTestCase):

    def setUp(self):
        super(NodeTestCase, self).setUp()
        self.makeItems()

    def test_expand_collapse(self):
        # first the node is expanded
        root_node = self.root_node
        self.assertTrue(root_node.expanded)
        # now collapse it
        root_node.collapse()
        self.assertFalse(root_node.expanded)
        # make sure there are no children nodes returned!
        self.assertEqual(root_node.getChildNodes(), [])
        # expand it again
        root_node.expand()
        self.assertTrue(root_node.expanded)
        self.assertEqual(2, len(root_node.getChildNodes()))

        root_node.collapse()
        root_node.expand(recursive=True)
        self.assertEqual(2, len(root_node.getChildNodes()))

        # coverage
        repr(root_node)

    def test_children(self):
        # test hasChildren()
        root_node = self.root_node
        self.assertTrue(root_node.hasChildren())

        # test getChildNodes()
        children = [node.context for node in root_node.getChildNodes()]
        expected = [self.items['b'], self.items['c']]
        self.assertEqual(children, expected)

        # test with filter
        expand_all = self.items.keys()  # expand all nodes
        # emulate node expansion with the FilterByObject filter
        filter = FilterByObject([self.items[id] for id in self.expanded_nodes])
        filtered_root = Node(self.root_obj, expand_all, filter)
        children = [node.context for node in filtered_root.getChildNodes()]
        expected = [self.items['c']]
        self.assertEqual(children, expected)

    def test_flat(self):
        # test getFlatNodes()
        root_node = self.root_node
        flat = root_node.getFlatNodes()
        children = [node.context for node in flat]
        # 'a' is not expected because the node on which getFlatNodes()
        # is called is not in the list
        expected = [self.items[i] for i in "bcfg"]
        self.assertEqual(children, expected)

    def test_pre_expanded(self):
        # 'a' is not expected because the node on which getFlatNodes()
        # is called is not in the list
        expected = [self.items[i] for i in "bcfg"]
        # test against to getFlatNodes()
        flat = [node.context for node in self.root_node.getFlatNodes()]
        self.assertEqual(flat, expected)

    def test_flat_dicts(self):
        flat, maxdepth = self.root_node.getFlatDicts()
        self.assertEqual(maxdepth, 2)
        self.assertEqual(len(flat), len(self.root_node.getFlatNodes()))
        bdict = flat[0]
        node = bdict['node']
        self.assertEqual(bdict['row-state'], [])
        self.assertEqual(node.getId(), 'b')
        self.assertTrue(node.hasChildren())
        self.assertIs(node.context, self.items['b'])

    def test_depth(self):
        expanded = ['a', 'c', 'f']
        root_node = Node(self.root_obj, expanded)
        flat, maxdepth = root_node.getFlatDicts()
        self.assertEqual(6, len(flat))
        self.assertEqual(2, maxdepth)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
