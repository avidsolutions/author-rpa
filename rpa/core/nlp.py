"""Natural Language Processing interface for RPA framework.

Allows users to control RPA operations using natural language commands
without writing any code.
"""

import os
import re
import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .logger import LoggerMixin


class IntentType(Enum):
    """Types of user intents."""
    # File Operations
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    COPY_FILE = "copy_file"
    MOVE_FILE = "move_file"
    DELETE_FILE = "delete_file"
    LIST_FILES = "list_files"

    # Spreadsheet Operations
    READ_SPREADSHEET = "read_spreadsheet"
    WRITE_SPREADSHEET = "write_spreadsheet"
    FILTER_DATA = "filter_data"

    # Document Operations
    CREATE_DOCUMENT = "create_document"
    FILL_FORM = "fill_form"
    CREATE_PDF = "create_pdf"
    EXTRACT_PDF = "extract_pdf"

    # Web Operations
    FETCH_URL = "fetch_url"
    SCRAPE_PAGE = "scrape_page"
    API_CALL = "api_call"
    DOWNLOAD = "download"

    # Database Operations
    QUERY_DATABASE = "query_database"

    # Email Operations
    SEND_EMAIL = "send_email"

    # Workflow Operations
    RUN_WORKFLOW = "run_workflow"
    CREATE_WORKFLOW = "create_workflow"

    # Help & Info
    HELP = "help"
    STATUS = "status"
    UNKNOWN = "unknown"


@dataclass
class ParsedIntent:
    """Represents a parsed user intent."""
    intent: IntentType
    confidence: float
    entities: Dict[str, Any]
    raw_text: str
    suggested_action: Optional[str] = None


