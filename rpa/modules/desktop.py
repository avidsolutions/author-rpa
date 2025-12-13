"""Desktop automation module for RPA framework."""

import time
from pathlib import Path
from typing import List, Optional, Tuple, Union

import pyautogui
from PIL import Image

from ..core.logger import LoggerMixin


# Configure pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


class DesktopModule(LoggerMixin):
    """Handle desktop GUI automation."""

    def __init__(self, failsafe: bool = True, pause: float = 0.1):
        pyautogui.FAILSAFE = failsafe
        pyautogui.PAUSE = pause

    # Mouse operations

    def click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        clicks: int = 1,
        button: str = "left",
    ) -> None:
        """Click at coordinates or current position.

        Args:
            x: X coordinate (None = current)
            y: Y coordinate (None = current)
            clicks: Number of clicks
            button: 'left', 'right', or 'middle'
        """
        if x is not None and y is not None:
            pyautogui.click(x, y, clicks=clicks, button=button)
            self.logger.debug(f"Clicked at ({x}, {y})")
        else:
            pyautogui.click(clicks=clicks, button=button)
            self.logger.debug("Clicked at current position")

    def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """Double-click at coordinates."""
        self.click(x, y, clicks=2)

    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """Right-click at coordinates."""
        self.click(x, y, button="right")

    def move_to(self, x: int, y: int, duration: float = 0.25) -> None:
        """Move mouse to coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            duration: Movement duration in seconds
        """
        pyautogui.moveTo(x, y, duration=duration)

    def drag_to(
        self,
        x: int,
        y: int,
        duration: float = 0.5,
        button: str = "left",
    ) -> None:
        """Drag to coordinates."""
        pyautogui.dragTo(x, y, duration=duration, button=button)
        self.logger.debug(f"Dragged to ({x}, {y})")

    def drag(
        self,
        x_offset: int,
        y_offset: int,
        duration: float = 0.5,
    ) -> None:
        """Drag by offset from current position."""
        pyautogui.drag(x_offset, y_offset, duration=duration)

    def scroll(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """Scroll the mouse wheel.

        Args:
            clicks: Positive = up, negative = down
            x, y: Optional position to scroll at
        """
        pyautogui.scroll(clicks, x, y)

    def get_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        return pyautogui.position()

    # Keyboard operations

    def type_text(
        self,
        text: str,
        interval: float = 0.0,
    ) -> None:
        """Type text character by character.

        Args:
            text: Text to type
            interval: Delay between keystrokes
        """
        pyautogui.typewrite(text, interval=interval)
        self.logger.debug(f"Typed: {text[:50]}...")

    def write(self, text: str) -> None:
        """Type text (handles special characters better on some systems)."""
        pyautogui.write(text)

    def press(self, key: str) -> None:
        """Press a key.

        Args:
            key: Key name (e.g., 'enter', 'tab', 'escape', 'f1')
        """
        pyautogui.press(key)
        self.logger.debug(f"Pressed: {key}")

    def hotkey(self, *keys: str) -> None:
        """Press a keyboard shortcut.

        Args:
            *keys: Keys to press together (e.g., 'ctrl', 'c')
        """
        pyautogui.hotkey(*keys)
        self.logger.debug(f"Hotkey: {'+'.join(keys)}")

    def key_down(self, key: str) -> None:
        """Hold a key down."""
        pyautogui.keyDown(key)

    def key_up(self, key: str) -> None:
        """Release a key."""
        pyautogui.keyUp(key)

    # Screen operations

    def screenshot(
        self,
        output_path: Optional[str] = None,
        region: Optional[Tuple[int, int, int, int]] = None,
    ) -> Union[str, Image.Image]:
        """Take a screenshot.

        Args:
            output_path: Path to save screenshot (None = return image)
            region: (x, y, width, height) to capture

        Returns:
            Path if saved, Image object otherwise
        """
        img = pyautogui.screenshot(region=region)

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path)
            self.logger.info(f"Screenshot saved: {output_path}")
            return output_path

        return img

    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen dimensions."""
        return pyautogui.size()

    def locate_on_screen(
        self,
        image_path: str,
        confidence: float = 0.9,
        grayscale: bool = False,
    ) -> Optional[Tuple[int, int, int, int]]:
        """Find an image on screen.

        Args:
            image_path: Path to image to find
            confidence: Match confidence (0-1)
            grayscale: Use grayscale matching

        Returns:
            (x, y, width, height) or None if not found
        """
        try:
            location = pyautogui.locateOnScreen(
                image_path,
                confidence=confidence,
                grayscale=grayscale,
            )
            if location:
                self.logger.debug(f"Found image at {location}")
            return location
        except Exception as e:
            self.logger.debug(f"Image not found: {e}")
            return None

    def wait_for_image(
        self,
        image_path: str,
        timeout: float = 10.0,
        confidence: float = 0.9,
    ) -> Optional[Tuple[int, int, int, int]]:
        """Wait for an image to appear on screen.

        Args:
            image_path: Path to image
            timeout: Maximum wait time
            confidence: Match confidence

        Returns:
            Location or None if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            location = self.locate_on_screen(image_path, confidence)
            if location:
                return location
            time.sleep(0.5)

        self.logger.warning(f"Timeout waiting for image: {image_path}")
        return None

    def click_image(
        self,
        image_path: str,
        confidence: float = 0.9,
        timeout: float = 10.0,
    ) -> bool:
        """Find and click on an image.

        Args:
            image_path: Path to image
            confidence: Match confidence
            timeout: Wait timeout

        Returns:
            True if clicked, False if not found
        """
        location = self.wait_for_image(image_path, timeout, confidence)

        if location:
            center = pyautogui.center(location)
            self.click(center.x, center.y)
            self.logger.info(f"Clicked on image: {image_path}")
            return True

        return False

    # Window operations (basic - platform dependent)

    def get_active_window(self) -> Optional[str]:
        """Get the title of the active window."""
        try:
            window = pyautogui.getActiveWindow()
            return window.title if window else None
        except Exception:
            return None

    def get_all_windows(self) -> List[str]:
        """Get titles of all windows."""
        try:
            return [w.title for w in pyautogui.getAllWindows() if w.title]
        except Exception:
            return []

    # Utility methods

    def wait(self, seconds: float) -> None:
        """Wait for specified seconds."""
        time.sleep(seconds)

    def alert(self, message: str, title: str = "Alert") -> None:
        """Show an alert dialog."""
        pyautogui.alert(message, title)

    def confirm(self, message: str, title: str = "Confirm") -> bool:
        """Show a confirmation dialog.

        Returns:
            True if OK clicked, False if Cancel
        """
        result = pyautogui.confirm(message, title)
        return result == "OK"

    def prompt(
        self,
        message: str,
        title: str = "Input",
        default: str = "",
    ) -> Optional[str]:
        """Show a text input dialog.

        Returns:
            User input or None if cancelled
        """
        return pyautogui.prompt(message, title, default)

    def password(self, message: str, title: str = "Password") -> Optional[str]:
        """Show a password input dialog."""
        return pyautogui.password(message, title)

    # OCR support (requires pytesseract)

    def read_text_from_screen(
        self,
        region: Optional[Tuple[int, int, int, int]] = None,
    ) -> str:
        """Read text from screen using OCR.

        Args:
            region: (x, y, width, height) to read from

        Returns:
            Extracted text
        """
        try:
            import pytesseract

            img = pyautogui.screenshot(region=region)
            text = pytesseract.image_to_string(img)
            self.logger.debug(f"OCR extracted: {text[:100]}...")
            return text.strip()
        except ImportError:
            self.logger.error("pytesseract not installed")
            raise

    def read_text_from_image(self, image_path: str) -> str:
        """Read text from an image file using OCR."""
        try:
            import pytesseract

            text = pytesseract.image_to_string(Image.open(image_path))
            return text.strip()
        except ImportError:
            self.logger.error("pytesseract not installed")
            raise

    # Macro recording/playback helpers

    def record_position(self) -> Tuple[int, int]:
        """Record current mouse position."""
        pos = self.get_position()
        self.logger.info(f"Recorded position: {pos}")
        return pos

    def execute_sequence(
        self,
        actions: List[dict],
        delay: float = 0.5,
    ) -> None:
        """Execute a sequence of actions.

        Args:
            actions: List of action dicts with 'type' and params
            delay: Delay between actions

        Action types:
            - click: {type: 'click', x: int, y: int}
            - type: {type: 'type', text: str}
            - press: {type: 'press', key: str}
            - hotkey: {type: 'hotkey', keys: [str]}
            - wait: {type: 'wait', seconds: float}
        """
        for action in actions:
            action_type = action.get("type")

            if action_type == "click":
                self.click(action.get("x"), action.get("y"))
            elif action_type == "type":
                self.type_text(action.get("text", ""))
            elif action_type == "press":
                self.press(action.get("key", ""))
            elif action_type == "hotkey":
                self.hotkey(*action.get("keys", []))
            elif action_type == "wait":
                self.wait(action.get("seconds", 1))
            elif action_type == "move":
                self.move_to(action.get("x", 0), action.get("y", 0))

            time.sleep(delay)

        self.logger.info(f"Executed {len(actions)} actions")
