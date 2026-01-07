#!/usr/bin/env python3
"""
Autho.R Application Navigation Demo with Screen Recording

This script navigates through all features of the Autho.R RPA web application,
records the session, and generates a reusable navigation script.

Usage:
    python navigate_app_demo.py [options]

Options:
    --url           Base URL of the app (default: http://localhost:8080)
    --output        Output video file (default: app_demo.mp4)
    --fps           Frames per second (default: 15)
    --no-record     Skip screen recording
    --generate-only Generate script without running
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rpa import RPA
from rpa.core.logger import LoggerMixin


@dataclass
class NavigationAction:
    """Represents a single navigation action."""
    action_type: str  # click, type, press, scroll, wait, navigate
    description: str
    target: Optional[str] = None  # CSS selector or URL
    value: Optional[Any] = None  # Text to type, key to press, etc.
    coordinates: Optional[tuple] = None  # (x, y) for clicks
    timestamp: float = field(default_factory=time.time)
    screenshot: Optional[str] = None  # Path to screenshot

    def to_dict(self) -> Dict:
        return {
            "action_type": self.action_type,
            "description": self.description,
            "target": self.target,
            "value": self.value,
            "coordinates": self.coordinates,
            "timestamp": self.timestamp,
        }

    def to_selenium_code(self) -> str:
        """Convert action to Selenium Python code."""
        if self.action_type == "navigate":
            return f'driver.get("{self.value}")'
        elif self.action_type == "click" and self.target:
            return f'driver.find_element(By.CSS_SELECTOR, "{self.target}").click()'
        elif self.action_type == "type" and self.target:
            return f'driver.find_element(By.CSS_SELECTOR, "{self.target}").send_keys("{self.value}")'
        elif self.action_type == "wait":
            return f'time.sleep({self.value})'
        elif self.action_type == "scroll":
            return f'driver.execute_script("window.scrollBy(0, {self.value})")'
        return f'# {self.description}'

    def to_pyautogui_code(self) -> str:
        """Convert action to PyAutoGUI Python code."""
        if self.action_type == "click" and self.coordinates:
            return f'pyautogui.click({self.coordinates[0]}, {self.coordinates[1]})  # {self.description}'
        elif self.action_type == "type":
            return f'pyautogui.typewrite("{self.value}")  # {self.description}'
        elif self.action_type == "press":
            return f'pyautogui.press("{self.value}")  # {self.description}'
        elif self.action_type == "wait":
            return f'time.sleep({self.value})  # {self.description}'
        elif self.action_type == "scroll":
            return f'pyautogui.scroll({self.value})  # {self.description}'
        return f'# {self.description}'


class AppNavigator(LoggerMixin):
    """Navigates through the Autho.R web application and records actions."""

    # Application routes/pages
    PAGES = [
        {"name": "Dashboard", "path": "/", "description": "Main dashboard with module overview"},
        {"name": "Spreadsheet", "path": "/spreadsheet", "description": "Excel/CSV processing"},
        {"name": "PDF", "path": "/pdf", "description": "PDF operations"},
        {"name": "Documents", "path": "/docs", "description": "Word and Markdown creation"},
        {"name": "Web Scraper", "path": "/scraper", "description": "Website data extraction"},
        {"name": "API Client", "path": "/api-client", "description": "REST API requests"},
        {"name": "Database", "path": "/database", "description": "Database queries"},
        {"name": "Files", "path": "/files", "description": "File management"},
        {"name": "Desktop", "path": "/desktop", "description": "Desktop automation"},
        {"name": "Workflow", "path": "/workflow", "description": "Multi-step automations"},
    ]

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        output_dir: str = "./demo_output",
    ):
        self.base_url = base_url.rstrip("/")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.rpa = RPA()
        self.actions: List[NavigationAction] = []
        self.screenshots: List[str] = []

        self.logger.info(f"AppNavigator initialized for {base_url}")

    def record_action(
        self,
        action_type: str,
        description: str,
        target: Optional[str] = None,
        value: Optional[Any] = None,
        coordinates: Optional[tuple] = None,
    ) -> NavigationAction:
        """Record a navigation action."""
        action = NavigationAction(
            action_type=action_type,
            description=description,
            target=target,
            value=value,
            coordinates=coordinates,
        )
        self.actions.append(action)
        self.logger.info(f"Action: {description}")
        return action

    def take_screenshot(self, name: str) -> str:
        """Take a screenshot and save it."""
        filename = f"{len(self.screenshots):03d}_{name}.png"
        filepath = str(self.output_dir / filename)
        self.rpa.desktop.screenshot(filepath)
        self.screenshots.append(filepath)
        return filepath

    def navigate_to(self, path: str, description: str) -> None:
        """Navigate to a URL path using Selenium."""
        url = f"{self.base_url}{path}"
        self.record_action("navigate", description, value=url)
        self.rpa.scraper.get_dynamic(url, wait_for="body")
        time.sleep(1)  # Allow page to render

    def wait(self, seconds: float, reason: str = "waiting") -> None:
        """Wait and record the action."""
        self.record_action("wait", reason, value=seconds)
        time.sleep(seconds)

    def scroll_page(self, amount: int = 300) -> None:
        """Scroll the page."""
        self.record_action("scroll", f"Scroll down {amount}px", value=amount)
        # Using JavaScript scroll via Selenium
        driver = self.rpa.scraper._get_driver()
        driver.execute_script(f"window.scrollBy(0, {amount})")
        time.sleep(0.5)

    def click_element(self, selector: str, description: str) -> None:
        """Click an element by CSS selector."""
        self.record_action("click", description, target=selector)
        self.rpa.scraper.click_and_wait(selector)
        time.sleep(0.5)

    def type_text(self, selector: str, text: str, description: str) -> None:
        """Type text into an element."""
        self.record_action("type", description, target=selector, value=text)
        self.rpa.scraper.fill_form({selector: text})
        time.sleep(0.3)

    def run_full_navigation(self, with_interactions: bool = True) -> List[NavigationAction]:
        """
        Navigate through all pages of the application.

        Args:
            with_interactions: Perform interactions on each page (forms, buttons)

        Returns:
            List of recorded actions
        """
        self.logger.info("Starting full application navigation")
        start_time = time.time()

        try:
            # Navigate through each page
            for page in self.PAGES:
                self.logger.info(f"Navigating to: {page['name']}")

                # Navigate to page
                self.navigate_to(page["path"], f"Navigate to {page['name']} page")
                self.take_screenshot(page["name"].lower().replace(" ", "_"))
                self.wait(1.5, f"Viewing {page['name']} page")

                # Perform page-specific interactions
                if with_interactions:
                    self._interact_with_page(page["name"])

                # Scroll to see full page
                self.scroll_page(300)
                self.wait(0.5, "Viewing more content")

            # Return to dashboard
            self.navigate_to("/", "Return to Dashboard")
            self.take_screenshot("final_dashboard")

        except Exception as e:
            self.logger.error(f"Navigation error: {e}")
            self.take_screenshot("error_state")

        elapsed = time.time() - start_time
        self.logger.info(f"Navigation completed in {elapsed:.1f} seconds")
        self.logger.info(f"Recorded {len(self.actions)} actions, {len(self.screenshots)} screenshots")

        return self.actions

    def _interact_with_page(self, page_name: str) -> None:
        """Perform interactions specific to each page."""
        try:
            if page_name == "Spreadsheet":
                # Highlight the file upload area
                self.scroll_page(100)
                self.wait(1, "Viewing spreadsheet upload area")

            elif page_name == "PDF":
                self.scroll_page(100)
                self.wait(1, "Viewing PDF tools")

            elif page_name == "Documents":
                # Try to interact with document creation form
                self.scroll_page(100)
                self.wait(1, "Viewing document creation options")

            elif page_name == "Web Scraper":
                # Enter a sample URL in the scraper
                try:
                    self.type_text(
                        "input[type='url'], input[name='url'], #url",
                        "https://example.com",
                        "Enter sample URL for scraping"
                    )
                except Exception:
                    pass
                self.wait(1, "Viewing scraper interface")

            elif page_name == "API Client":
                # Enter a sample API endpoint
                try:
                    self.type_text(
                        "input[type='url'], input[name='url'], #url",
                        "https://jsonplaceholder.typicode.com/posts/1",
                        "Enter sample API endpoint"
                    )
                except Exception:
                    pass
                self.wait(1, "Viewing API client interface")

            elif page_name == "Database":
                self.scroll_page(100)
                self.wait(1, "Viewing database connection options")

            elif page_name == "Files":
                self.scroll_page(100)
                self.wait(1, "Viewing file browser")

            elif page_name == "Desktop":
                self.scroll_page(100)
                self.wait(1, "Viewing desktop automation options")

            elif page_name == "Workflow":
                self.scroll_page(100)
                self.wait(1, "Viewing workflow builder")

            elif page_name == "Pricing":
                self.scroll_page(200)
                self.wait(1.5, "Viewing pricing plans")

        except Exception as e:
            self.logger.warning(f"Interaction error on {page_name}: {e}")

    def generate_script(self, output_file: str = "generated_navigation.py") -> str:
        """
        Generate a Python script from recorded actions.

        Args:
            output_file: Output filename

        Returns:
            Path to generated script
        """
        output_path = self.output_dir / output_file

        # Generate Selenium-based script
        selenium_script = self._generate_selenium_script()

        # Generate PyAutoGUI-based script
        pyautogui_script = self._generate_pyautogui_script()

        # Generate RPA framework script
        rpa_script = self._generate_rpa_script()

        # Combine into a single file with options
        full_script = f'''#!/usr/bin/env python3
"""
Auto-Generated Navigation Script for Autho.R Application

