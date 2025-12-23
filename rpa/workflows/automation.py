"""Full automation workflow module for RPA framework.

Provides declarative workflow definitions for:
- Local file operations
- Web scraping and API calls
- Document generation and form filling
- Data transformations
- Email notifications
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime
from enum import Enum
import json
import time

from ..core.logger import LoggerMixin
from .base import Workflow, WorkflowStep, StepStatus


class StepType(Enum):
    """Types of automation steps."""
    # Local Operations
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    COPY_FILE = "copy_file"
    MOVE_FILE = "move_file"
    DELETE_FILE = "delete_file"
    LIST_FILES = "list_files"
    CREATE_DIRECTORY = "create_directory"

    # Spreadsheet Operations
    READ_CSV = "read_csv"
    WRITE_CSV = "write_csv"
    READ_EXCEL = "read_excel"
    WRITE_EXCEL = "write_excel"
    FILTER_DATA = "filter_data"
    TRANSFORM_DATA = "transform_data"

    # Web Operations
    HTTP_GET = "http_get"
    HTTP_POST = "http_post"
    SCRAPE_PAGE = "scrape_page"
    API_CALL = "api_call"
    DOWNLOAD_FILE = "download_file"

    # Document Operations
    CREATE_WORD = "create_word"
    FILL_FORM = "fill_form"
    CREATE_PDF = "create_pdf"
    MERGE_PDFS = "merge_pdfs"
    EXTRACT_PDF_TEXT = "extract_pdf_text"

    # Database Operations
    DB_QUERY = "db_query"
    DB_INSERT = "db_insert"
    DB_UPDATE = "db_update"

    # Communication
    SEND_EMAIL = "send_email"
    LOG_MESSAGE = "log_message"

    # Control Flow
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    WAIT = "wait"
    CUSTOM = "custom"


@dataclass
class AutomationStep:
    """A declarative automation step."""
    name: str
    step_type: StepType
    params: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[str] = None  # Expression to evaluate
    on_error: str = "fail"  # "fail", "skip", "retry"
    retry_count: int = 0
    retry_delay: float = 1.0
    save_result_as: Optional[str] = None  # Variable name to store result
    depends_on: List[str] = field(default_factory=list)


class AutomationWorkflow(LoggerMixin):
    """Declarative automation workflow with built-in step handlers.

    Example usage:
        workflow = AutomationWorkflow("Invoice Processing")

        workflow.add_steps([
            AutomationStep(
                name="read_invoices",
                step_type=StepType.READ_CSV,
                params={"path": "invoices.csv"},
                save_result_as="invoices"
            ),
            AutomationStep(
                name="fetch_rates",
                step_type=StepType.API_CALL,
                params={"url": "https://api.example.com/rates"},
                save_result_as="rates"
            ),
            AutomationStep(
                name="generate_report",
                step_type=StepType.CREATE_WORD,
                params={
                    "output_path": "report.docx",
                    "title": "Invoice Report",
                    "content": "{{invoices}}"
                }
            ),
        ])

        result = workflow.run()
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.steps: List[AutomationStep] = []
        self.context: Dict[str, Any] = {}
        self.results: Dict[str, Any] = {}
        self._rpa = None  # Lazy-loaded RPA instance

    @property
    def rpa(self):
        """Lazy-load RPA instance."""
        if self._rpa is None:
            from rpa import RPA
            self._rpa = RPA()
        return self._rpa

    def add_step(self, step: AutomationStep) -> "AutomationWorkflow":
        """Add a single step."""
        self.steps.append(step)
        return self

    def add_steps(self, steps: List[AutomationStep]) -> "AutomationWorkflow":
        """Add multiple steps."""
        self.steps.extend(steps)
        return self

    # =========================================================================
    # Fluent API for common operations
    # =========================================================================

    def read_file(
        self,
        name: str,
        path: str,
        save_as: Optional[str] = None,
    ) -> "AutomationWorkflow":
        """Add a read file step."""
        return self.add_step(AutomationStep(
            name=name,
            step_type=StepType.READ_FILE,
            params={"path": path},
            save_result_as=save_as or name,
        ))

    def write_file(
        self,
        name: str,
        path: str,
        content: str,
    ) -> "AutomationWorkflow":
        """Add a write file step."""
        return self.add_step(AutomationStep(
            name=name,
            step_type=StepType.WRITE_FILE,
            params={"path": path, "content": content},
        ))

    def read_csv(
        self,
        name: str,
        path: str,
        save_as: Optional[str] = None,
    ) -> "AutomationWorkflow":
        """Add a read CSV step."""
        return self.add_step(AutomationStep(
            name=name,
            step_type=StepType.READ_CSV,
            params={"path": path},
            save_result_as=save_as or name,
        ))

    def write_csv(
        self,
        name: str,
        path: str,
        data: Union[str, List[Dict]],
        headers: Optional[List[str]] = None,
    ) -> "AutomationWorkflow":
        """Add a write CSV step."""
        return self.add_step(AutomationStep(
            name=name,
            step_type=StepType.WRITE_CSV,
            params={"path": path, "data": data, "headers": headers},
        ))

    def http_get(
        self,
        name: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        save_as: Optional[str] = None,
    ) -> "AutomationWorkflow":
        """Add an HTTP GET step."""
        return self.add_step(AutomationStep(
            name=name,
            step_type=StepType.HTTP_GET,
            params={"url": url, "headers": headers or {}},
            save_result_as=save_as or name,
        ))

    def http_post(
        self,
        name: str,
        url: str,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None,
        save_as: Optional[str] = None,
    ) -> "AutomationWorkflow":
        """Add an HTTP POST step."""
        return self.add_step(AutomationStep(
            name=name,
            step_type=StepType.HTTP_POST,
            params={
                "url": url,
                "data": data,
                "json": json_data,
                "headers": headers or {},
            },
            save_result_as=save_as or name,
        ))

    def api_call(
        self,
        name: str,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        save_as: Optional[str] = None,
    ) -> "AutomationWorkflow":
        """Add an API call step."""
        return self.add_step(AutomationStep(
            name=name,
            step_type=StepType.API_CALL,
            params={
                "url": url,
                "method": method,
                "headers": headers or {},
                "params": params,
                "data": data,
            },
            save_result_as=save_as or name,
        ))

    def scrape_page(
        self,
        name: str,
        url: str,
        selectors: Dict[str, str],
        save_as: Optional[str] = None,
    ) -> "AutomationWorkflow":
        """Add a web scraping step."""
        return self.add_step(AutomationStep(
            name=name,
            step_type=StepType.SCRAPE_PAGE,
            params={"url": url, "selectors": selectors},
            save_result_as=save_as or name,
        ))

    def create_word(
        self,
        name: str,
        output_path: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
    ) -> "AutomationWorkflow":
        """Add a Word document creation step."""
        return self.add_step(AutomationStep(
            name=name,
            step_type=StepType.CREATE_WORD,
            params={
                "output_path": output_path,
                "title": title,
                "content": content,
            },
        ))

    def fill_form(
        self,
        name: str,
        template_path: str,
        output_path: str,
        field_mappings: List[Dict[str, Any]],
    ) -> "AutomationWorkflow":
        """Add a form filling step."""
        return self.add_step(AutomationStep(
            name=name,
            step_type=StepType.FILL_FORM,
            params={
                "template_path": template_path,
                "output_path": output_path,
                "field_mappings": field_mappings,
            },
        ))

    def create_pdf(
        self,
        name: str,
        output_path: str,
        content: str,
        title: Optional[str] = None,
    ) -> "AutomationWorkflow":
        """Add a PDF creation step."""
        return self.add_step(AutomationStep(
            name=name,
            step_type=StepType.CREATE_PDF,
            params={
                "output_path": output_path,
                "content": content,
                "title": title,
            },
        ))

    def db_query(
        self,
        name: str,
        connection_string: str,
        query: str,
        params: Optional[tuple] = None,
        save_as: Optional[str] = None,
    ) -> "AutomationWorkflow":
        """Add a database query step."""
        return self.add_step(AutomationStep(
            name=name,
            step_type=StepType.DB_QUERY,
            params={
                "connection_string": connection_string,
                "query": query,
                "params": params,
            },
            save_result_as=save_as or name,
        ))

    def send_email(
        self,
        name: str,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
    ) -> "AutomationWorkflow":
        """Add an email step."""
        return self.add_step(AutomationStep(
            name=name,
            step_type=StepType.SEND_EMAIL,
            params={
                "to": to,
                "subject": subject,
                "body": body,
                "attachments": attachments or [],
            },
        ))

    def transform_data(
        self,
        name: str,
        source_var: str,
        transform_fn: Callable[[Any], Any],
        save_as: Optional[str] = None,
    ) -> "AutomationWorkflow":
        """Add a data transformation step."""
        return self.add_step(AutomationStep(
            name=name,
            step_type=StepType.TRANSFORM_DATA,
            params={
                "source_var": source_var,
                "transform_fn": transform_fn,
            },
            save_result_as=save_as or name,
        ))

    def wait(self, name: str, seconds: float) -> "AutomationWorkflow":
        """Add a wait step."""
        return self.add_step(AutomationStep(
            name=name,
            step_type=StepType.WAIT,
            params={"seconds": seconds},
        ))

    def log(self, name: str, message: str) -> "AutomationWorkflow":
        """Add a log message step."""
        return self.add_step(AutomationStep(
            name=name,
            step_type=StepType.LOG_MESSAGE,
            params={"message": message},
        ))

    def custom(
        self,
        name: str,
        action: Callable,
        params: Optional[Dict] = None,
        save_as: Optional[str] = None,
    ) -> "AutomationWorkflow":
        """Add a custom function step."""
        return self.add_step(AutomationStep(
            name=name,
            step_type=StepType.CUSTOM,
            params={"action": action, **(params or {})},
            save_result_as=save_as,
        ))

    # =========================================================================
    # Step Execution Handlers
    # =========================================================================

    def _resolve_value(self, value: Any) -> Any:
        """Resolve template variables in values."""
        if isinstance(value, str):
            # Replace {{var}} with context values
            import re
            pattern = r'\{\{(\w+)\}\}'
            matches = re.findall(pattern, value)
            for var_name in matches:
                if var_name in self.context:
                    var_value = self.context[var_name]
                    if value == f"{{{{{var_name}}}}}":
                        # Entire value is a variable reference
                        return var_value
                    else:
                        # Partial replacement
                        value = value.replace(f"{{{{{var_name}}}}}", str(var_value))
            return value
        elif isinstance(value, dict):
            return {k: self._resolve_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_value(v) for v in value]
        return value

    def _execute_step(self, step: AutomationStep) -> Any:
        """Execute a single automation step."""
        params = self._resolve_value(step.params)
        step_type = step.step_type

        # Local File Operations
        if step_type == StepType.READ_FILE:
            return self.rpa.files.read_text(params["path"])

        elif step_type == StepType.WRITE_FILE:
            return self.rpa.files.write_text(params["path"], params["content"])

        elif step_type == StepType.COPY_FILE:
            return self.rpa.files.copy(params["source"], params["destination"])

        elif step_type == StepType.MOVE_FILE:
            return self.rpa.files.move(params["source"], params["destination"])

        elif step_type == StepType.DELETE_FILE:
            return self.rpa.files.delete(params["path"])

        elif step_type == StepType.LIST_FILES:
            return self.rpa.files.list_directory(
                params["path"],
                pattern=params.get("pattern", "*")
            )

        elif step_type == StepType.CREATE_DIRECTORY:
            return self.rpa.files.create_directory(params["path"])

        # Spreadsheet Operations
        elif step_type == StepType.READ_CSV:
            return self.rpa.spreadsheet.read_csv(params["path"])

        elif step_type == StepType.WRITE_CSV:
            data = params["data"]
            if isinstance(data, str):
                data = self.context.get(data, [])
            return self.rpa.spreadsheet.write_csv(
                params["path"],
                data,
                headers=params.get("headers")
            )

        elif step_type == StepType.READ_EXCEL:
            return self.rpa.spreadsheet.read_excel(
                params["path"],
                sheet_name=params.get("sheet_name")
            )

        elif step_type == StepType.WRITE_EXCEL:
            data = params["data"]
            if isinstance(data, str):
                data = self.context.get(data, [])
            return self.rpa.spreadsheet.write_excel(
                params["path"],
                data,
                sheet_name=params.get("sheet_name", "Sheet1")
            )

        elif step_type == StepType.FILTER_DATA:
            data = self.context.get(params["source_var"], [])
            filter_fn = params["filter_fn"]
            return [row for row in data if filter_fn(row)]

        elif step_type == StepType.TRANSFORM_DATA:
            data = self.context.get(params["source_var"])
            transform_fn = params["transform_fn"]
            return transform_fn(data)

        # Web Operations
        elif step_type == StepType.HTTP_GET:
            return self.rpa.scraper.get(
                params["url"],
                headers=params.get("headers")
            )

        elif step_type == StepType.HTTP_POST:
            import requests
            response = requests.post(
                params["url"],
                data=params.get("data"),
                json=params.get("json"),
                headers=params.get("headers", {}),
            )
            response.raise_for_status()
            try:
                return response.json()
            except:
                return response.text

        elif step_type == StepType.SCRAPE_PAGE:
            html = self.rpa.scraper.get(params["url"])
            return self.rpa.scraper.extract_elements(html, params["selectors"])

        elif step_type == StepType.API_CALL:
            return self.rpa.api.request(
                method=params.get("method", "GET"),
                url=params["url"],
                headers=params.get("headers"),
                params=params.get("params"),
                json_data=params.get("data"),
            )

        elif step_type == StepType.DOWNLOAD_FILE:
            return self.rpa.scraper.download(
                params["url"],
                params["output_path"]
            )

        # Document Operations
        elif step_type == StepType.CREATE_WORD:
            return self.rpa.docs.create_word(
                output_path=params["output_path"],
                title=params.get("title"),
                content=params.get("content"),
            )

        elif step_type == StepType.FILL_FORM:
            return self.rpa.docs.fill_form(
                doc_path=params["template_path"],
                output_path=params["output_path"],
                field_mappings=params["field_mappings"],
            )

        elif step_type == StepType.CREATE_PDF:
            return self.rpa.pdf.create(
                output_path=params["output_path"],
                content=params["content"],
                title=params.get("title"),
            )

        elif step_type == StepType.MERGE_PDFS:
            return self.rpa.pdf.merge(
                input_paths=params["input_paths"],
                output_path=params["output_path"],
            )

        elif step_type == StepType.EXTRACT_PDF_TEXT:
            return self.rpa.pdf.extract_text(params["path"])

        # Database Operations
        elif step_type == StepType.DB_QUERY:
            return self.rpa.database.query(
                connection_string=params["connection_string"],
                query=params["query"],
                params=params.get("params"),
            )

        elif step_type == StepType.DB_INSERT:
            return self.rpa.database.insert(
                connection_string=params["connection_string"],
                table=params["table"],
                data=params["data"],
            )

        elif step_type == StepType.DB_UPDATE:
            return self.rpa.database.update(
                connection_string=params["connection_string"],
                table=params["table"],
                data=params["data"],
                where=params["where"],
            )

        # Communication
        elif step_type == StepType.SEND_EMAIL:
            return self.rpa.email.send(
                to=params["to"],
                subject=params["subject"],
                body=params["body"],
                attachments=params.get("attachments"),
            )

        elif step_type == StepType.LOG_MESSAGE:
            message = params["message"]
            self.logger.info(f"[{step.name}] {message}")
            return message

        # Control Flow
        elif step_type == StepType.WAIT:
            time.sleep(params["seconds"])
            return params["seconds"]

        elif step_type == StepType.CUSTOM:
            action = params.pop("action")
            return action(**params, context=self.context)

        else:
            raise ValueError(f"Unknown step type: {step_type}")

    # =========================================================================
    # Workflow Execution
    # =========================================================================

    def run(self, **initial_context) -> Dict[str, Any]:
        """Execute the automation workflow.

        Args:
            **initial_context: Initial context variables

        Returns:
            Workflow execution results
        """
        self.context.update(initial_context)
        self.results.clear()

        started_at = datetime.now()
        self.logger.info(f"Starting automation workflow: {self.name}")

        step_results = []
        failed = False
        failed_step = None

        for step in self.steps:
            step_start = datetime.now()
            self.logger.info(f"Executing step: {step.name} ({step.step_type.value})")

            # Check condition
            if step.condition:
                try:
                    condition_result = eval(step.condition, {"context": self.context})
                    if not condition_result:
                        self.logger.info(f"Skipping step {step.name}: condition not met")
                        step_results.append({
                            "name": step.name,
                            "status": "skipped",
                            "reason": "condition not met",
                        })
                        continue
                except Exception as e:
                    self.logger.warning(f"Error evaluating condition: {e}")

            attempts = 0
            max_attempts = step.retry_count + 1
            step_error = None
            step_result = None

            while attempts < max_attempts:
                try:
                    step_result = self._execute_step(step)

                    # Save result if requested
                    if step.save_result_as:
                        self.context[step.save_result_as] = step_result
                        self.results[step.save_result_as] = step_result

                    step_duration = (datetime.now() - step_start).total_seconds()
                    self.logger.info(f"Completed step: {step.name} ({step_duration:.2f}s)")

                    step_results.append({
                        "name": step.name,
                        "status": "completed",
                        "duration": step_duration,
                        "result": str(step_result)[:200] if step_result else None,
                    })
                    break

                except Exception as e:
                    attempts += 1
                    step_error = e

                    if attempts < max_attempts:
                        self.logger.warning(
                            f"Step {step.name} failed, retrying ({attempts}/{max_attempts}): {e}"
                        )
                        time.sleep(step.retry_delay)
                    else:
                        if step.on_error == "skip":
                            self.logger.warning(f"Skipping failed step {step.name}: {e}")
                            step_results.append({
                                "name": step.name,
                                "status": "skipped",
                                "error": str(e),
                            })
                        else:
                            self.logger.error(f"Step {step.name} failed: {e}")
                            step_results.append({
                                "name": step.name,
                                "status": "failed",
                                "error": str(e),
                            })
                            failed = True
                            failed_step = step.name

            if failed and step.on_error == "fail":
                break

        completed_at = datetime.now()
        duration = (completed_at - started_at).total_seconds()
        status = "failed" if failed else "completed"

        self.logger.info(f"Workflow {status}: {self.name} ({duration:.2f}s)")

        return {
            "workflow": self.name,
            "status": status,
            "duration": duration,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "steps": step_results,
            "results": self.results,
            "failed_step": failed_step,
        }

    def dry_run(self) -> List[Dict[str, Any]]:
        """Preview workflow without executing."""
        return [
            {
                "name": step.name,
                "type": step.step_type.value,
                "params": step.params,
                "saves_as": step.save_result_as,
            }
            for step in self.steps
        ]

    def to_json(self) -> str:
        """Export workflow definition as JSON."""
        return json.dumps({
            "name": self.name,
            "description": self.description,
            "steps": [
                {
                    "name": step.name,
                    "type": step.step_type.value,
                    "params": {k: v for k, v in step.params.items() if not callable(v)},
                    "condition": step.condition,
                    "on_error": step.on_error,
                    "retry_count": step.retry_count,
                    "save_result_as": step.save_result_as,
                }
                for step in self.steps
            ],
        }, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "AutomationWorkflow":
        """Create workflow from JSON definition."""
        data = json.loads(json_str)
        workflow = cls(name=data["name"], description=data.get("description", ""))

        for step_data in data["steps"]:
            step = AutomationStep(
                name=step_data["name"],
                step_type=StepType(step_data["type"]),
                params=step_data.get("params", {}),
                condition=step_data.get("condition"),
                on_error=step_data.get("on_error", "fail"),
                retry_count=step_data.get("retry_count", 0),
                save_result_as=step_data.get("save_result_as"),
            )
            workflow.add_step(step)

        return workflow

    def __repr__(self) -> str:
        return f"AutomationWorkflow(name='{self.name}', steps={len(self.steps)})"
