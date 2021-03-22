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
"""A node in the tree

"""
from zope.component import getUtility
from zope.interface import implementer
from zope.app.tree.interfaces import INode, IUniqueId, IChildObjects
from zope.app.tree.interfaces import ITreeStateEncoder


@implementer(INode)
class Node(object):
    """A tree node

    This object represents a node in the tree. It wraps the actual
    object and provides the INode interface to be relied on. In that
    way, it works similar to an adapter.

    This implementation is designed to be as lazy as possible.
    Especially, it will only create child nodes when necessary.
    """

    __slots__ = (
        'context', 'expanded', 'filter', '_id', '_expanded_nodes',
        '_child_nodes', '_child_objects_adapter',
    )

    def __init__(self, context, expanded_nodes=(), filter=None):
        self.context = context
        self.expanded = False
        self.filter = filter
        self._expanded_nodes = expanded_nodes
        self._child_nodes = None
        self._child_objects_adapter = None
        self._id = uid = IUniqueId(context).getId()
        if uid in expanded_nodes:
            self.expand()

    def __repr__(self):
        c = self.__class__
        return "<%s.%s id='%s' at %s>" % (
            c.__module__, c.__name__, self._id, id(self))

    def _create_child_nodes(self):
        """Create child nodes and save the result so we don't have
        to create that sequence every time"""
        nodes = []
        for obj in self.getChildObjects():
            node = Node(obj, self._expanded_nodes, self.filter)
            nodes.append(node)
        self._child_nodes = nodes

    def _get_child_objects_adapter(self):
        """Lazily create the child objects adapter"""
        if self._child_objects_adapter is None:
            self._child_objects_adapter = IChildObjects(self.context)
        return self._child_objects_adapter

    def expand(self, recursive=False):
        """See zope.app.tree.interfaces.INode"""
        self.expanded = True
        if recursive:
            for node in self.getChildNodes():
                node.expand(True)

    def collapse(self):
        """See zope.app.tree.interfaces.INode"""
        self.expanded = False

    def getId(self):
        """See zope.app.tree.interfaces.INode"""
        return self._id

    def hasChildren(self):
        """See zope.app.tree.interfaces.INode"""
        # we could actually test for the length of the result of
        # getChildObjects(), but we need to watch performance
        return self._get_child_objects_adapter().hasChildren()

    def getChildObjects(self):
        """See zope.app.tree.interfaces.INode"""
        filter = self.filter
        children = self._get_child_objects_adapter().getChildObjects()
        if filter:
            return [child for child in children if filter.matches(child)]
        return children

    def getChildNodes(self):
        """See zope.app.tree.interfaces.INode"""
        if not self.expanded:
            return []
        if self._child_nodes is None:
            # children nodes are not created until they are explicitly
            # requested through this method
            self._create_child_nodes()
        return self._child_nodes[:]

    def getFlatNodes(self):
        """See zope.app.tree.interfaces.INode"""
        nodes = []
        for node in self.getChildNodes():
            nodes.append(node)
            nodes += node.getFlatNodes()
        return nodes

    def getFlatDicts(self, maxdepth=0, row_state=None):
        """See zope.app.tree.interfaces.INode"""
        nodes = []
        if row_state is None:
            row_state = []
        encoder = getUtility(ITreeStateEncoder)

        if self.hasChildren() and len(row_state) > maxdepth:
            maxdepth = len(row_state)

        childNodes = self.getChildNodes()
        for node in childNodes:
            id = node.getId()
            expanded_nodes = self._expanded_nodes[:]
            if id in self._expanded_nodes:
                # if the node is already expanded, the toggle would
                # collapse it
                expanded_nodes.remove(id)
                row_state.append(node is not childNodes[-1])
            else:
                # if it isn't expanded, the toggle would expand it
                expanded_nodes += [id]
                row_state.append(False)
            flatdict = {
                'node': node,
                'tree-state': encoder.encodeTreeState(expanded_nodes),
                'row-state': row_state[:-1],
                'last-level-node': node is childNodes[-1],
            }
            nodes.append(flatdict)
            child_nodes, maxdepth = node.getFlatDicts(maxdepth, row_state)
            nodes += child_nodes
            row_state.pop()
        return nodes, maxdepth
