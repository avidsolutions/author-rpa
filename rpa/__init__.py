"""
RPA Framework - Python-based Robotic Process Automation

A modular framework for automating tasks including:
- Documentation creation
- Web scraping
- File processing
- PDF automation
- Email automation
- Spreadsheet automation
- Desktop automation
- API integration
- Database operations
"""

from typing import Optional

from .core import Config, get_logger, Scheduler
from .modules import (
    SpreadsheetModule,
    FileModule,
    PDFModule,
    DocsModule,
    EmailModule,
    ScraperModule,
    APIModule,
    DatabaseModule,
    DesktopModule,
)
from .workflows import Workflow, WorkflowStep


__version__ = "1.0.0"
__author__ = "Malcolm Adams"


class RPA:
    """Main RPA automation class providing access to all modules."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize RPA with optional configuration.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config = Config(config_path)
        self.logger = get_logger("RPA")
        self.scheduler = Scheduler()

        # Initialize modules
        self._spreadsheet: Optional[SpreadsheetModule] = None
        self._files: Optional[FileModule] = None
        self._pdf: Optional[PDFModule] = None
        self._docs: Optional[DocsModule] = None
        self._email: Optional[EmailModule] = None
        self._scraper: Optional[ScraperModule] = None
        self._api: Optional[APIModule] = None
        self._database: Optional[DatabaseModule] = None
        self._desktop: Optional[DesktopModule] = None

        self.logger.info("RPA initialized")

    # Lazy-loaded module properties

    @property
    def spreadsheet(self) -> SpreadsheetModule:
        """Spreadsheet automation module."""
        if self._spreadsheet is None:
            self._spreadsheet = SpreadsheetModule()
        return self._spreadsheet

    @property
    def files(self) -> FileModule:
        """File processing module."""
        if self._files is None:
            self._files = FileModule()
        return self._files

    @property
    def pdf(self) -> PDFModule:
        """PDF automation module."""
        if self._pdf is None:
            self._pdf = PDFModule()
        return self._pdf

    @property
    def docs(self) -> DocsModule:
        """Documentation creation module."""
        if self._docs is None:
            self._docs = DocsModule()
        return self._docs

    @property
    def email(self) -> EmailModule:
        """Email automation module."""
        if self._email is None:
            self._email = EmailModule(
                smtp_server=self.config.get("email.smtp_server"),
                smtp_port=self.config.get("email.smtp_port", 587),
                imap_server=self.config.get("email.imap_server"),
                imap_port=self.config.get("email.imap_port", 993),
                username=self.config.get("email.username"),
                password=self.config.get("email.password"),
            )
        return self._email

    @property
    def scraper(self) -> ScraperModule:
        """Web scraping module."""
        if self._scraper is None:
            self._scraper = ScraperModule(
                user_agent=self.config.get("scraper.user_agent"),
                rate_limit=self.config.get("scraper.rate_limit", 1.0),
            )
        return self._scraper

    @property
    def api(self) -> APIModule:
        """API integration module."""
        if self._api is None:
            self._api = APIModule()
        return self._api

    @property
    def database(self) -> DatabaseModule:
        """Database operations module."""
        if self._database is None:
            connection_string = self.config.get("database.default")
            self._database = DatabaseModule(connection_string)
        return self._database

    @property
    def desktop(self) -> DesktopModule:
        """Desktop automation module."""
        if self._desktop is None:
            self._desktop = DesktopModule()
        return self._desktop

    # Workflow support

    def workflow(self, name: str, description: str = "") -> Workflow:
        """Create a new workflow.

        Args:
            name: Workflow name
            description: Optional description

        Returns:
            Workflow instance
        """
        return Workflow(name, description)

    # Scheduling support

    def schedule(
        self,
        task,
        every: str = "day",
        at: Optional[str] = None,
        interval: int = 1,
    ):
        """Schedule a task.

        Args:
            task: Function to schedule
            every: 'day', 'hour', 'minute', 'monday', etc.
            at: Time for daily tasks (HH:MM)
            interval: Interval for minute/hour tasks

        Returns:
            Scheduled job
        """
        if every == "day" and at:
            return self.scheduler.daily(at, task)
        elif every == "hour":
            return self.scheduler.hourly(task)
        elif every == "minute":
            return self.scheduler.minutes(interval, task)
        else:
            return self.scheduler.every(interval).do(task)

    def run(self):
        """Start the scheduler and run indefinitely."""
        self.logger.info("Starting RPA scheduler")
        self.scheduler.run_continuously()

        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.scheduler.stop()
            self.logger.info("RPA stopped")

    def run_once(self):
        """Run all pending scheduled tasks once."""
        self.scheduler.run_pending()

    # Cleanup

    def close(self):
        """Clean up resources."""
        if self._scraper:
            self._scraper.close()
        if self._database:
            self._database.close()
        self.scheduler.stop()
        self.logger.info("RPA closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience exports
__all__ = [
    "RPA",
    "Config",
    "Scheduler",
    "Workflow",
    "WorkflowStep",
    "SpreadsheetModule",
    "FileModule",
    "PDFModule",
    "DocsModule",
    "EmailModule",
    "ScraperModule",
    "APIModule",
    "DatabaseModule",
    "DesktopModule",
    "get_logger",
]
