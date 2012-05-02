#-*- test-case-name: gyro.test.test_scheduler
"""
Schedule functions to be run at certain times
"""
import time
from gyro import core

class Scheduler(object):
    """
    A generic scheduler which schedules callLater's to repeatedly run a
    function. This will be extended by different types of schedulers that parse
    different schedule formats
    """
    fn = None
    cl = None
    args = None
    kwargs = None

    def __init__(self, fn, clock=None, args=None, kwargs=None):
        self.fn = fn
        self.args = args or []
        self.kwargs = kwargs or {}
        self.clock = clock

        self.shutdown_trigger = core.call_on_shutdown(self.stop)

    def start(self):
        """
        Start running this schedule
        """
        return self.schedule()

    def schedule(self):
        """
        Find the next time we should run our function and schedule a call to run
        then
        """
        n = self.next()
        if n is not None:
            if self.clock:
                self.cl = self.clock.callLater(n, self.run)
            else:
                self.cl = core.call_later(n, self.run)
        else:
            self.cl = None

    def run(self):
        """
        Run our function and schedule the next call
        """
        self.fn(*self.args, **self.kwargs)
        self.schedule()

    def next(self):
        """
        How many seconds until we should run again, return None to not execute
        again. This should be overloaded by all schedulers
        """
        pass

    def stop(self):
        """
        Stop this scheduler
        """
        if self.cl and self.cl.active():
            self.cl.cancel()

        try:
            core.cancel_call_on_shutdown(self.shutdown_trigger)
        except (KeyError, ValueError, TypeError):
            pass

class SimpleScheduler(Scheduler):
    """
    A scheduler that takes in a simple interval string such as "30s" or "50m"
    and runs the function according to this inverval

    Accepts intervals in format 1d2h3m4s500ms (or any portion)
    """

    def __init__(self, fn, interval, start=True, clock=None, args=None,
            kwargs=None):
        super(SimpleScheduler, self).__init__(fn, clock, args, kwargs)
        self.fn = fn
        self.interval = interval
        self.seconds = 0.0

        import re
        regex = re.compile("(?:(?P<days>\d+)d)?(?:(?P<hours>\d+)h)?"
                "(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?"
                "(?:(?P<miliseconds>\d+)ms)?")

        d = regex.match(interval).groupdict()

        if d["days"]:
            self.seconds += 60 * 60 * 24 * int(d["days"])
        if d["hours"]:
            self.seconds += 60 * 60 * int(d["hours"])
        if d["minutes"]:
            self.seconds += 60 * int(d["minutes"])
        if d["seconds"]:
            self.seconds += int(d["seconds"])
        if d["miliseconds"]:
            self.seconds += int(d["miliseconds"]) * .001

        if start:
            self.schedule()

    def next(self):
        return self.seconds

class CronScheduler(Scheduler):
    """
    A scheduler that will run a function according to a cron format string.

    This method uses the croniter package to parse the format
    (http://pypi.python.org/pypi/croniter/)
    """

    def __init__(self, fn, interval, start=True, clock=None, args=None,
            kwargs=None):
        super(CronScheduler, self).__init__(fn, clock, args, kwargs)
        self.fn = fn

        from croniter import croniter
        if clock:
            self.iter = croniter(interval, clock.seconds())
        else:
            self.iter = croniter(interval)

        if start:
            self.schedule()

    def next(self):
        n = self.iter.get_next()
        if self.clock:
            now = self.clock.seconds()
        else:
            now = time.time()

        return n - now

#TODO rrule scheduler

class every(object):
    """
    Decorator for SimpleScheduler which will run the function according to the
    interval given
    """
    def __init__(self, interval):
        self.interval = interval

    def __call__(self, fn):
        s = SimpleScheduler(fn, self.interval)
        return fn

class cron(object):
    def __init__(self, expression):
        pass

    def __call__(self, fn):
        return fn

class rrule(object):
    def __init__(self, rule):
        pass

    def __call__(self, fn):
        pass

#TODO other common schedule things
def on_start(fn):
    return fn

def on_shutdown(fn):
    return fn
