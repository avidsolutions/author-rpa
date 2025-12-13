"""Task scheduling for RPA framework."""

import time
import threading
from typing import Callable, Optional, List, Dict, Any
from datetime import datetime

import schedule

from .logger import get_logger


class Scheduler:
    """Schedule and run tasks at specified intervals."""

    def __init__(self):
        self.logger = get_logger("Scheduler")
        self._jobs: List[schedule.Job] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def every(self, interval: int = 1) -> schedule.Job:
        """Create a new scheduled job."""
        job = schedule.every(interval)
        self._jobs.append(job)
        return job

    def daily(self, at_time: str, task: Callable, *args, **kwargs) -> schedule.Job:
        """Schedule a task to run daily at a specific time.

        Args:
            at_time: Time in HH:MM format
            task: Function to execute
            *args, **kwargs: Arguments to pass to the task
        """
        job = schedule.every().day.at(at_time).do(task, *args, **kwargs)
        self._jobs.append(job)
        self.logger.info(f"Scheduled daily task '{task.__name__}' at {at_time}")
        return job

    def hourly(self, task: Callable, *args, **kwargs) -> schedule.Job:
        """Schedule a task to run every hour."""
        job = schedule.every().hour.do(task, *args, **kwargs)
        self._jobs.append(job)
        self.logger.info(f"Scheduled hourly task '{task.__name__}'")
        return job

    def minutes(self, interval: int, task: Callable, *args, **kwargs) -> schedule.Job:
        """Schedule a task to run every N minutes."""
        job = schedule.every(interval).minutes.do(task, *args, **kwargs)
        self._jobs.append(job)
        self.logger.info(f"Scheduled task '{task.__name__}' every {interval} minutes")
        return job

    def once(self, at_time: str, task: Callable, *args, **kwargs) -> None:
        """Schedule a task to run once at a specific time today."""
        def run_once():
            task(*args, **kwargs)
            return schedule.CancelJob

        job = schedule.every().day.at(at_time).do(run_once)
        self._jobs.append(job)
        self.logger.info(f"Scheduled one-time task '{task.__name__}' at {at_time}")

    def run_pending(self) -> None:
        """Run all pending scheduled tasks."""
        schedule.run_pending()

    def run_continuously(self, interval: float = 1.0) -> None:
        """Run the scheduler continuously in a background thread.

        Args:
            interval: Sleep interval between checks in seconds
        """
        self._running = True

        def run():
            while self._running:
                schedule.run_pending()
                time.sleep(interval)

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()
        self.logger.info("Scheduler started in background")

    def stop(self) -> None:
        """Stop the background scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        self.logger.info("Scheduler stopped")

    def clear(self) -> None:
        """Clear all scheduled jobs."""
        schedule.clear()
        self._jobs.clear()
        self.logger.info("All scheduled jobs cleared")

    @property
    def jobs(self) -> List[schedule.Job]:
        """Return list of scheduled jobs."""
        return self._jobs.copy()