Generated: {datetime.now().isoformat()}
Total Actions: {len(self.actions)}
Pages Visited: {len(self.PAGES)}

This script can be run in three modes:
1. Selenium mode - Browser automation
2. PyAutoGUI mode - Desktop automation
3. RPA mode - Using the RPA framework

Usage:
    python {output_file} [--mode selenium|pyautogui|rpa] [--url URL]
"""

import argparse
import time
import sys
from pathlib import Path


# ============================================================
# SELENIUM MODE
# ============================================================

{selenium_script}


# ============================================================
# PYAUTOGUI MODE
# ============================================================

{pyautogui_script}


# ============================================================
# RPA FRAMEWORK MODE
# ============================================================

{rpa_script}


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Autho.R Navigation Script")
    parser.add_argument(
        "--mode",
        choices=["selenium", "pyautogui", "rpa"],
        default="rpa",
        help="Automation mode (default: rpa)"
    )
    parser.add_argument(
        "--url",
        default="{self.base_url}",
        help="Base URL of the application"
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="Record screen during navigation"
    )

    args = parser.parse_args()

    print(f"Running in {{args.mode}} mode")
    print(f"Target URL: {{args.url}}")

    if args.mode == "selenium":
        run_selenium_navigation(args.url)
    elif args.mode == "pyautogui":
        run_pyautogui_navigation()
    elif args.mode == "rpa":
        run_rpa_navigation(args.url, record=args.record)


if __name__ == "__main__":
    main()
'''

        with open(output_path, "w") as f:
            f.write(full_script)

        self.logger.info(f"Generated script: {output_path}")
        return str(output_path)

    def _generate_selenium_script(self) -> str:
        """Generate Selenium-based navigation code."""
        lines = [
            "def run_selenium_navigation(base_url):",
            '    """Navigate using Selenium WebDriver."""',
            "    from selenium import webdriver",
            "    from selenium.webdriver.common.by import By",
            "    from selenium.webdriver.chrome.options import Options",
            "    from selenium.webdriver.support.ui import WebDriverWait",
            "    from selenium.webdriver.support import expected_conditions as EC",
            "",
            "    options = Options()",
            "    options.add_argument('--start-maximized')",
            "    driver = webdriver.Chrome(options=options)",
            "",
            "    try:",
        ]

        for action in self.actions:
            code = action.to_selenium_code()
            if action.action_type == "navigate":
                # Replace hardcoded URL with base_url
                code = code.replace(self.base_url, '" + base_url + "')
                code = f'driver.get(base_url + "{action.value.replace(self.base_url, "")}")'
            lines.append(f"        {code}")
            lines.append(f"        print('Done: {action.description}')")

        lines.extend([
            "",
            "    finally:",
            "        input('Press Enter to close browser...')",
            "        driver.quit()",
        ])

        return "\n".join(lines)

    def _generate_pyautogui_script(self) -> str:
        """Generate PyAutoGUI-based navigation code."""
        lines = [
            "def run_pyautogui_navigation():",
            '    """Navigate using PyAutoGUI desktop automation."""',
            "    try:",
            "        import pyautogui",
            "    except ImportError:",
            "        print('PyAutoGUI not installed. Run: pip install pyautogui')",
            "        return",
            "",
            "    pyautogui.FAILSAFE = True",
            "    pyautogui.PAUSE = 0.5",
            "",
            "    print('PyAutoGUI navigation requires manual browser positioning.')",
            "    print('Please open the browser to the app and position it.')",
            "    input('Press Enter when ready...')",
            "",
        ]

        for action in self.actions:
            if action.action_type in ["click", "type", "press", "wait", "scroll"]:
                code = action.to_pyautogui_code()
                lines.append(f"    {code}")

        lines.append("    print('Navigation complete')")

        return "\n".join(lines)

    def _generate_rpa_script(self) -> str:
        """Generate RPA framework navigation code."""
        lines = [
            "def run_rpa_navigation(base_url, record=False):",
            '    """Navigate using the RPA framework."""',
            "    sys.path.insert(0, str(Path(__file__).parent))",
            "    from rpa import RPA",
            "",
            "    bot = RPA()",
            "    recorder = None",
            "",
            "    if record:",
            "        recorder = bot.desktop.start_recording('navigation_recording.mp4', fps=15)",
            "",
            "    try:",
        ]

        # Group navigation actions by page
        current_page = None
        for action in self.actions:
            if action.action_type == "navigate":
                path = action.value.replace(self.base_url, "")
                lines.append(f"        # Navigate to {action.description}")
                lines.append(f"        bot.scraper.get_dynamic(base_url + '{path}', wait_for='body')")
            elif action.action_type == "wait":
                lines.append(f"        time.sleep({action.value})  # {action.description}")
            elif action.action_type == "scroll":
                lines.append(f"        # {action.description}")
            elif action.action_type == "type" and action.target:
                lines.append(f"        bot.scraper.fill_form({{'{action.target}': '{action.value}'}})")

        lines.extend([
            "",
            "        print('Navigation complete')",
            "",
            "    finally:",
            "        if recorder:",
            "            stats = recorder.stop()",
            "            print(f'Recording saved: {stats}')",
            "        bot.close()",
        ])

        return "\n".join(lines)

    def save_actions_json(self) -> str:
        """Save recorded actions to JSON file."""
        output_path = self.output_dir / "navigation_actions.json"

        data = {
            "base_url": self.base_url,
            "generated": datetime.now().isoformat(),
            "total_actions": len(self.actions),
            "pages": [p["name"] for p in self.PAGES],
            "actions": [a.to_dict() for a in self.actions],
            "screenshots": self.screenshots,
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        self.logger.info(f"Actions saved to: {output_path}")
        return str(output_path)

    def close(self):
        """Clean up resources."""
        self.rpa.close()


def main():
    parser = argparse.ArgumentParser(
        description="Navigate Autho.R app and generate navigation script"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8080",
        help="Base URL of the application"
    )
    parser.add_argument(
        "--output",
        default="app_demo.mp4",
        help="Output video file"
    )
    parser.add_argument(
        "--output-dir",
        default="./demo_output",
        help="Output directory"
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=15,
        help="Recording frames per second"
    )
    parser.add_argument(
        "--no-record",
        action="store_true",
        help="Skip screen recording"
    )
    parser.add_argument(
        "--no-interact",
        action="store_true",
        help="Skip page interactions"
    )
    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Generate script from existing actions.json"
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    navigator = AppNavigator(base_url=args.url, output_dir=str(output_dir))

    try:
        if args.generate_only:
            # Load existing actions
            actions_file = output_dir / "navigation_actions.json"
            if actions_file.exists():
                print(f"Loading actions from {actions_file}")
                # Generate script only
                script_path = navigator.generate_script()
                print(f"Script generated: {script_path}")
            else:
                print(f"No actions file found at {actions_file}")
                print("Run without --generate-only first to record actions")
            return

        # Start screen recording if enabled
        recorder = None
        if not args.no_record:
            video_path = str(output_dir / args.output)
            print(f"Starting screen recording: {video_path}")
            recorder = navigator.rpa.desktop.start_recording(video_path, fps=args.fps)

        # Run navigation
        print(f"Navigating {args.url}...")
        print("=" * 60)

        actions = navigator.run_full_navigation(with_interactions=not args.no_interact)

        # Stop recording
        if recorder:
            stats = recorder.stop()
            print("=" * 60)
            print(f"Recording stats: {stats}")

        # Save actions to JSON
        json_path = navigator.save_actions_json()
        print(f"Actions saved: {json_path}")

        # Generate navigation script
        script_path = navigator.generate_script()
        print(f"Script generated: {script_path}")

        print("=" * 60)
        print("Demo complete!")
        print(f"  Video: {output_dir / args.output}")
        print(f"  Actions: {json_path}")
        print(f"  Script: {script_path}")
        print(f"  Screenshots: {len(navigator.screenshots)} images in {output_dir}")

    finally:
        navigator.close()


if __name__ == "__main__":
    main()