class NaturalLanguageProcessor(LoggerMixin):
    """Process natural language commands for RPA operations.

    This class provides two modes:
    1. Rule-based parsing (no API key required)
    2. LLM-powered parsing (requires OpenAI or Anthropic API key)
    """

    def __init__(self, use_llm: bool = True):
        """Initialize the NLP processor.

        Args:
            use_llm: Whether to use LLM for parsing (falls back to rules if no API key)
        """
        self.use_llm = use_llm
        self._llm_client = None
        self._api_key = None

        # Try to load API keys from environment
        self._openai_key = os.getenv("OPENAI_API_KEY")
        self._anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        # Intent patterns for rule-based parsing
        self._intent_patterns = self._build_intent_patterns()

    def _build_intent_patterns(self) -> Dict[IntentType, List[re.Pattern]]:
        """Build regex patterns for intent detection."""
        patterns = {
            IntentType.READ_FILE: [
                re.compile(r"read\s+(?:the\s+)?(?:file\s+)?(.+)", re.I),
                re.compile(r"open\s+(?:the\s+)?(?:file\s+)?(.+)", re.I),
                re.compile(r"show\s+(?:me\s+)?(?:the\s+)?(?:contents?\s+of\s+)?(.+)", re.I),
                re.compile(r"what(?:'s| is)\s+in\s+(.+)", re.I),
            ],
            IntentType.WRITE_FILE: [
                re.compile(r"write\s+['\"](.+?)['\"]\s+to\s+(.+)", re.I),
                re.compile(r"save\s+(?:to\s+)?(.+)", re.I),
                re.compile(r"create\s+(?:a\s+)?(?:new\s+)?file\s+(?:called\s+)?(.+)", re.I),
            ],
            IntentType.COPY_FILE: [
                re.compile(r"copy\s+(.+?)\s+to\s+(.+)", re.I),
                re.compile(r"duplicate\s+(.+)", re.I),
            ],
            IntentType.MOVE_FILE: [
                re.compile(r"move\s+(.+?)\s+to\s+(.+)", re.I),
                re.compile(r"rename\s+(.+?)\s+to\s+(.+)", re.I),
            ],
            IntentType.DELETE_FILE: [
                re.compile(r"delete\s+(?:the\s+)?(?:file\s+)?(.+)", re.I),
                re.compile(r"remove\s+(?:the\s+)?(?:file\s+)?(.+)", re.I),
            ],
            IntentType.LIST_FILES: [
                re.compile(r"list\s+(?:all\s+)?files?\s+in\s+(.+)", re.I),
                re.compile(r"list\s+(?:all\s+)?files?$", re.I),
                re.compile(r"show\s+(?:me\s+)?(?:all\s+)?files?\s+in\s+(.+)", re.I),
                re.compile(r"show\s+(?:me\s+)?(?:all\s+)?files?$", re.I),
                re.compile(r"what\s+files?\s+(?:are\s+)?in\s+(.+)", re.I),
                re.compile(r"what\s+files?\s+(?:are\s+there|do\s+we\s+have)", re.I),
            ],
            IntentType.READ_SPREADSHEET: [
                re.compile(r"read\s+(?:the\s+)?(?:spreadsheet|csv|excel)\s+(.+)", re.I),
                re.compile(r"open\s+(?:the\s+)?(?:spreadsheet|csv|excel)\s+(.+)", re.I),
                re.compile(r"load\s+(?:data\s+from\s+)?(.+\.(?:csv|xlsx?))", re.I),
            ],
            IntentType.WRITE_SPREADSHEET: [
                re.compile(r"(?:save|write|export)\s+(?:to\s+)?(?:spreadsheet|csv|excel)\s+(.+)", re.I),
                re.compile(r"create\s+(?:a\s+)?(?:spreadsheet|csv|excel)\s+(.+)", re.I),
            ],
            IntentType.CREATE_DOCUMENT: [
                re.compile(r"create\s+(?:a\s+)?(?:word\s+)?(?:document|doc)\s+(?:called\s+)?(.+)?", re.I),
                re.compile(r"write\s+(?:a\s+)?(?:word\s+)?(?:document|doc)\s+(.+)?", re.I),
                re.compile(r"generate\s+(?:a\s+)?(?:word\s+)?(?:document|doc|report)\s+(.+)?", re.I),
            ],
            IntentType.FILL_FORM: [
                re.compile(r"fill\s+(?:out\s+)?(?:the\s+)?form\s+(.+)?", re.I),
                re.compile(r"complete\s+(?:the\s+)?form\s+(.+)?", re.I),
                re.compile(r"populate\s+(?:the\s+)?(?:form\s+)?(.+)?", re.I),
            ],
            IntentType.CREATE_PDF: [
                re.compile(r"create\s+(?:a\s+)?pdf\s+(.+)?", re.I),
                re.compile(r"generate\s+(?:a\s+)?pdf\s+(.+)?", re.I),
                re.compile(r"convert\s+(?:to\s+)?pdf\s+(.+)?", re.I),
            ],
            IntentType.EXTRACT_PDF: [
                re.compile(r"extract\s+(?:text\s+)?from\s+(?:pdf\s+)?(.+)", re.I),
                re.compile(r"read\s+(?:the\s+)?pdf\s+(.+)", re.I),
                re.compile(r"get\s+text\s+from\s+(.+\.pdf)", re.I),
            ],
            IntentType.FETCH_URL: [
                re.compile(r"fetch\s+(?:the\s+)?(?:url\s+)?(.+)", re.I),
                re.compile(r"get\s+(?:the\s+)?(?:page|content|data)\s+(?:from\s+)?(.+)", re.I),
                re.compile(r"download\s+(?:the\s+)?page\s+(.+)", re.I),
            ],
            IntentType.SCRAPE_PAGE: [
                re.compile(r"scrape\s+(?:the\s+)?(?:page\s+)?(.+)", re.I),
                re.compile(r"extract\s+(?:data\s+)?from\s+(?:website\s+)?(.+)", re.I),
            ],
            IntentType.API_CALL: [
                re.compile(r"(?:call|hit|request)\s+(?:the\s+)?api\s+(.+)?", re.I),
                re.compile(r"(?:make\s+)?(?:an?\s+)?api\s+(?:call|request)\s+(?:to\s+)?(.+)?", re.I),
            ],
            IntentType.SEND_EMAIL: [
                re.compile(r"send\s+(?:an?\s+)?email\s+(?:to\s+)?(.+)?", re.I),
                re.compile(r"email\s+(.+)", re.I),
            ],
            IntentType.QUERY_DATABASE: [
                re.compile(r"query\s+(?:the\s+)?(?:database|db)\s+(.+)?", re.I),
                re.compile(r"run\s+(?:a\s+)?(?:sql\s+)?query\s+(.+)?", re.I),
                re.compile(r"select\s+.+\s+from\s+.+", re.I),
            ],
            IntentType.RUN_WORKFLOW: [
                re.compile(r"run\s+(?:the\s+)?workflow\s+(.+)?", re.I),
                re.compile(r"execute\s+(?:the\s+)?workflow\s+(.+)?", re.I),
                re.compile(r"start\s+(?:the\s+)?(?:workflow|automation)\s+(.+)?", re.I),
            ],
            IntentType.HELP: [
                re.compile(r"^help$", re.I),
                re.compile(r"what\s+can\s+(?:you|i)\s+do", re.I),
                re.compile(r"how\s+(?:do\s+i|to)\s+(.+)", re.I),
                re.compile(r"show\s+(?:me\s+)?(?:the\s+)?(?:commands|help)", re.I),
            ],
            IntentType.STATUS: [
                re.compile(r"^status$", re.I),
                re.compile(r"what(?:'s| is)\s+(?:the\s+)?status", re.I),
                re.compile(r"show\s+(?:me\s+)?(?:the\s+)?status", re.I),
            ],
        }
        return patterns

    def parse(self, text: str) -> ParsedIntent:
        """Parse a natural language command.

        Args:
            text: The user's natural language input

        Returns:
            ParsedIntent with detected intent and entities
        """
        text = text.strip()

        # Try LLM parsing first if enabled and API key available
        if self.use_llm and (self._openai_key or self._anthropic_key):
            try:
                return self._parse_with_llm(text)
            except Exception as e:
                self.logger.warning(f"LLM parsing failed, falling back to rules: {e}")

        # Fall back to rule-based parsing
        return self._parse_with_rules(text)

    def _parse_with_rules(self, text: str) -> ParsedIntent:
        """Parse using rule-based patterns."""
        best_match = None
        best_confidence = 0.0
        best_entities = {}

        for intent, patterns in self._intent_patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    # Calculate confidence based on match coverage
                    coverage = len(match.group(0)) / len(text)
                    confidence = min(0.9, coverage + 0.3)

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = intent
                        best_entities = self._extract_entities(intent, match, text)

        if best_match:
            return ParsedIntent(
                intent=best_match,
                confidence=best_confidence,
                entities=best_entities,
                raw_text=text,
                suggested_action=self._get_suggested_action(best_match, best_entities),
            )

        return ParsedIntent(
            intent=IntentType.UNKNOWN,
            confidence=0.0,
            entities={},
            raw_text=text,
            suggested_action="I didn't understand that. Try 'help' for available commands.",
        )

    def _extract_entities(
        self, intent: IntentType, match: re.Match, text: str
    ) -> Dict[str, Any]:
        """Extract entities from a regex match."""
        entities = {}
        groups = match.groups()

        if intent in [IntentType.READ_FILE, IntentType.DELETE_FILE, IntentType.EXTRACT_PDF]:
            if groups and groups[0]:
                entities["path"] = groups[0].strip().strip("'\"")

        elif intent == IntentType.WRITE_FILE:
            if len(groups) >= 2:
                entities["content"] = groups[0]
                entities["path"] = groups[1].strip().strip("'\"")

        elif intent in [IntentType.COPY_FILE, IntentType.MOVE_FILE]:
            if len(groups) >= 2:
                entities["source"] = groups[0].strip().strip("'\"")
                entities["destination"] = groups[1].strip().strip("'\"")

        elif intent == IntentType.LIST_FILES:
            if groups and groups[0]:
                entities["path"] = groups[0].strip().strip("'\"")
            else:
                entities["path"] = "."

        elif intent in [IntentType.READ_SPREADSHEET, IntentType.WRITE_SPREADSHEET]:
            if groups and groups[0]:
                entities["path"] = groups[0].strip().strip("'\"")

        elif intent in [IntentType.CREATE_DOCUMENT, IntentType.CREATE_PDF]:
            if groups and groups[0]:
                entities["output_path"] = groups[0].strip().strip("'\"")

        elif intent == IntentType.FILL_FORM:
            if groups and groups[0]:
                entities["form_path"] = groups[0].strip().strip("'\"")

        elif intent in [IntentType.FETCH_URL, IntentType.SCRAPE_PAGE]:
            if groups and groups[0]:
                url = groups[0].strip().strip("'\"")
                if not url.startswith("http"):
                    url = "https://" + url
                entities["url"] = url

        elif intent == IntentType.SEND_EMAIL:
            if groups and groups[0]:
                entities["recipient"] = groups[0].strip()

        return entities

    def _get_suggested_action(
        self, intent: IntentType, entities: Dict[str, Any]
    ) -> str:
        """Generate a suggested action description."""
        suggestions = {
            IntentType.READ_FILE: f"Read file: {entities.get('path', '<path>')}",
            IntentType.WRITE_FILE: f"Write to: {entities.get('path', '<path>')}",
            IntentType.COPY_FILE: f"Copy {entities.get('source', '<source>')} to {entities.get('destination', '<dest>')}",
            IntentType.MOVE_FILE: f"Move {entities.get('source', '<source>')} to {entities.get('destination', '<dest>')}",
            IntentType.DELETE_FILE: f"Delete: {entities.get('path', '<path>')}",
            IntentType.LIST_FILES: f"List files in: {entities.get('path', '.')}",
            IntentType.READ_SPREADSHEET: f"Read spreadsheet: {entities.get('path', '<path>')}",
            IntentType.WRITE_SPREADSHEET: f"Write spreadsheet: {entities.get('path', '<path>')}",
            IntentType.CREATE_DOCUMENT: f"Create document: {entities.get('output_path', '<path>')}",
            IntentType.FILL_FORM: f"Fill form: {entities.get('form_path', '<path>')}",
            IntentType.CREATE_PDF: f"Create PDF: {entities.get('output_path', '<path>')}",
            IntentType.EXTRACT_PDF: f"Extract text from: {entities.get('path', '<path>')}",
            IntentType.FETCH_URL: f"Fetch: {entities.get('url', '<url>')}",
            IntentType.SCRAPE_PAGE: f"Scrape: {entities.get('url', '<url>')}",
            IntentType.SEND_EMAIL: f"Send email to: {entities.get('recipient', '<recipient>')}",
            IntentType.HELP: "Show available commands",
            IntentType.STATUS: "Show system status",
        }
        return suggestions.get(intent, "Execute action")

    def _parse_with_llm(self, text: str) -> ParsedIntent:
        """Parse using LLM for more sophisticated understanding."""
        if self._anthropic_key:
            return self._parse_with_anthropic(text)
        elif self._openai_key:
            return self._parse_with_openai(text)
        raise ValueError("No LLM API key available")

    def _parse_with_anthropic(self, text: str) -> ParsedIntent:
        """Parse using Anthropic Claude API."""
        import anthropic

        client = anthropic.Anthropic(api_key=self._anthropic_key)

        system_prompt = """You are an RPA (Robotic Process Automation) command parser.
Parse the user's natural language request and extract:
1. The intent (what action they want)
2. The entities (files, paths, URLs, data mentioned)

Respond ONLY with valid JSON in this format:
{
    "intent": "one of: read_file, write_file, copy_file, move_file, delete_file, list_files, read_spreadsheet, write_spreadsheet, create_document, fill_form, create_pdf, extract_pdf, fetch_url, scrape_page, api_call, send_email, query_database, run_workflow, help, status, unknown",
    "confidence": 0.0 to 1.0,
    "entities": {"key": "value"},
    "suggested_action": "human readable description of what will happen"
}"""

        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": text}],
        )

        result = json.loads(response.content[0].text)

        return ParsedIntent(
            intent=IntentType(result["intent"]),
            confidence=result["confidence"],
            entities=result.get("entities", {}),
            raw_text=text,
            suggested_action=result.get("suggested_action"),
        )

    def _parse_with_openai(self, text: str) -> ParsedIntent:
        """Parse using OpenAI API."""
        import openai

        client = openai.OpenAI(api_key=self._openai_key)

        system_prompt = """You are an RPA (Robotic Process Automation) command parser.
Parse the user's natural language request and extract:
1. The intent (what action they want)
2. The entities (files, paths, URLs, data mentioned)

Respond ONLY with valid JSON in this format:
{
    "intent": "one of: read_file, write_file, copy_file, move_file, delete_file, list_files, read_spreadsheet, write_spreadsheet, create_document, fill_form, create_pdf, extract_pdf, fetch_url, scrape_page, api_call, send_email, query_database, run_workflow, help, status, unknown",
    "confidence": 0.0 to 1.0,
    "entities": {"key": "value"},
    "suggested_action": "human readable description of what will happen"
}"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            max_tokens=500,
        )

        result = json.loads(response.choices[0].message.content)

        return ParsedIntent(
            intent=IntentType(result["intent"]),
            confidence=result["confidence"],
            entities=result.get("entities", {}),
            raw_text=text,
            suggested_action=result.get("suggested_action"),
        )


class NaturalLanguageInterface(LoggerMixin):
    """High-level natural language interface for RPA operations.

    Provides a conversational interface that translates natural language
    commands into RPA actions.
    """

    def __init__(self):
        self.nlp = NaturalLanguageProcessor()
        self._rpa = None
        self.history: List[Dict[str, Any]] = []

    @property
    def rpa(self):
        """Lazy-load RPA instance."""
        if self._rpa is None:
            from rpa import RPA
            self._rpa = RPA()
        return self._rpa

    def process(self, command: str) -> Dict[str, Any]:
        """Process a natural language command and execute the corresponding action.

        Args:
            command: Natural language command from user

        Returns:
            Dict with execution results
        """
        # Parse the command
        parsed = self.nlp.parse(command)

        self.logger.info(f"Parsed intent: {parsed.intent.value} (confidence: {parsed.confidence:.2f})")

        # Record in history
        self.history.append({
            "command": command,
            "intent": parsed.intent.value,
            "confidence": parsed.confidence,
        })

        # Execute based on intent
        try:
            result = self._execute_intent(parsed)
            return {
                "success": True,
                "intent": parsed.intent.value,
                "action": parsed.suggested_action,
                "result": result,
            }
        except Exception as e:
            self.logger.error(f"Execution failed: {e}")
            return {
                "success": False,
                "intent": parsed.intent.value,
                "action": parsed.suggested_action,
                "error": str(e),
            }

    def _execute_intent(self, parsed: ParsedIntent) -> Any:
        """Execute the parsed intent."""
        intent = parsed.intent
        entities = parsed.entities

        # File Operations
        if intent == IntentType.READ_FILE:
            path = entities.get("path")
            if not path:
                return "Please specify a file path. Example: 'read file report.txt'"
            return self.rpa.files.read_text(path)

        elif intent == IntentType.WRITE_FILE:
            path = entities.get("path")
            content = entities.get("content", "")
            if not path:
                return "Please specify a file path. Example: 'write \"Hello\" to greeting.txt'"
            return self.rpa.files.write_text(path, content)

        elif intent == IntentType.COPY_FILE:
            source = entities.get("source")
            dest = entities.get("destination")
            if not source or not dest:
                return "Please specify source and destination. Example: 'copy file.txt to backup/file.txt'"
            return self.rpa.files.copy(source, dest)

        elif intent == IntentType.MOVE_FILE:
            source = entities.get("source")
            dest = entities.get("destination")
            if not source or not dest:
                return "Please specify source and destination. Example: 'move old.txt to new.txt'"
            return self.rpa.files.move(source, dest)

        elif intent == IntentType.DELETE_FILE:
            path = entities.get("path")
            if not path:
                return "Please specify a file path. Example: 'delete temp.txt'"
            return self.rpa.files.delete(path)

        elif intent == IntentType.LIST_FILES:
            path = entities.get("path", ".")
            files = self.rpa.files.list_files(path)
            return [str(f) for f in files] if files else ["No files found"]

        # Spreadsheet Operations
        elif intent == IntentType.READ_SPREADSHEET:
            path = entities.get("path")
            if not path:
                return "Please specify a spreadsheet path. Example: 'read spreadsheet data.csv'"
            if path.endswith(".csv"):
                return self.rpa.spreadsheet.read_csv(path)
            else:
                return self.rpa.spreadsheet.read_excel(path)

        # Document Operations
        elif intent == IntentType.CREATE_DOCUMENT:
            path = entities.get("output_path", "document.docx")
            title = entities.get("title", "Untitled Document")
            content = entities.get("content", "")
            return self.rpa.docs.create_word(path, title=title, content=content)

        elif intent == IntentType.FILL_FORM:
            form_path = entities.get("form_path")
            if not form_path:
                return "Please specify a form path. Example: 'fill form application.docx'"
            return f"Form filling requires field mappings. Use the fill_form() method directly or provide more details."

        elif intent == IntentType.CREATE_PDF:
            path = entities.get("output_path", "document.pdf")
            content = entities.get("content", "")
            return self.rpa.pdf.create(path, content=content)

        elif intent == IntentType.EXTRACT_PDF:
            path = entities.get("path")
            if not path:
                return "Please specify a PDF path. Example: 'extract text from report.pdf'"
            return self.rpa.pdf.extract_text(path)

        # Web Operations
        elif intent == IntentType.FETCH_URL:
            url = entities.get("url")
            if not url:
                return "Please specify a URL. Example: 'fetch https://example.com'"
            return self.rpa.scraper.get(url)

        elif intent == IntentType.SCRAPE_PAGE:
            url = entities.get("url")
            if not url:
                return "Please specify a URL. Example: 'scrape https://example.com'"
            return self.rpa.scraper.get(url)

        # Help & Info
        elif intent == IntentType.HELP:
            return self._get_help_text()

        elif intent == IntentType.STATUS:
            return self._get_status()

        elif intent == IntentType.UNKNOWN:
            return parsed.suggested_action

        else:
            return f"Intent '{intent.value}' recognized but not yet implemented."

    def _get_help_text(self) -> str:
        """Return help text for available commands."""
        return """
