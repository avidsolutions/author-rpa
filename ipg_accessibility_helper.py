#!/usr/bin/env python3
"""
Universal Web Accessibility Helper for RPA Framework

This script provides accessibility assistance for navigating any website,
with a default configuration for https://ipg.illinois.gov/

Features:
- Text extraction and simplification for screen readers
- Text-to-speech output
- Keyboard navigation guidance
- Link and heading extraction
- Table data extraction
- Form field identification
- ARIA label reading
- High-contrast text output

Usage:
    python ipg_accessibility_helper.py [command] [options]

Commands:
    interactive     - Run interactive accessibility menu
    read            - Read page content
    links           - Extract all links
    headings        - Extract page structure (headings)
    forms           - Identify form fields
    tables          - Extract table data
    navigate        - Step-by-step navigation guide
"""

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

# Add parent directory to path for RPA imports
sys.path.insert(0, str(Path(__file__).parent))

from rpa import RPA
from rpa.core.logger import LoggerMixin


@dataclass
class AccessibilityElement:
    """Represents an accessible element on the page."""
    element_type: str  # link, heading, button, input, etc.
    text: str
    attributes: Dict[str, str] = field(default_factory=dict)
    level: int = 0  # For headings (h1=1, h2=2, etc.)
    role: str = ""  # ARIA role
    label: str = ""  # aria-label or associated label


@dataclass
class PageAccessibilityInfo:
    """Complete accessibility information for a page."""
    url: str
    title: str
    lang: str
    headings: List[AccessibilityElement] = field(default_factory=list)
    links: List[AccessibilityElement] = field(default_factory=list)
    buttons: List[AccessibilityElement] = field(default_factory=list)
    forms: List[Dict[str, Any]] = field(default_factory=list)
    images: List[AccessibilityElement] = field(default_factory=list)
    landmarks: List[AccessibilityElement] = field(default_factory=list)
    tables: List[List[List[str]]] = field(default_factory=list)
    main_content: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_heading_outline(self) -> str:
        """Generate a heading-based document outline."""
        lines = ["Document Outline:", ""]
        for h in self.headings:
            indent = "  " * (h.level - 1)
            lines.append(f"{indent}H{h.level}: {h.text}")
        return "\n".join(lines) if self.headings else "No headings found."

    def get_link_list(self) -> str:
        """Generate a numbered link list."""
        if not self.links:
            return "No links found."

        lines = [f"Links ({len(self.links)} found):", ""]
        for i, link in enumerate(self.links, 1):
            text = link.text or link.label or "[No text]"
            href = link.attributes.get("href", "")
            lines.append(f"  {i}. {text}")
            if href:
                lines.append(f"      URL: {href}")
        return "\n".join(lines)

    def get_form_summary(self) -> str:
        """Generate a form field summary."""
        if not self.forms:
            return "No forms found."

        lines = [f"Forms ({len(self.forms)} found):", ""]
        for i, form in enumerate(self.forms, 1):
            lines.append(f"Form {i}: {form.get('action', 'No action')}")
            for field in form.get("fields", []):
                label = field.get("label", field.get("name", "Unlabeled"))
                ftype = field.get("type", "text")
                required = " (required)" if field.get("required") else ""
                lines.append(f"    - {label} [{ftype}]{required}")
        return "\n".join(lines)

    def to_speech_text(self) -> str:
        """Convert to speech-friendly text."""
        lines = [
            f"Page: {self.title}",
            f"URL: {self.url}",
            "",
            self.get_heading_outline(),
            "",
            f"This page has {len(self.links)} links, {len(self.buttons)} buttons, and {len(self.forms)} forms.",
        ]

        if self.main_content:
            lines.append("")
            lines.append("Main content:")
            lines.append(self.main_content[:2000])

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return {
            "url": self.url,
            "title": self.title,
            "lang": self.lang,
            "headings": [{"level": h.level, "text": h.text} for h in self.headings],
            "links": [{"text": l.text, **l.attributes} for l in self.links],
            "buttons": [{"text": b.text, "label": b.label} for b in self.buttons],
            "forms": self.forms,
            "images": [{"alt": i.text, **i.attributes} for i in self.images],
            "landmarks": [{"role": l.role, "label": l.label} for l in self.landmarks],
            "table_count": len(self.tables),
            "main_content_length": len(self.main_content),
            "timestamp": self.timestamp,
        }


