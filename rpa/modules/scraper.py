"""Web scraping module for RPA framework."""

import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions

from ..core.logger import LoggerMixin


class ScraperModule(LoggerMixin):
    """Handle web scraping and data extraction."""

    def __init__(
        self,
        user_agent: Optional[str] = None,
        rate_limit: float = 1.0,
        timeout: int = 30,
    ):
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.rate_limit = rate_limit
        self.timeout = timeout
        self._last_request_time = 0
        self._session = requests.Session()
        self._driver: Optional[webdriver.Chrome] = None

    def _wait_for_rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request_time = time.time()

    def get(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """Make a GET request.

        Args:
            url: URL to fetch
            params: Query parameters
            headers: Additional headers

        Returns:
            Response object
        """
        self._wait_for_rate_limit()

        request_headers = {"User-Agent": self.user_agent}
        if headers:
            request_headers.update(headers)

        self.logger.info(f"GET {url}")
        response = self._session.get(
            url,
            params=params,
            headers=request_headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response

    def get_soup(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
    ) -> BeautifulSoup:
        """Fetch a page and return BeautifulSoup object.

        Args:
            url: URL to fetch
            params: Query parameters

        Returns:
            BeautifulSoup object
        """
        response = self.get(url, params)
        return BeautifulSoup(response.text, "lxml")

    def extract_text(
        self,
        url: str,
        selector: Optional[str] = None,
    ) -> str:
        """Extract text content from a page.

        Args:
            url: URL to fetch
            selector: CSS selector (default: body text)

        Returns:
            Extracted text
        """
        soup = self.get_soup(url)

        if selector:
            elements = soup.select(selector)
            text = " ".join(el.get_text(strip=True) for el in elements)
        else:
            text = soup.get_text(separator=" ", strip=True)

        self.logger.info(f"Extracted {len(text)} characters from {url}")
        return text

    def extract_links(
        self,
        url: str,
        selector: str = "a[href]",
        absolute: bool = True,
    ) -> List[str]:
        """Extract links from a page.

        Args:
            url: URL to fetch
            selector: CSS selector for links
            absolute: Convert to absolute URLs

        Returns:
            List of URLs
        """
        soup = self.get_soup(url)
        links = []

        for a in soup.select(selector):
            href = a.get("href")
            if href:
                if absolute:
                    href = urljoin(url, href)
                links.append(href)

        self.logger.info(f"Found {len(links)} links on {url}")
        return links

    def extract_table(
        self,
        url: str,
        table_selector: str = "table",
        index: int = 0,
    ) -> List[List[str]]:
        """Extract table data from a page.

        Args:
            url: URL to fetch
            table_selector: CSS selector for table
            index: Table index if multiple match

        Returns:
            List of rows, each row is a list of cell values
        """
        soup = self.get_soup(url)
        tables = soup.select(table_selector)

        if not tables or index >= len(tables):
            return []

        table = tables[index]
        rows = []

        for tr in table.find_all("tr"):
            cells = []
            for td in tr.find_all(["td", "th"]):
                cells.append(td.get_text(strip=True))
            if cells:
                rows.append(cells)

        self.logger.info(f"Extracted table with {len(rows)} rows")
        return rows

    def extract_elements(
        self,
        url: str,
        selector: str,
        attributes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Extract data from multiple elements.

        Args:
            url: URL to fetch
            selector: CSS selector
            attributes: List of attributes to extract

        Returns:
            List of dicts with text and attributes
        """
        soup = self.get_soup(url)
        elements = soup.select(selector)
        results = []

        for el in elements:
            data = {"text": el.get_text(strip=True)}

            if attributes:
                for attr in attributes:
                    data[attr] = el.get(attr)
            else:
                data["attrs"] = dict(el.attrs)

            results.append(data)

        self.logger.info(f"Extracted {len(results)} elements matching '{selector}'")
        return results

    # Selenium-based methods for dynamic pages

    def _get_driver(self) -> webdriver.Chrome:
        """Get or create Selenium WebDriver."""
        if self._driver is None:
            options = ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(f"--user-agent={self.user_agent}")

            self._driver = webdriver.Chrome(options=options)

        return self._driver

    def get_dynamic(
        self,
        url: str,
        wait_for: Optional[str] = None,
        wait_timeout: int = 10,
    ) -> str:
        """Fetch a page with JavaScript rendering.

        Args:
            url: URL to fetch
            wait_for: CSS selector to wait for
            wait_timeout: Timeout for wait

        Returns:
            Page HTML
        """
        self._wait_for_rate_limit()
        driver = self._get_driver()

        self.logger.info(f"GET (dynamic) {url}")
        driver.get(url)

        if wait_for:
            WebDriverWait(driver, wait_timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
            )

        return driver.page_source

    def get_dynamic_soup(
        self,
        url: str,
        wait_for: Optional[str] = None,
    ) -> BeautifulSoup:
        """Fetch dynamic page and return BeautifulSoup object."""
        html = self.get_dynamic(url, wait_for)
        return BeautifulSoup(html, "lxml")

    def click_and_wait(
        self,
        selector: str,
        wait_for: Optional[str] = None,
        timeout: int = 10,
    ) -> None:
        """Click an element and optionally wait.

        Args:
            selector: CSS selector to click
            wait_for: CSS selector to wait for after click
            timeout: Wait timeout
        """
        driver = self._get_driver()

        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        element.click()

        if wait_for:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
            )

    def fill_form(
        self,
        fields: Dict[str, str],
        submit_selector: Optional[str] = None,
    ) -> None:
        """Fill form fields.

        Args:
            fields: Dict of {selector: value}
            submit_selector: Optional submit button selector
        """
        driver = self._get_driver()

        for selector, value in fields.items():
            element = driver.find_element(By.CSS_SELECTOR, selector)
            element.clear()
            element.send_keys(value)

        if submit_selector:
            submit = driver.find_element(By.CSS_SELECTOR, submit_selector)
            submit.click()

    def screenshot(self, output_path: str) -> str:
        """Take a screenshot of current page.

        Args:
            output_path: Path to save screenshot

        Returns:
            Path to screenshot
        """
        driver = self._get_driver()
        driver.save_screenshot(output_path)
        self.logger.info(f"Screenshot saved: {output_path}")
        return output_path

    def close(self) -> None:
        """Close the Selenium driver."""
        if self._driver:
            self._driver.quit()
            self._driver = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def download_file(
        self,
        url: str,
        output_path: str,
    ) -> str:
        """Download a file.

        Args:
            url: File URL
            output_path: Path to save file

        Returns:
            Path to downloaded file
        """
        self._wait_for_rate_limit()

        response = self._session.get(
            url,
            headers={"User-Agent": self.user_agent},
            stream=True,
            timeout=self.timeout,
        )
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        self.logger.info(f"Downloaded {url} to {output_path}")
        return output_path

    def download_images(
        self,
        url: str,
        output_dir: str,
        selector: str = "img[src]",
    ) -> List[str]:
        """Download all images from a page.

        Args:
            url: Page URL
            output_dir: Directory to save images
            selector: CSS selector for images

        Returns:
            List of downloaded file paths
        """
        from pathlib import Path

        soup = self.get_soup(url)
        images = soup.select(selector)
        downloaded = []

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        for i, img in enumerate(images):
            src = img.get("src")
            if src:
                img_url = urljoin(url, src)
                ext = Path(urlparse(img_url).path).suffix or ".jpg"
                output_path = str(Path(output_dir) / f"image_{i}{ext}")

                try:
                    self.download_file(img_url, output_path)
                    downloaded.append(output_path)
                except Exception as e:
                    self.logger.warning(f"Failed to download {img_url}: {e}")

        return downloaded