AUTHO.R RPA - Natural Language Commands
========================================

FILE OPERATIONS:
  • "read file report.txt"
  • "show me the contents of data.json"
  • "list files in documents/"
  • "copy report.txt to backup/"
  • "move old.txt to archive/"
  • "delete temp.txt"

SPREADSHEET OPERATIONS:
  • "read spreadsheet sales.csv"
  • "open the excel file data.xlsx"

DOCUMENT OPERATIONS:
  • "create a word document called report.docx"
  • "fill form application.docx"
  • "create a pdf summary.pdf"
  • "extract text from document.pdf"

WEB OPERATIONS:
  • "fetch https://api.example.com/data"
  • "scrape the page example.com"
  • "download the file from https://..."

OTHER:
  • "help" - Show this help
  • "status" - Show system status

TIP: You can speak naturally. The system understands variations like:
  "what's in the file?", "show me files", "grab the webpage", etc.
"""

    def _get_status(self) -> str:
        """Return system status."""
        llm_status = "Available" if (self.nlp._openai_key or self.nlp._anthropic_key) else "Not configured (using rule-based parsing)"

        return f"""
AUTHO.R RPA Status
==================
RPA Framework: Active
NLP Engine: {'LLM-powered' if self.nlp.use_llm else 'Rule-based'}
LLM API: {llm_status}
Commands Processed: {len(self.history)}
"""


def create_cli():
    """Create and return the CLI interface."""
    return NaturalLanguageInterface()
