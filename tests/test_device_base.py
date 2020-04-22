import unittest
from brick.device import base


class SingleClickHandlerTest(unittest.TestCase):
    def test_single(self):
        handler = base.SingleClickHandler(start=0)
        self.assertEqual(handler.get_events(False, ms=50), [])
        self.assertEqual(handler.get_events(False, ms=100), [])
        self.assertEqual(handler.get_events(True, ms=150), ['begin', 'single'])
        self.assertEqual(handler.get_events(True, ms=200), [])
        self.assertEqual(handler.get_events(False, ms=250), ['end'])
        self.assertEqual(handler.get_events(False, ms=300), [])


class LongClickHandlerTest(unittest.TestCase):
    def test_single(self):
        handler = base.LongClickHandler(long_click=1000, start=0)
        self.assertEqual(handler.get_events(False, ms=50), [])
        self.assertEqual(handler.get_events(False, ms=100), [])
        self.assertEqual(handler.get_events(True, ms=150), ['begin'])
        self.assertEqual(handler.get_events(True, ms=200), [])
        self.assertEqual(handler.get_events(False, ms=250), ['single', 'end'])
        self.assertEqual(handler.get_events(False, ms=300), [])

    def test_long(self):
        handler = base.LongClickHandler(long_click=1000, start=0)
        self.assertEqual(handler.get_events(False, ms=50), [])
        self.assertEqual(handler.get_events(True, ms=100), ['begin'])
        self.assertEqual(handler.get_events(True, ms=1100), [])
        self.assertEqual(handler.get_events(True, ms=1150), ['long'])
        self.assertEqual(handler.get_events(True, ms=1200), [])
        self.assertEqual(handler.get_events(False, ms=1500), ['end'])
        self.assertEqual(handler.get_events(False, ms=1550), [])
