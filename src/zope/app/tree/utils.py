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
"""Static tree utilities

"""
import zlib
from binascii import a2b_base64
from binascii import b2a_base64

from zope.interface import implementer

from zope.app.tree.interfaces import ITreeStateEncoder


@implementer(ITreeStateEncoder)
class TreeStateEncoder:
    """Encodes tree state.

    Implements :class:`zope.app.tree.interfaces.ITreeStateEncoder`.

    >>> expanded_nodes = ['a', 'c', 'foobar']
    >>> encoder = TreeStateEncoder()
    >>> encoded = encoder.encodeTreeState(expanded_nodes)
    >>> decoded = encoder.decodeTreeState(encoded)
    >>> decoded == expanded_nodes
    True
    """

    # note that this implementation relies on the node ids not
    # containing colons
    def encodeTreeState(self, expanded_nodes):
        tree_state = ":".join(expanded_nodes)
        if not isinstance(tree_state, bytes):
            tree_state = tree_state.encode("utf-8")
        tree_state = zlib.compress(tree_state)
        return b2a(tree_state)

    def decodeTreeState(self, tree_state):
        tree_state = a2b(tree_state)
        tree_state = zlib.decompress(tree_state)
        if not isinstance(tree_state, str):
            tree_state = tree_state.decode('utf-8')
        return tree_state.split(":")

#
# The following code was originally part of Zope2's
# ZTUtils.Tree module
#


a2u_map = str.maketrans('+/=', '-._')
u2a_map = str.maketrans('-._', '+/=')


def b2a(s):
    '''Encode a value as a cookie- and url-safe string.

    Encoded string use only alphanumeric characters, and "._-".
    '''
    assert isinstance(s, bytes)

    frags = []
    for i in range(0, len(s), 57):
        frags.append(b2a_base64(s[i:i + 57])[:-1])

    encoded = b''.join(frags)
    if not isinstance(encoded, str):
        encoded = encoded.decode('ascii')
    return str.translate(encoded, a2u_map)


def a2b(s):
    '''Decode a b2a-encoded string.'''
    assert isinstance(s, str)

    s = str.translate(s, u2a_map)
    frags = []
    for i in range(0, len(s), 76):
        frags.append(a2b_base64(s[i:i + 76]))
    return b''.join(frags)
