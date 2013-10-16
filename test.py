import time
import mock
import gevent
from unittest import TestCase

from gevent_helpers import BlockingDetector, AlarmInterrupt

# From https://github.com/traviscline/gevent-utils/blob/master/tests.py, with
# modifications

def busysleep(seconds):
    target = time.time() + seconds
    while time.time() < target:
        pass

class TestBlockingDetector(TestCase):
    @mock.patch.object(BlockingDetector, 'alarm_handler')
    def test_triggered_when_blocking(self, mock_alarm_handler):
        detector_greenlet = gevent.spawn(BlockingDetector(0.25))
        gevent.sleep()

        self.assertFalse(mock_alarm_handler.called)
        busysleep(0.1)
        self.assertFalse(mock_alarm_handler.called)
        busysleep(0.5)

        # after two seconds of sleep the alarm_handler should have been called
        self.assertTrue(mock_alarm_handler.called)
        detector_greenlet.kill()

    def test_actual_exception_raised(self):
        detector_greenlet = gevent.spawn(BlockingDetector(0.25))
        gevent.sleep()

        self.assertRaises(AlarmInterrupt, busysleep, 1)
        detector_greenlet.kill()

    @mock.patch.object(BlockingDetector, 'alarm_handler')
    def test_not_triggered_when_cooperating(self, mock_alarm_handler):
        detector_greenlet = gevent.spawn(BlockingDetector(0.25))
        gevent.sleep()

        self.assertFalse(mock_alarm_handler.called)
        gevent.sleep(0.5)
        self.assertFalse(mock_alarm_handler.called)
        detector_greenlet.kill()

if __name__ == "__main__":
    import unittest
    unittest.main()
