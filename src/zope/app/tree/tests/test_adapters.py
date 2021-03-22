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
"""Tree adapter tests
"""
from __future__ import absolute_import
import unittest

from zope.interface import implementer, directlyProvides
from zope.interface.interfaces import ComponentLookupError
from zope.security.checker import defineChecker
from zope.security.checker import NamesChecker
from zope.traversing.interfaces import IContainmentRoot
from zope.location.interfaces import ILocation
import zope.traversing.testing

from zope.container.interfaces import IReadContainer
from zope.container.sample import SampleContainer
from zope.container.contained import setitem
from zope.component.testing import PlacelessSetup
from zope.app.tree.tests import basetest as ztapi

from zope.app.tree.interfaces import IUniqueId, IChildObjects, \
    ITreeStateEncoder
from zope.app.tree.utils import TreeStateEncoder
from zope.app.tree.adapters import StubUniqueId, StubChildObjects, \
    LocationUniqueId, ContainerChildObjects, ContainerSiteChildObjects

import zope.component.interfaces


class SampleContent(object):
    pass


@implementer(zope.component.interfaces.ISite)
class SampleSite(SampleContainer):

    def setSiteManager(self, sm):
        self._sm = sm

    def getSiteManager(self):
        try:
            return self._sm
        except AttributeError:
            raise ComponentLookupError


class SiteManagerStub(object):
    """This stub is used for to check the permission on __getitem__."""

    def __getitem__(key):
        raise NotImplementedError()


class AdapterTestCase(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(AdapterTestCase, self).setUp()
        # provide necessary components
        zope.traversing.testing.setUp()
        ztapi.provideAdapter(None, IUniqueId, StubUniqueId)
        ztapi.provideAdapter(None, IChildObjects, StubChildObjects)
        ztapi.provideAdapter(ILocation, IUniqueId, LocationUniqueId)
        ztapi.provideAdapter(
            IReadContainer,
            IChildObjects,
            ContainerChildObjects)
        ztapi.provideAdapter(zope.component.interfaces.ISite,
                             IChildObjects, ContainerSiteChildObjects)
        ztapi.provideUtility(ITreeStateEncoder, TreeStateEncoder())
        self.makeObjects()

    def makeObjects(self):
        checker = NamesChecker(['__getitem__'])
        defineChecker(SiteManagerStub, checker)
        self.futurama = futurama = SampleSite()
        directlyProvides(futurama, IContainmentRoot)
        planetexpress = SampleContainer()
        robotfactory = SampleContainer()
        nimbus = SampleContainer()
        omicronpersei = SampleSite()

        bender = SampleContent()
        fry = SampleContent()
        leela = SampleContent()
        mom = SampleContent()
        zapp = SampleContent()
        kif = SampleContent()

        setitem(futurama, futurama.__setitem__, 'planetexpress', planetexpress)
        setitem(futurama, futurama.__setitem__, 'robotfactory', robotfactory)
        setitem(futurama, futurama.__setitem__, 'nimbus', nimbus)
        setitem(futurama, futurama.__setitem__, 'omicronpersei', omicronpersei)

        setitem(planetexpress, planetexpress.__setitem__, 'bender', bender)
        setitem(planetexpress, planetexpress.__setitem__, 'fry', fry)
        setitem(planetexpress, planetexpress.__setitem__, 'leela', leela)
        setitem(robotfactory, robotfactory.__setitem__, 'mom', mom)
        setitem(nimbus, nimbus.__setitem__, 'zapp', zapp)
        setitem(nimbus, nimbus.__setitem__, 'kif', kif)

    def test_stub_adapters(self):
        # test content unique id
        farnesworth = SampleContent()
        elzar = SampleContent()
        adapter = IUniqueId(farnesworth)
        adapter2 = IUniqueId(elzar)
        self.assertNotEqual(adapter.getId(), 'farnesworth')
        self.assertNotEqual(adapter2.getId(), 'elzar')
        # test for uniqueness
        self.assertNotEqual(adapter.getId(), adapter2.getId())

        # test content child objects
        adapter = IChildObjects(elzar)
        self.assertFalse(adapter.hasChildren())
        self.assertEqual(len(adapter.getChildObjects()), 0)
        # test with acquired content
        bender = self.futurama['planetexpress']['bender']
        adapter = IChildObjects(bender)
        self.assertFalse(adapter.hasChildren())
        self.assertEqual(len(adapter.getChildObjects()), 0)

    def test_location_uniqueid(self):
        # futurama does not have a name
        futurama = self.futurama
        adapter = IUniqueId(futurama)
        self.assertEqual(adapter.getId(), str(id(futurama)))

        # test container
        planetexpress = self.futurama['planetexpress']
        adapter = IUniqueId(planetexpress)
        self.assertEqual(adapter.getId(), 'planetexpress')

        # test content
        bender = self.futurama['planetexpress']['bender']
        adapter = IUniqueId(bender)
        self.assertEqual(adapter.getId(), r'bender\planetexpress')

    def test_container_childobjects(self):
        # test container with children
        futurama = self.futurama
        adapter = IChildObjects(futurama)
        self.assertTrue(adapter.hasChildren())
        self.assertEqual(list(adapter.getChildObjects()),
                         list(futurama.values()))

        # test acquired container with children
        planetexpress = self.futurama['planetexpress']
        adapter = IChildObjects(planetexpress)
        self.assertTrue(adapter.hasChildren())
        self.assertEqual(adapter.getChildObjects(),
                         list(planetexpress.values()))

        # test acquired container w/o children
        omicronpersei = self.futurama['omicronpersei']
        adapter = IChildObjects(omicronpersei)
        self.assertFalse(adapter.hasChildren())
        self.assertEqual(adapter.getChildObjects(), [])

    def test_container_site(self):
        sm = SiteManagerStub()
        futurama = self.futurama
        omicronpersei = self.futurama['omicronpersei']

        # test behaviour before and after setting a site
        adapter = IChildObjects(futurama)
        self.assertTrue(adapter.hasChildren())
        self.assertEqual(adapter.getChildObjects(),
                         list(futurama.values()))
        futurama.setSiteManager(sm)
        self.assertIn(sm, adapter.getChildObjects())

        adapter = IChildObjects(omicronpersei)
        self.assertFalse(adapter.hasChildren())
        omicronpersei.setSiteManager(sm)
        self.assertTrue(adapter.hasChildren())
        self.assertEqual(adapter.getChildObjects(), [sm])


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
