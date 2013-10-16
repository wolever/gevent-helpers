"""
Utilities that are helpful while developing with gevent.

BlockingDetector based on https://github.com/traviscline/gevent-utils/blob/master/gevent_utils.py
"""

import sys
import signal
import logging
import traceback

import gevent

log = logging.getLogger(__name__)


def fork():
    """ A workaround for gevent issue 154[0], until that is fixed.

        [0]: http://code.google.com/p/gevent/issues/detail?id=154 """
    tp = gevent.get_hub().threadpool
    if len(tp):
        sys.stderr.write("WARNING: calling fork() while threads are active; "
                         "they will be killed.\n")
    tp.kill()
    tp.join()
    result = gevent.fork()
    gevent.sleep(0)
    return result


def get_arm_alarm():
    if hasattr(signal, "setitimer"):
        def alarm_itimer(seconds):
            signal.setitimer(signal.ITIMER_REAL, seconds)
        return alarm_itimer
    try:
        import itimer
        return itimer.alarm
    except ImportError:
        pass
    import math
    def alarm_signal(seconds):
        signal.alarm(math.ceil(seconds))
    return alarm_signal
arm_alarm = get_arm_alarm()


class AlarmInterrupt(BaseException):
    pass


class BlockingDetector(object):
    """Use operating system signals to detect blocking threads.

    ``timeout=1`` is the number of seconds to wait before considering the
    thread blocked (note: if ``signal.setitimer`` or the ``itimer`` package is
    available, this can be a real number; otherwise it will be rounded up to
    the nearest integer).

    ``raise_exc=AlarmInterrupt`` controls which exception will be raised
    in the blocking thread. If ``raise_exc`` is False-ish, no exception will be
    raised (a ``log.warning`` message, including stack trace, will always be
    issued). **NOTE**: the default value, ``AlarmInterrupt``, is a subclass of
    ``BaseException``, so it *will not* be caught by ``except Exception:`` (it
    will be caught by ``dirt.runloop``). For example::

        # Don't raise an exception, only log a warning message and stack trace:
        BlockingDetector(raise_exc=False)

        # Raise ``MyException()`` and lot a warning message:
        BlockingDetector(raise_exc=MyException())

        # Raise ``MyException("blocking detected after timeout=...")`` and log
        # a warning message:
        BlockingDetector(raise_exc=MyException)

    ``aggressive=True`` determines whether the blocking detector will reset
    as soon as it is triggered, or whether it will wait until the blocking
    thread yields before it resets. For example, if ``aggressive=True``,
    ``raise_exc=False``, and ``timeout=1``, a log message will be written for
    every second that a thread blocks. However, if ``aggressive=False``, only
    one log message will be written until the blocking thread yields, at which
    point the alarm will be reset.

    Note: ``BlockingDetector`` overwrites the ``signal.SIGALRM`` handler, and
    does not attempt to save the previous value.

    For example::

        >>> def spinblock():
        ...     while True:
        ...         pass
        >>> gevent.spawn(BlockingDetector())
        >>> gevent.sleep()
        >>> spinblock()
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
          File "<stdin>", line 3, in spinblock
          File ".../gevent_helpers.py", line 167, in alarm_handler
            raise exc
        gevent_helpers.AlarmInterrupt: blocking detected after timeout=1

    """
    def __init__(self, timeout=1, raise_exc=AlarmInterrupt, aggressive=True):
        self.timeout = timeout
        self.raise_exc = raise_exc
        self.aggressive = aggressive

    def __call__(self):
        """
        Loop for 95% of our detection time and attempt to clear the signal.
        """
        try:
            while True:
                self.reset_signal()
                gevent.sleep(self.timeout * 0.95)
        finally:
            self.clear_signal()

    def arm_alarm(self, timeout):
        global arm_alarm
        arm_alarm(timeout)

    def alarm_handler(self, signum, frame):
        log.warning("blocking detected after timeout=%r; stack:\n%s",
                    self.timeout, "".join(traceback.format_stack(frame)))
        if self.aggressive:
            self.reset_signal()
        if self.raise_exc:
            exc = self.raise_exc
            if issubclass(exc, type):
                exc = exc("blocking detected after timeout=%r"
                          %(self.timeout, ))
            raise exc

    def reset_signal(self):
        signal.signal(signal.SIGALRM, self.alarm_handler)
        self.arm_alarm(self.timeout)

    def clear_signal(self):
        self.arm_alarm(0)


if __name__ == "__main__":
    import time

    def test_blocking_thread():
        try:
            target = time.time() + 2
            while time.time() < target:
                pass
            print "ERROR: AlarmInterrupt not raised!"
        except AlarmInterrupt:
            print "ok."
    print "Testing that AlarmInterrupt is correctly raised...",
    gevent.spawn(BlockingDetector(timeout=0.25,))
    gevent.spawn(test_blocking_thread).join()

    def test_nonblocking_thread():
        try:
            gevent.sleep(0.5)
            print "ok."
        except Exception, e:
            print "ERROR: Unexpected exception:", e
    print "Testing that AlarmInterrupt not raised on gevent.sleep...",
    gevent.spawn(BlockingDetector(timeout=0.25))
    gevent.spawn(test_nonblocking_thread).join()
