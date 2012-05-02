from twisted.trial import unittest
from gyro import scheduler
from twisted.internet import task
from collections import deque
import time
import datetime

class TestScheduler(unittest.TestCase):
    def test_base_scheduler(self):
        """
        Test the base scheduler that everything derives from. Given a scheduler
        that returns the number of seconds to wait, confirm that the function is
        called at the correct intervals
        """

        intervals = deque([1, 5, 10, 30, 60])

        class TestingScheduler(scheduler.Scheduler):
            def __init__(self):
                self.clock = task.Clock()
                self.called_count = 0
                super(TestingScheduler, self).__init__(self.fn, self.clock)

            def fn(self):
                self.called_count += 1

            def next(self):
                return intervals.popleft()

        s = TestingScheduler()
        s.start()

        self.assertEquals(s.called_count, 0)
        self.assertNotEquals(s.cl, None)

        #Called once after one second
        s.clock.advance(1)
        self.assertEquals(s.called_count, 1)

        #Not called again after 4
        s.clock.advance(4)
        self.assertEquals(s.called_count, 1)

        #Called after another second (5 total)
        s.clock.advance(1)
        self.assertEquals(s.called_count, 2)

        s.clock.advance(10)
        self.assertEquals(s.called_count, 3)

        s.clock.advance(30)
        self.assertEquals(s.called_count, 4)

        s.stop()

class TestSimpleScheduler(unittest.TestCase):
    """
    Test our simple interval scheduler
    """
    def test_format_parser(self):
        #Just seconds
        s = scheduler.SimpleScheduler(None, "30s", start=False)
        self.assertEquals(s.seconds, 30)

        #Hours, minutes, seconds
        s = scheduler.SimpleScheduler(None, "1h30m30s", start=False)
        self.assertEquals(s.seconds, 5430)

        #Days, hours, minutes, seconds
        s = scheduler.SimpleScheduler(None, "2d1h30m30s", start=False)
        self.assertEquals(s.seconds, 178230)

        #Minutes, miliseconds
        s = scheduler.SimpleScheduler(None, "1m400ms", start=False)
        self.assertEquals(s.seconds, 60.4)

    def test_next(self):
        #Test we are return the correct interval for our scheduler
        s = scheduler.SimpleScheduler(None, "30s", start=False)
        self.assertEquals(s.next(), 30)
        self.assertEquals(s.next(), 30)

class TestCronScheduler(unittest.TestCase):
    """
    Test our cron format scheduler
    """

    def test_interval(self):
        c = task.Clock()
        d = datetime.datetime(2012, 02, 13, 17, 03, 0)
        t = time.mktime(d.timetuple())
        c.advance(t)

        s = scheduler.CronScheduler(None, '*/5 * * * *', start=False, clock=c)

        #First we should wait 2 minutes to get to 5 past
        self.assertEquals(s.next(), 120)
        c.advance(120)

        #And then 5 minutes afterwards
        self.assertEquals(s.next(), 300)
        c.advance(300)
        self.assertEquals(s.next(), 300)

    def test_complex(self):
        c = task.Clock()
        d = datetime.datetime(2012, 02, 13, 17, 07)
        t = time.mktime(d.timetuple())
        c.advance(t)

        s = scheduler.CronScheduler(None, '2 4 * * mon,fri', start=False,
                clock=c)

        #04:02 every monday and friday

        #Friday
        next = s.next()
        n = d + datetime.timedelta(seconds=next)
        expected = datetime.datetime(2012, 02, 17, 04, 02, 0)
        self.assertEquals(n, expected)
        s.clock.advance(next)

        #Monday
        next = s.next()
        n = n + datetime.timedelta(seconds=next)
        expected = datetime.datetime(2012, 02, 20, 04, 02, 0)
        self.assertEquals(n, expected)
        s.clock.advance(next)

        #Friday
        next = s.next()
        n = n + datetime.timedelta(seconds=next)
        expected = datetime.datetime(2012, 02, 24, 04, 02, 0)
        self.assertEquals(n, expected)
