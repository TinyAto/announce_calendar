import json
import logging
import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)

class ChromeAuthExtractor:
    def __init__(self, mattermost_url, debug_port=9222):
        self.mattermost_url = mattermost_url.rstrip("/")
        self.debug_port = debug_port
        self.driver = None

    def attach_to_chrome(self):
        options = Options()
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.debug_port}")
        self.driver = webdriver.Chrome(options=options)
        logger.info("Attached to Chrome with debug port %d", self.debug_port)

    def ensure_logged_in(self, timeout=120):
        self.driver.get(self.mattermost_url)
        start = time.time()
        while time.time() - start < timeout:
            try:
                token = self.extract_token()
                if token:
                    logger.info("Login confirmed")
                    return True
            except Exception:
                pass
            time.sleep(2)
        raise TimeoutError("Login timeout. Please log in to Mattermost in Chrome.")

    def extract_token(self):
        try:
            token = self.driver.execute_script(
                "return localStorage.getItem('MMTOKEN');"
            )
            if token:
                return token
        except Exception as e:
            logger.warning("Failed to extract MMTOKEN: %s", e)

        try:
            cookies = self.driver.get_cookies()
            for cookie in cookies:
                if cookie["name"] in ("MMAUTHTOKEN", "MATTERMOST_SESSION"):
                    return cookie["value"]
        except Exception as e:
            logger.warning("Failed to extract cookie: %s", e)

        return None

    def close(self):
        if self.driver:
            self.driver.quit()