class WebAccessibilityHelper(LoggerMixin):
    """
    Universal web accessibility helper.

    Provides enhanced navigation and content extraction for users
    who need accessibility accommodations on any website.
    """

    # Default URL (can be overridden)
    DEFAULT_URL = "https://ipg.illinois.gov"

    def __init__(
        self,
        use_tts: bool = False,
        output_dir: str = "./accessibility_output",
        rate_limit: float = 1.0,
    ):
        """
        Initialize the accessibility helper.

        Args:
            use_tts: Enable text-to-speech output
            output_dir: Directory for saving extracted content
            rate_limit: Seconds between requests
        """
        self.rpa = RPA()
        self.use_tts = use_tts
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit = rate_limit
        self.current_url = None
        self.history: List[str] = []

        # TTS engine (optional)
        self._tts_engine = None
        if use_tts:
            self._init_tts()

        self.logger.info("Web Accessibility Helper initialized")

    def _init_tts(self) -> None:
        """Initialize text-to-speech engine if available."""
        try:
            import pyttsx3
            self._tts_engine = pyttsx3.init()
            self._tts_engine.setProperty('rate', 150)  # Slower for clarity
            self.logger.info("Text-to-speech enabled")
        except ImportError:
            self.logger.warning(
                "pyttsx3 not installed. Install with: pip install pyttsx3"
            )
            self.use_tts = False

    def speak(self, text: str) -> None:
        """Speak text aloud using TTS."""
        if self._tts_engine and self.use_tts:
            self._tts_engine.say(text)
            self._tts_engine.runAndWait()
        else:
            # Fallback: print to console with marker
            print(f"\n[SPEECH]: {text}\n")

    def announce(self, message: str) -> None:
        """Announce a message (both print and speak)."""
        print(message)
        if self.use_tts:
            self.speak(message)

    def _normalize_url(self, url: str) -> str:
        """Normalize and validate URL."""
        if not url:
            return self.DEFAULT_URL

        # Handle relative URLs
        if not url.startswith(("http://", "https://")):
            if self.current_url:
                return urljoin(self.current_url, url)
            elif url.startswith("/"):
                return f"{self.DEFAULT_URL}{url}"
            else:
                return f"https://{url}"

        return url

    def analyze_page(
        self,
        url: str,
        dynamic: bool = False,
        wait_for: Optional[str] = None,
    ) -> PageAccessibilityInfo:
        """
        Analyze a page for accessibility information.

        Args:
            url: URL to analyze
            dynamic: Use Selenium for JavaScript-heavy pages
            wait_for: CSS selector to wait for (dynamic mode only)

        Returns:
            PageAccessibilityInfo with all accessibility data
        """
        url = self._normalize_url(url)
        self.announce(f"Analyzing: {url}")

        try:
            if dynamic:
                soup = self.rpa.scraper.get_dynamic_soup(url, wait_for=wait_for or "body")
            else:
                soup = self.rpa.scraper.get_soup(url)

            self.current_url = url
            self.history.append(url)

            # Extract basic page info
            title = soup.title.get_text(strip=True) if soup.title else "No title"
            lang = soup.html.get("lang", "unknown") if soup.html else "unknown"

            info = PageAccessibilityInfo(url=url, title=title, lang=lang)

            # Extract headings
            for level in range(1, 7):
                for h in soup.find_all(f"h{level}"):
                    info.headings.append(AccessibilityElement(
                        element_type="heading",
                        text=h.get_text(strip=True),
                        level=level,
                        attributes={"id": h.get("id", "")},
                    ))

            # Extract links
            for a in soup.find_all("a", href=True):
                text = a.get_text(strip=True)
                aria_label = a.get("aria-label", "")
                title_attr = a.get("title", "")

                info.links.append(AccessibilityElement(
                    element_type="link",
                    text=text,
                    label=aria_label or title_attr,
                    attributes={
                        "href": a.get("href", ""),
                        "target": a.get("target", ""),
                    },
                ))

            # Extract buttons
            for btn in soup.find_all(["button", "input"]):
                if btn.name == "input" and btn.get("type") not in ["submit", "button", "reset"]:
                    continue

                text = btn.get_text(strip=True) if btn.name == "button" else btn.get("value", "")
                aria_label = btn.get("aria-label", "")

                info.buttons.append(AccessibilityElement(
                    element_type="button",
                    text=text,
                    label=aria_label,
                    role=btn.get("role", "button"),
                ))

            # Extract forms
            for form in soup.find_all("form"):
                form_data = {
                    "action": form.get("action", ""),
                    "method": form.get("method", "get"),
                    "id": form.get("id", ""),
                    "fields": [],
                }

                for inp in form.find_all(["input", "select", "textarea"]):
                    if inp.get("type") == "hidden":
                        continue

                    # Find associated label
                    label_text = ""
                    inp_id = inp.get("id")
                    if inp_id:
                        label = soup.find("label", {"for": inp_id})
                        if label:
                            label_text = label.get_text(strip=True)

                    form_data["fields"].append({
                        "name": inp.get("name", ""),
                        "type": inp.get("type", inp.name),
                        "id": inp_id or "",
                        "label": label_text or inp.get("aria-label", "") or inp.get("placeholder", ""),
                        "required": inp.has_attr("required"),
                    })

                info.forms.append(form_data)

            # Extract images with alt text
            for img in soup.find_all("img"):
                info.images.append(AccessibilityElement(
                    element_type="image",
                    text=img.get("alt", "[No alt text]"),
                    attributes={
                        "src": img.get("src", ""),
                        "width": img.get("width", ""),
                        "height": img.get("height", ""),
                    },
                ))

            # Extract ARIA landmarks
            landmark_roles = [
                "banner", "navigation", "main", "complementary",
                "contentinfo", "search", "form", "region"
            ]
            for role in landmark_roles:
                for el in soup.find_all(attrs={"role": role}):
                    info.landmarks.append(AccessibilityElement(
                        element_type="landmark",
                        text=el.get_text(strip=True)[:100],
                        role=role,
                        label=el.get("aria-label", ""),
                    ))

            # Also check semantic HTML5 elements
            landmark_map = {
                "header": "banner",
                "nav": "navigation",
                "main": "main",
                "aside": "complementary",
                "footer": "contentinfo",
            }
            for tag, role in landmark_map.items():
                for el in soup.find_all(tag):
                    if not el.get("role"):  # Don't duplicate
                        info.landmarks.append(AccessibilityElement(
                            element_type="landmark",
                            text="",
                            role=role,
                            label=el.get("aria-label", ""),
                        ))

            # Extract tables
            for table in soup.find_all("table"):
                table_data = []
                for tr in table.find_all("tr"):
                    row = [cell.get_text(strip=True) for cell in tr.find_all(["td", "th"])]
                    if row:
                        table_data.append(row)
                if table_data:
                    info.tables.append(table_data)

            # Extract main content
            main_selectors = ["main", "[role='main']", "#content", ".content", "article", "#main"]
            for sel in main_selectors:
                main_el = soup.select_one(sel)
                if main_el:
                    info.main_content = main_el.get_text(separator=" ", strip=True)
                    break
            else:
                # Fallback: get body text, excluding scripts/styles
                for script in soup(["script", "style", "nav", "header", "footer"]):
                    script.decompose()
                info.main_content = soup.get_text(separator=" ", strip=True)

            # Truncate main content
            info.main_content = info.main_content[:10000]

            self.announce(
                f"Page analyzed: {len(info.headings)} headings, {len(info.links)} links, "
                f"{len(info.forms)} forms, {len(info.tables)} tables"
            )

            return info

        except Exception as e:
            self.logger.error(f"Error analyzing page: {e}")
            return PageAccessibilityInfo(
                url=url,
                title="Error",
                lang="unknown",
                main_content=f"Failed to analyze page: {str(e)}",
            )

    def read_content(
        self,
        url: str,
        selector: Optional[str] = None,
        dynamic: bool = False,
    ) -> str:
        """
        Read and simplify page content.

        Args:
            url: URL to read
            selector: CSS selector to focus on specific content
            dynamic: Use Selenium for JavaScript pages

        Returns:
            Simplified, readable text content
        """
        url = self._normalize_url(url)
        self.announce(f"Reading: {url}")

        try:
            if dynamic:
                soup = self.rpa.scraper.get_dynamic_soup(url)
            else:
                soup = self.rpa.scraper.get_soup(url)

            if selector:
                elements = soup.select(selector)
                content = "\n\n".join(el.get_text(separator=" ", strip=True) for el in elements)
            else:
                # Remove non-content elements
                for el in soup(["script", "style", "nav", "iframe", "noscript"]):
                    el.decompose()

                # Try to find main content
                main = soup.select_one("main, [role='main'], #content, article")
                if main:
                    content = main.get_text(separator="\n", strip=True)
                else:
                    content = soup.get_text(separator="\n", strip=True)

            # Clean up whitespace
            content = re.sub(r'\n\s*\n', '\n\n', content)
            content = re.sub(r' +', ' ', content)

            if self.use_tts:
                self.speak(content[:3000])  # Limit TTS to first 3000 chars

            return content

        except Exception as e:
            error_msg = f"Error reading page: {str(e)}"
            self.logger.error(error_msg)
            return error_msg

    def list_links(self, url: str, filter_text: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Extract all links from a page.

        Args:
            url: URL to analyze
            filter_text: Optional text filter for links

        Returns:
            List of link dictionaries
        """
        info = self.analyze_page(url)

        links = []
        for link in info.links:
            text = link.text or link.label or "[No text]"

            if filter_text and filter_text.lower() not in text.lower():
                continue

            links.append({
                "text": text,
                "url": link.attributes.get("href", ""),
            })

        return links

    def list_headings(self, url: str) -> List[Dict[str, Any]]:
        """
        Extract heading structure from a page.

        Args:
            url: URL to analyze

        Returns:
            List of heading dictionaries
        """
        info = self.analyze_page(url)

        return [
            {"level": h.level, "text": h.text}
            for h in info.headings
        ]

    def describe_forms(self, url: str) -> List[Dict[str, Any]]:
        """
        Describe all forms on a page.

        Args:
            url: URL to analyze

        Returns:
            List of form descriptions
        """
        info = self.analyze_page(url)
        return info.forms

    def extract_tables(self, url: str) -> List[List[List[str]]]:
        """
        Extract all tables from a page.

        Args:
            url: URL to analyze

        Returns:
            List of tables (each table is a list of rows)
        """
        info = self.analyze_page(url)
        return info.tables

    def navigate_by_number(self, link_number: int) -> Optional[str]:
        """
        Navigate to a link by its number in the list.

        Args:
            link_number: 1-based index of link to navigate to

        Returns:
            URL navigated to, or None if invalid
        """
        if not self.current_url:
            self.announce("No page loaded. Please analyze a page first.")
            return None

        info = self.analyze_page(self.current_url)

        if link_number < 1 or link_number > len(info.links):
            self.announce(f"Invalid link number. Choose between 1 and {len(info.links)}.")
            return None

        link = info.links[link_number - 1]
        href = link.attributes.get("href", "")

        if not href:
            self.announce("This link has no URL.")
            return None

        new_url = self._normalize_url(href)
        self.announce(f"Navigating to: {link.text or link.label}")

        return new_url

    def keyboard_help(self) -> str:
        """Get keyboard navigation help text."""
        return """
Keyboard Navigation Guide (works on most websites):

General Navigation:
  Tab           Move to next interactive element
  Shift+Tab     Move to previous interactive element
  Enter         Activate buttons and links
  Space         Toggle checkboxes, activate buttons
  Escape        Close dialogs, cancel actions
  Arrow Keys    Navigate within menus and widgets

Page Navigation:
  Home          Go to top of page
  End           Go to bottom of page
  Page Up/Down  Scroll by viewport
  Ctrl+Home     Go to start of document
  Ctrl+End      Go to end of document

Screen Reader Shortcuts (NVDA/JAWS):
  H / Shift+H   Next/Previous heading
  1-6           Jump to heading level 1-6
  K / Shift+K   Next/Previous link
  F / Shift+F   Next/Previous form field
  T / Shift+T   Next/Previous table
  B / Shift+B   Next/Previous button
  D / Shift+D   Next/Previous landmark
  M / Shift+M   Next/Previous frame

This Helper Commands:
  read [url]         Read page content
  links [url]        List all links (numbered)
  headings [url]     Show document structure
  forms [url]        Describe form fields
  tables [url]       Extract table data
  go [number]        Navigate to link by number
  back               Go to previous page
  help               Show this help
"""

    def save_results(self, data: Any, filename: str, as_json: bool = True) -> str:
        """
        Save results to file.

        Args:
            data: Data to save
            filename: Output filename (without extension)
            as_json: Save as JSON (True) or text (False)

        Returns:
            Path to saved file
        """
        if as_json:
            output_path = self.output_dir / f"{filename}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                if hasattr(data, "to_dict"):
                    json.dump(data.to_dict(), f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            output_path = self.output_dir / f"{filename}.txt"
            with open(output_path, "w", encoding="utf-8") as f:
                if hasattr(data, "to_speech_text"):
                    f.write(data.to_speech_text())
                else:
                    f.write(str(data))

        self.logger.info(f"Saved to {output_path}")
        return str(output_path)

    def interactive_menu(self, start_url: Optional[str] = None) -> None:
        """
        Run an interactive accessibility session.

        Args:
            start_url: Optional starting URL
        """
        self.announce("Welcome to the Web Accessibility Helper")
        url = start_url or self.DEFAULT_URL

        while True:
            print("\n" + "=" * 60)
            print("Web Accessibility Helper")
            print(f"Current URL: {self.current_url or 'None'}")
            print("=" * 60)
            print("Commands:")
            print("  1. Analyze page      - Full accessibility analysis")
            print("  2. Read content      - Read simplified text")
            print("  3. List links        - Show numbered links")
            print("  4. List headings     - Show document structure")
            print("  5. Describe forms    - Show form fields")
            print("  6. Extract tables    - Get table data")
            print("  7. Go to link        - Navigate by number")
            print("  8. Enter URL         - Go to new URL")
            print("  9. Keyboard help     - Navigation tips")
            print("  0. Exit")
            print("=" * 60)

            try:
                choice = input("\nEnter command (0-9) or URL: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                break

            if choice == "0":
                self.announce("Goodbye!")
                break

            elif choice == "1":
                url_input = input(f"URL [{url}]: ").strip() or url
                info = self.analyze_page(url_input)
                url = info.url
                print("\n" + info.to_speech_text())
                self.save_results(info, "analysis")

            elif choice == "2":
                url_input = input(f"URL [{url}]: ").strip() or url
                selector = input("CSS selector (optional): ").strip() or None
                content = self.read_content(url_input, selector=selector)
                print("\n" + content[:5000])

            elif choice == "3":
                url_input = input(f"URL [{url}]: ").strip() or url
                filter_text = input("Filter by text (optional): ").strip() or None
                links = self.list_links(url_input, filter_text=filter_text)
                print(f"\nLinks ({len(links)} found):")
                for i, link in enumerate(links[:50], 1):
                    print(f"  {i:3}. {link['text'][:60]}")
                    print(f"       {link['url']}")

            elif choice == "4":
                url_input = input(f"URL [{url}]: ").strip() or url
                headings = self.list_headings(url_input)
                print("\nDocument Structure:")
                for h in headings:
                    indent = "  " * (h["level"] - 1)
                    print(f"{indent}H{h['level']}: {h['text']}")

            elif choice == "5":
                url_input = input(f"URL [{url}]: ").strip() or url
                forms = self.describe_forms(url_input)
                print(f"\nForms ({len(forms)} found):")
                for i, form in enumerate(forms, 1):
                    print(f"\nForm {i}:")
                    print(f"  Action: {form.get('action', 'None')}")
                    print(f"  Method: {form.get('method', 'GET')}")
                    print("  Fields:")
                    for field in form.get("fields", []):
                        req = " *" if field.get("required") else ""
                        print(f"    - {field.get('label', 'Unlabeled')} [{field.get('type', 'text')}]{req}")

            elif choice == "6":
                url_input = input(f"URL [{url}]: ").strip() or url
                tables = self.extract_tables(url_input)
                print(f"\nTables ({len(tables)} found):")
                for i, table in enumerate(tables, 1):
                    print(f"\nTable {i} ({len(table)} rows):")
                    for row in table[:10]:  # Show first 10 rows
                        print("  | " + " | ".join(cell[:30] for cell in row) + " |")
                    if len(table) > 10:
                        print(f"  ... and {len(table) - 10} more rows")

            elif choice == "7":
                if not self.current_url:
                    print("No page analyzed yet. Analyze a page first (option 1).")
                    continue
                try:
                    num = int(input("Enter link number: "))
                    new_url = self.navigate_by_number(num)
                    if new_url:
                        url = new_url
                        info = self.analyze_page(url)
                        print("\n" + info.to_speech_text())
                except ValueError:
                    print("Please enter a valid number.")

            elif choice == "8":
                url_input = input("Enter URL: ").strip()
                if url_input:
                    url = self._normalize_url(url_input)
                    info = self.analyze_page(url)
                    print("\n" + info.to_speech_text())

            elif choice == "9":
                print(self.keyboard_help())

            elif choice.startswith(("http://", "https://", "www.")):
                url = self._normalize_url(choice)
                info = self.analyze_page(url)
                print("\n" + info.to_speech_text())

            else:
                print("Invalid command. Enter 0-9 or a URL.")

    def close(self) -> None:
        """Clean up resources."""
        self.rpa.close()
        self.logger.info("Web Accessibility Helper closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Universal Web Accessibility Helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s interactive
  %(prog)s interactive --url https://example.com
  %(prog)s read https://example.com
  %(prog)s links https://example.com --filter "contact"
  %(prog)s headings https://example.com
  %(prog)s forms https://example.com
  %(prog)s tables https://example.com --output data.json
        """,
    )

    parser.add_argument(
        "command",
        choices=["interactive", "read", "links", "headings", "forms", "tables", "analyze", "help"],
        nargs="?",
        default="interactive",
        help="Command to run (default: interactive)",
    )

    parser.add_argument(
        "url",
        nargs="?",
        help="URL to analyze",
    )

    parser.add_argument(
        "--selector", "-s",
        help="CSS selector for content extraction",
    )

    parser.add_argument(
        "--filter", "-f",
        help="Filter results by text",
    )

    parser.add_argument(
        "--output", "-o",
        help="Output file path",
    )

    parser.add_argument(
        "--tts",
        action="store_true",
        help="Enable text-to-speech output",
    )

    parser.add_argument(
        "--dynamic",
        action="store_true",
        help="Use Selenium for JavaScript-rendered pages",
    )

    parser.add_argument(
        "--output-dir",
        default="./accessibility_output",
        help="Directory for output files",
    )

    args = parser.parse_args()

    with WebAccessibilityHelper(use_tts=args.tts, output_dir=args.output_dir) as helper:

        if args.command == "interactive":
            helper.interactive_menu(start_url=args.url)

        elif args.command == "read":
            url = args.url or helper.DEFAULT_URL
            content = helper.read_content(url, selector=args.selector, dynamic=args.dynamic)
            print(content)

        elif args.command == "links":
            url = args.url or helper.DEFAULT_URL
            links = helper.list_links(url, filter_text=args.filter)
            for i, link in enumerate(links, 1):
                print(f"{i:3}. {link['text']}")
                print(f"     {link['url']}")
            if args.output:
                helper.save_results(links, Path(args.output).stem)

        elif args.command == "headings":
            url = args.url or helper.DEFAULT_URL
            headings = helper.list_headings(url)
            for h in headings:
                indent = "  " * (h["level"] - 1)
                print(f"{indent}H{h['level']}: {h['text']}")
            if args.output:
                helper.save_results(headings, Path(args.output).stem)

        elif args.command == "forms":
            url = args.url or helper.DEFAULT_URL
            forms = helper.describe_forms(url)
            for i, form in enumerate(forms, 1):
                print(f"\nForm {i}: {form.get('action', 'No action')}")
                for field in form.get("fields", []):
                    print(f"  - {field.get('label', 'Unlabeled')} [{field.get('type')}]")
            if args.output:
                helper.save_results(forms, Path(args.output).stem)

        elif args.command == "tables":
            url = args.url or helper.DEFAULT_URL
            tables = helper.extract_tables(url)
            for i, table in enumerate(tables, 1):
                print(f"\nTable {i} ({len(table)} rows):")
                for row in table[:5]:
                    print("  " + " | ".join(row))
            if args.output:
                helper.save_results(tables, Path(args.output).stem)

        elif args.command == "analyze":
            url = args.url or helper.DEFAULT_URL
            info = helper.analyze_page(url, dynamic=args.dynamic)
            print(info.to_speech_text())
            if args.output:
                helper.save_results(info, Path(args.output).stem)

        elif args.command == "help":
            print(helper.keyboard_help())
            parser.print_help()


if __name__ == "__main__":
    main()
