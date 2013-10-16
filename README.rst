gevent-helpers
==============

``gevent-helpers`` contains a collection of utilities which are helpful while
developing with ``gevent``.

Compatible with ``gevent==1.0rc3``.

fork()
------
A workaround for `gevent issue 154`__, until that issue is fixed.

__ http://code.google.com/p/gevent/issues/detail?id=154

BlockingDetector(timeout=1, raise_exc=AlarmInterrupt, aggressive=True)
----------------------------------------------------------------------

Use operating system signals to detect blocking threads.

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

Note: ``BlockingDetector`` overwrites the ``signal.SIGALRM`` handler and
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
      File ".../dirt/misc/gevent_.py", line 167, in alarm_handler
        raise exc
    gevent_helpers.AlarmInterrupt: blocking detected after timeout=1
