"""
Chrome WebDriver Manager for Selenium automation
"""
import logging
import os
import re
import subprocess
from typing import Optional

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
except ImportError as exc:
    raise ImportError(
        "Selenium dependencies not installed. Install with:\n"
        "    pip install selenium\n"
    ) from exc

# Try to import undetected_chromedriver, but make it optional
# It may fail on Python 3.12+ due to missing distutils
try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as exc:
    # Check if it's a distutils error
    if 'distutils' in str(exc).lower():
        UC_AVAILABLE = False
        uc = None
    else:
        UC_AVAILABLE = False
        uc = None


def get_chrome_version() -> Optional[int]:
    """Detect installed Chrome version"""
    try:
        # Try different paths for Chrome
        chrome_paths = [
            'google-chrome',
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            'chromium',
            'chromium-browser'
        ]
        
        for chrome_path in chrome_paths:
            try:
                result = subprocess.run(
                    [chrome_path, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Extract version number (e.g., "Google Chrome 142.0.7444.176")
                    match = re.search(r'(\d+)\.\d+\.\d+\.\d+', result.stdout)
                    if match:
                        return int(match.group(1))
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
    except Exception:
        pass
    return None


class ChromeDriverManager:
    """
    Manage Chrome WebDriver instances with support for headless mode
    and custom Chrome profiles.

    Args:
        headless: Run Chrome in headless mode (default: False)
        profile_path: Optional Chrome profile directory to reuse session
        logger: Optional logger instance
    """

    def __init__(
        self,
        headless: bool = False,
        profile_path: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.headless = headless
        self.profile_path = profile_path
        self.logger = logger or logging.getLogger(__name__)
        self._driver = None

    def get_driver(self):
        """Get or create a Chrome WebDriver instance"""
        if self._driver is not None:
            return self._driver

        self.logger.info("Initializing Chrome WebDriver...")

        # Create options - use uc.ChromeOptions if available, otherwise regular Options
        if UC_AVAILABLE and uc is not None:
            uc_options = uc.ChromeOptions()
        else:
            uc_options = None
        
        # Create regular Options for webdriver-manager (primary method)
        chrome_options = Options()

        # Headless mode
        if self.headless:
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--disable-gpu')
            if uc_options:
                uc_options.add_argument('--headless=new')
                uc_options.add_argument('--disable-gpu')

        # Custom profile path
        if self.profile_path and os.path.exists(self.profile_path):
            chrome_options.add_argument(f'--user-data-dir={self.profile_path}')
            if uc_options:
                uc_options.add_argument(f'--user-data-dir={self.profile_path}')
            self.logger.info(f"Using Chrome profile: {self.profile_path}")

        # Additional options for stability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--window-size=1920,1080')
        
        if uc_options:
            uc_options.add_argument('--no-sandbox')
            uc_options.add_argument('--disable-dev-shm-usage')
            uc_options.add_argument('--disable-blink-features=AutomationControlled')
            uc_options.add_argument('--window-size=1920,1080')

        # Performance optimizations - disable images and CSS for faster loading
        prefs = {
            'profile.managed_default_content_settings.images': 2,  # Disable images
            'profile.managed_default_content_settings.stylesheets': 2,  # Disable CSS
        }
        chrome_options.add_experimental_option('prefs', prefs)
        if uc_options:
            uc_options.add_experimental_option('prefs', prefs)

        # Disable unnecessary features for speed
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        
        if uc_options:
            uc_options.add_argument('--disable-extensions')
            uc_options.add_argument('--disable-plugins')
            uc_options.add_argument('--blink-settings=imagesEnabled=false')

        # User agent to avoid detection
        user_agent = (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
        chrome_options.add_argument(f'user-agent={user_agent}')
        if uc_options:
            uc_options.add_argument(f'user-agent={user_agent}')

        # Try webdriver-manager first (more reliable for version matching)
        try:
            from selenium.webdriver import Chrome
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager

            self.logger.info("Attempting to initialize Chrome with webdriver-manager...")
            service = Service(ChromeDriverManager().install())

            self._driver = Chrome(service=service, options=chrome_options)
            self.logger.info("Chrome WebDriver initialized successfully with webdriver-manager")
            self._disable_browser_cache()
        except Exception as e:
            self.logger.warning(f"webdriver-manager failed: {e}")
            # Fallback: use undetected-chromedriver if available
            if UC_AVAILABLE and uc is not None:
                self.logger.info("Trying fallback with undetected-chromedriver...")
                try:
                    # Detect Chrome version first
                    chrome_version = get_chrome_version()
                    if chrome_version:
                        self.logger.info(f"Detected Chrome version: {chrome_version}")
                    
                    version_to_use = chrome_version if chrome_version else None
                    if uc_options is None:
                        raise RuntimeError("undetected_chromedriver options not available")
                    self._driver = uc.Chrome(
                        options=uc_options,
                        use_subprocess=True,
                        version_main=version_to_use
                    )
                    self.logger.info(f"Chrome WebDriver initialized with undetected-chromedriver (version: {version_to_use or 'auto'})")
                    self._disable_browser_cache()
                except Exception as e2:
                    self.logger.error(f"Both methods failed. Last error: {e2}")
                    raise
            else:
                self.logger.error("undetected-chromedriver not available (distutils missing or import failed)")
                raise RuntimeError(
                    "Failed to initialize Chrome WebDriver. webdriver-manager failed and "
                    "undetected-chromedriver is not available. Please install setuptools: "
                    "pip install setuptools"
                )

        return self._driver

    def _disable_browser_cache(self):
        """Disable HTTP cache so page loads always get fresh data (avoids stale/wrong order in CI)."""
        if self._driver is None:
            return
        try:
            self._driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
            self.logger.info("Browser cache disabled (fresh page loads)")
        except Exception as e:
            self.logger.warning(f"Could not disable browser cache via CDP: {e}")

    def close(self):
        """Close the WebDriver instance"""
        if self._driver:
            try:
                self._driver.quit()
                self.logger.info("Chrome WebDriver closed")
            except Exception as e:
                self.logger.warning(f"Error closing Chrome WebDriver: {e}")
            finally:
                self._driver = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
