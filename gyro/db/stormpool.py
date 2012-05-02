from twisted.python import threadpool, util, failure, log, context
from twisted.internet import threads, reactor, defer

from storm import properties
from storm.locals import Reference, ReferenceSet, create_database, Store
from storm.exceptions import IntegrityError, DisconnectionError

import time
import random

STORMPOOLS = {}
DEFAULT_STORMPOOL = None

class Worker(object):
	def __init__(self, parent):
		self.parent = parent

		self.db = parent.db
		self.idleConnectionTimeout = parent.idleConnectionTimeout

		self.lastUsed = None
		self.store = None

	def _reset(self):
		"""
		Reset or create a Storm store
		"""
		if not self.store:
			self.store = Store(create_database(self.db))
		else:
			reactor.callFromThread(log.msg, "Reconnecting Storm connection")

			try:
				self.store.close()
				self.store.reset()
				del self.store
			except (DisconnectionError, IntegrityError), e:
				pass
			except:
				f = failure.Failure()
				reactor.callFromThread(log.err, f, 
						_why="Could not gracefully close Storm connection)",
						system="stormpool")

			self.store = Store(create_database(self.db))

	def _stop(self):
		if self.store:
			try:
				self.store.close()
				self.store.reset()
				del self.store
			except DisconnectionError:
				pass
			except:
				f = failure.Failure()
				reactor.callFromThread(log.err, f, 
						_why="Could not gracefully close Storm connection)",
						system="stormpool")

class ThreadWorker(Worker):
	"""
	A worker inside a single thread. Each worker will have it's own store and
	will re-use it when applicable according to the idle connection timeout
	"""

	def _transact(self, ctx, function, args, kwargs, onResult):
		"""
		Run this function within this thread, passing it a store that is already
		connected to the right database.
		"""

		retries = 0
		while retries <= self.parent.retries:
			try:
				if not self.store:
					self._reset()
				elif time.time() - self.lastUsed > self.idleConnectionTimeout:
					self._reset()

				self.lastUsed = time.time()

				if "store" not in kwargs:
					kwargs["store"] = self.store

				return context.call(ctx, function, *args, **kwargs)
			except (DisconnectionError, IntegrityError):
				self._reset()
				retries += 1

				if retries > self.parent.retries:
					return failure.Failure()

				time.sleep(random.uniform(1, 2 ** retries))
			except Exception:
				return failure.Failure()

class ThreadPool(threadpool.ThreadPool):
	"""
	A threadpool that creates a store and passes it into functions that are
	called
	"""
	def __init__(self, parent):
		threadpool.ThreadPool.__init__(self, *parent.args, **parent.kwargs)

		self.db = parent.db
		self.parent = parent
		self.idleConnectionTimeout = 60
		self.retries = parent.retries

		reactor.callWhenRunning(self.start)
		reactor.addSystemEventTrigger('after', 'shutdown', self.stop)

	def _worker(self):
		"""
		Continuously get events from our event queue and execute them until told
		to stop.
		"""

		worker = ThreadWorker(self)

		ct = self.currentThread()
		o = self.q.get()

		while o is not threadpool.WorkerStop:
			self.working.append(ct)
			ctx, function, args, kwargs, onResult = o
			del o

			result = worker._transact(ctx, function, args, kwargs, onResult)

			self.working.remove(ct)

			del function, args, kwargs

			success = True
			if isinstance(result, failure.Failure):
				success = False

			if onResult is not None:
				try:
					context.call(ctx, onResult, success, result)
				except:
					context.call(ctx, log.err)

			del ctx, onResult, result

			self.waiters.append(ct)
			o = self.q.get()
			self.waiters.remove(ct)

		worker._stop()

		self.threads.remove(ct)

	def deferToThread(self, f, *args, **kwargs):
		"""
		Run this function in a seperate thread and return the result as a
		Deferred
		"""

		d = defer.Deferred()

		def onResult(success, result):
			if success:
				reactor.callFromThread(d.callback, result)
			else:
				reactor.callFromThread(d.errback, result)

		self.callInThreadWithCallback(onResult, f, *args, **kwargs)

		return d

class ReactorThreadPool(Worker):
	def deferToThread(self, fn, *args, **kwargs):
		d = defer.Deferred()
		#Run this in the reactor thread
		reactor.callFromThread(self._transact, d, fn, *args, **kwargs)
		return d

	def _transact(self, d, fn, *args, **kwargs):
		retries = 0

		while True:
			try:
				if not self.store:
					self._reset()
				elif time.time() - self.lastUsed > self.idleConnectionTimeout:
					self._reset(self.store)

				self.lastUsed = time.time()

				if "store" not in kwargs:
					kwargs["store"] = self.store

				result = fn(*args, **kwargs)
				success = True
			except (DisconnectionError, IntegrityError):
				self._reset()
				retries += 1

				if retries > self.parent.retries:
					d.errback(failure.Failure)
					return

				time.sleep(random.uniform(1, 2 ** retries))
				continue
			except Exception:
				d.errback(failure.Failure())
				return

			#We don't want this inside our try/catch in case there is an
			#error in the callback itself
			d.callback(result)
			return

class StormPool(object):
	def __init__(self, db, idleConnectionTimeout=60, retries=1, pool=None,
			*args, **kwargs):

		self.db = db
		self.idleConnectionTimeout = 60
		self.pool = None
		self.args = args
		self.retries = retries
		self.kwargs = kwargs

		if pool:
			self.pool = pool
		elif self.db.startswith("sqlite"):
			self.pool = ReactorThreadPool(self) 
		else: 
			self.pool = ThreadPool(self)

		global DEFAULT_STORMPOOL
		DEFAULT_STORMPOOL = self

	def transact(self, fn, *args, **kwargs):
		return self.pool.deferToThread(fn, *args, **kwargs)

def create(db):
	return StormPool(db)

def transact(fn):
	def _transact(*args, **kwargs):
		return DEFAULT_STORMPOOL.transact(fn, *args, **kwargs)

	f = util.mergeFunctionMetadata(fn, _transact)
	f._blockingCall = fn
	return f

class ItemProxy(object):
	"""
	If we want to return a storm database result from a thread and use it within
	our main Twisted reactor thread
	"""

	def __init__(self, obj):
		self.parentClass = obj.__class__

		for key, value in obj.__class__.__dict__.iteritems():
			if isinstance(value, properties.Property):
				if isinstance(value, ReferenceSet) or isinstance(value,
						Reference):
					pass
				else:
					setattr(self, key, getattr(obj, key))

	def __str__(self):
		return "ItemProxy(%s)[%s]" % (str(self.parentClass), self.__dict__)

def unbindItem(item):
	"""
	If we want to return a database item to the main reactor thread, we need to
	unbind it from the store. We do this by actually creating a copy of the
	variable, no methods or references are copied across.
	"""

	if item:
		return ItemProxy(item)
	else:
		return item
