"""
scheduler

A small module that wraps APScheduler and helps manage scheduling of tasks, in concert
with Dramatiq which provides the async execution handling.

This can be used either via decorator to set static schedules for tasks to execute on,
or programmatically to request a task be scheduled dynamically (which will then be kept
persistently in the database).
"""
import logging
from threading import Event
from typing import Callable

import dramatiq
from apscheduler.executors.debug import DebugExecutor
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.base import STATE_STOPPED, BaseScheduler
from apscheduler.util import TIMEOUT_MAX
from dramatiq import Worker
from dramatiq.middleware import SkipMessage
from dramatiq.worker import _WorkerThread  # noqa
from pytz import utc

from opinionated.fastapi.db import engine

logger = logging.getLogger(__name__)


class CustomScheduler(BaseScheduler):
    server: bool = False

    def __init__(self, scheduler_server=False):
        self.server = scheduler_server
        if self.server:
            pool = ThreadPoolExecutor()
        else:
            # Don't bother starting a threadpool if we aren't ever going to run a job locally
            pool = DebugExecutor()

        job_store = SQLAlchemyJobStore(engine=engine)
        self._event = Event()

        super().__init__(
            jobstores={"default": job_store},
            executors={"default": pool},
            job_defaults={},
            timezone=utc,
        )

    def start(self, *args, **kwargs):
        if self._event is None or self._event.is_set():
            self._event = Event()

        super().start(*args, **kwargs)
        if self.server:
            self._main_loop()

    def shutdown(self, wait=True):
        super().shutdown(wait)
        self._event.set()

    def _main_loop(self):
        wait_seconds = TIMEOUT_MAX
        while self.state != STATE_STOPPED:
            self._event.wait(wait_seconds)
            self._event.clear()
            wait_seconds = self._process_jobs()

    def wakeup(self):
        """Custom wakeup that sets event flag if we're in runscheduler, or otherwise sends a dramatiq event"""
        if self.server:
            self._event.set()
        else:
            # If dramatiq is set up...
            # Send a task to dramatiq broker to let the scheduler know
            dramatiq.get_broker().enqueue(
                dramatiq.Message(
                    queue_name="scheduler",
                    actor_name="wakeup-scheduler",
                    args=(),
                    kwargs={},
                    options={},
                )
            )


class CustomWorkerThread(_WorkerThread):
    wakeup: Callable[..., None]

    def __init__(self, *args, wakeup: Callable[..., None], **kwargs):
        super().__init__(*args, **kwargs)
        setattr(self, "wakeup", wakeup)

    def process_message(self, message):
        """Custom version of process_message that is specific to the scheduler."""
        try:
            self.logger.debug(
                "Received message %s with id %r.", message, message.message_id
            )
            if not message.failed:
                self.wakeup(*message.args, **message.kwargs)
        except SkipMessage:
            self.logger.warning("Message %s was skipped.", message)
        except BaseException as e:
            message.stuff_exception(e)
        finally:
            self.consumers[message.queue_name].post_process_message(message)
            self.work_queue.task_done()
            message.clear_exception()


class CustomWorker(Worker):
    """A custom dramatiq worker that overrides the normal actor mechanism and uses our own callback"""

    wakeup: Callable[..., None]

    def __init__(self, *args, wakeup: Callable[..., None], **kwargs):
        super().__init__(*args, **kwargs)
        setattr(self, "wakeup", wakeup)

    def _add_worker(self):
        """Custom function to override the normal worker thread, allowing us to just run the wakeup callback"""

        worker = CustomWorkerThread(
            wakeup=self.wakeup,
            broker=self.broker,
            consumers=self.consumers,
            work_queue=self.work_queue,
            worker_timeout=self.worker_timeout,
        )
        worker.start()
        self.workers.append(worker)


def run_scheduler() -> None:
    """
    Run a scheduler process, this should be a separate process and only one should be running at any time.
    """

    # Set up the scheduler. This is separate from the scheduler that gets launched as part of the normal
    #  api server/worker startup, that one doesn't actually run a scheduling loop, just provides the jobstore.
    scheduler_process = CustomScheduler(scheduler_server=True)

    # Now before we start the scheduler (which will block anything more on this thread), set up the dramatiq Worker.
    # This is a custom worker that receives messages from the 'scheduler' queue, and uses those to "wake up" the
    #  scheduler in the event of new/modified jobs.
    def wakeup():
        scheduler_process.wakeup()

    # We probably only need or want one thread, to be honest...lets see what works best though.
    worker = CustomWorker(
        dramatiq.get_broker(), queues={"scheduler"}, worker_threads=4, wakeup=wakeup
    )
    worker.start()
    # Now that we've got everything running, start the scheduler.
    scheduler_process.start()


dramatiq.get_broker().declare_queue("scheduler")
# This is the scheduler we use for workers and the main webserver processes. It won't actually schedule anything, it
#  will just add the jobs to the sqlalchemy table, and send a "wakeup" task to the scheduler queue in dramatiq, which
#  will let the scheduler process know to wake up and reschedule jobs accordingly.
scheduler = CustomScheduler(scheduler_server=False)
# start() won't actually do much of anything as we aren't running an actual scheduler here
scheduler.start()
