"""Workflow orchestration for RPA framework."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from enum import Enum

from ..core.logger import LoggerMixin


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""
    name: str
    action: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[Callable[[], bool]] = None
    on_error: Optional[Callable[[Exception], Any]] = None
    retry_count: int = 0
    retry_delay: float = 1.0
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def duration(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class Workflow(LoggerMixin):
    """Orchestrate multi-step automation workflows."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.steps: List[WorkflowStep] = []
        self.context: Dict[str, Any] = {}
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self._on_start: Optional[Callable] = None
        self._on_complete: Optional[Callable] = None
        self._on_error: Optional[Callable[[Exception, WorkflowStep], Any]] = None

    def add_step(
        self,
        name: str,
        action: Callable,
        *args,
        condition: Optional[Callable[[], bool]] = None,
        on_error: Optional[Callable[[Exception], Any]] = None,
        retry_count: int = 0,
        retry_delay: float = 1.0,
        **kwargs,
    ) -> "Workflow":
        """Add a step to the workflow.

        Args:
            name: Step name
            action: Function to execute
            *args: Arguments for the action
            condition: Optional condition function (step runs if True)
            on_error: Error handler for this step
            retry_count: Number of retries on failure
            retry_delay: Delay between retries
            **kwargs: Keyword arguments for the action

        Returns:
            Self for chaining
        """
        step = WorkflowStep(
            name=name,
            action=action,
            args=args,
            kwargs=kwargs,
            condition=condition,
            on_error=on_error,
            retry_count=retry_count,
            retry_delay=retry_delay,
        )
        self.steps.append(step)
        return self

    def step(
        self,
        name: str,
        condition: Optional[Callable[[], bool]] = None,
        retry_count: int = 0,
    ) -> Callable:
        """Decorator to add a step to the workflow.

        Usage:
            @workflow.step("Process data")
            def process():
                return data
        """
        def decorator(func: Callable) -> Callable:
            self.add_step(name, func, condition=condition, retry_count=retry_count)
            return func
        return decorator

    def on_start(self, callback: Callable) -> Callable:
        """Set callback for workflow start."""
        self._on_start = callback
        return callback

    def on_complete(self, callback: Callable) -> Callable:
        """Set callback for workflow completion."""
        self._on_complete = callback
        return callback

    def on_error(self, callback: Callable[[Exception, WorkflowStep], Any]) -> Callable:
        """Set callback for workflow errors."""
        self._on_error = callback
        return callback

    def run(self, **initial_context) -> Dict[str, Any]:
        """Execute the workflow.

        Args:
            **initial_context: Initial context variables

        Returns:
            Dict with workflow results
        """
        import time

        self.context.update(initial_context)
        self.started_at = datetime.now()
        self.logger.info(f"Starting workflow: {self.name}")

        if self._on_start:
            self._on_start()

        results = {}
        failed = False

        for step in self.steps:
            # Check condition
            if step.condition and not step.condition():
                step.status = StepStatus.SKIPPED
                self.logger.info(f"Skipped step: {step.name} (condition not met)")
                continue

            step.status = StepStatus.RUNNING
            step.started_at = datetime.now()
            self.logger.info(f"Running step: {step.name}")

            attempts = 0
            max_attempts = step.retry_count + 1

            while attempts < max_attempts:
                try:
                    # Execute the step
                    result = step.action(*step.args, **step.kwargs)
                    step.result = result
                    step.status = StepStatus.COMPLETED
                    step.completed_at = datetime.now()

                    results[step.name] = result
                    self.context[f"step_{step.name}_result"] = result

                    self.logger.info(f"Completed step: {step.name} ({step.duration:.2f}s)")
                    break

                except Exception as e:
                    attempts += 1
                    step.error = e

                    if attempts < max_attempts:
                        self.logger.warning(
                            f"Step '{step.name}' failed, retrying ({attempts}/{max_attempts}): {e}"
                        )
                        time.sleep(step.retry_delay)
                    else:
                        step.status = StepStatus.FAILED
                        step.completed_at = datetime.now()

                        self.logger.error(f"Step '{step.name}' failed: {e}")

                        # Try step-level error handler
                        if step.on_error:
                            try:
                                step.on_error(e)
                            except Exception as handler_error:
                                self.logger.error(f"Error handler failed: {handler_error}")

                        # Try workflow-level error handler
                        if self._on_error:
                            try:
                                self._on_error(e, step)
                            except Exception as handler_error:
                                self.logger.error(f"Workflow error handler failed: {handler_error}")

                        failed = True
                        break

            if failed:
                break

        self.completed_at = datetime.now()
        duration = (self.completed_at - self.started_at).total_seconds()

        if not failed and self._on_complete:
            self._on_complete()

        status = "FAILED" if failed else "COMPLETED"
        self.logger.info(f"Workflow {status}: {self.name} ({duration:.2f}s)")

        return {
            "name": self.name,
            "status": status,
            "duration": duration,
            "steps": {
                s.name: {
                    "status": s.status.value,
                    "duration": s.duration,
                    "result": s.result,
                    "error": str(s.error) if s.error else None,
                }
                for s in self.steps
            },
            "results": results,
        }

    def dry_run(self) -> List[str]:
        """Preview workflow steps without executing.

        Returns:
            List of step names in execution order
        """
        return [step.name for step in self.steps]

    def reset(self) -> None:
        """Reset workflow state for re-execution."""
        for step in self.steps:
            step.status = StepStatus.PENDING
            step.result = None
            step.error = None
            step.started_at = None
            step.completed_at = None

        self.started_at = None
        self.completed_at = None
        self.context.clear()

    def get_step(self, name: str) -> Optional[WorkflowStep]:
        """Get a step by name."""
        for step in self.steps:
            if step.name == name:
                return step
        return None

    def remove_step(self, name: str) -> bool:
        """Remove a step by name."""
        for i, step in enumerate(self.steps):
            if step.name == name:
                self.steps.pop(i)
                return True
        return False

    def __repr__(self) -> str:
        return f"Workflow(name='{self.name}', steps={len(self.steps)})"
