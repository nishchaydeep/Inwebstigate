"""Web scraping module using Selenium."""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
import os
import glob
from config import Config
from logger import setup_logger

logger = setup_logger('scraper')


class WebScraper:
    """Web scraper using Selenium and BeautifulSoup."""
    
    def __init__(self):
        """Initialize the web scraper."""
        self.driver = None
        self._init_driver()
    
    def _find_chromedriver_binary(self, search_dir: str) -> Optional[str]:
        """
        Recursively search for the actual chromedriver binary.
        
        Args:
            search_dir: Directory to search in
            
        Returns:
            Path to chromedriver binary or None
        """
        logger.debug(f"Searching for chromedriver in: {search_dir}")
        
        # Pattern to match chromedriver executable (not text files)
        patterns = [
            os.path.join(search_dir, 'chromedriver'),
            os.path.join(search_dir, '**/chromedriver'),
            os.path.join(search_dir, 'chromedriver-mac-arm64/chromedriver'),
            os.path.join(search_dir, 'chromedriver-mac-x64/chromedriver'),
        ]
        
        for pattern in patterns:
            matches = glob.glob(pattern, recursive=True)
            for match in matches:
                # Skip if it's a text file (THIRD_PARTY_NOTICES, etc.)
                if os.path.isfile(match) and not match.endswith(('.txt', '.chromedriver', 'LICENSE')):
                    # Verify it's actually an executable binary
                    try:
                        with open(match, 'rb') as f:
                            header = f.read(4)
                            # Check for Mach-O magic number (macOS executable)
                            if header in [b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe', b'\xfe\xed\xfa\xcf', b'\xfe\xed\xfa\xce']:
                                logger.info(f"Found valid Mach-O executable: {match}")
                                return match
                    except Exception as e:
                        logger.debug(f"Error checking {match}: {e}")
                        continue
        
        return None
    
    def _init_driver(self):
        """Initialize the Chrome WebDriver."""
        logger.info("Initializing Chrome WebDriver...")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Add proxy if configured
        proxy_url = Config.get_proxy_url()
        if proxy_url:
            logger.info(f"Using proxy: {proxy_url}")
            chrome_options.add_argument(f'--proxy-server={proxy_url}')
        else:
            logger.info("No proxy configured")
        
        try:
            # Initialize driver with automatic ChromeDriver installation
            logger.info("Installing/locating ChromeDriver...")
            driver_path = ChromeDriverManager().install()
            logger.info(f"ChromeDriver path from manager: {driver_path}")
            
            # Fix for macOS ARM - ensure we get the actual chromedriver binary
            # ChromeDriverManager sometimes returns the wrong file (like THIRD_PARTY_NOTICES)
            if 'THIRD_PARTY' in driver_path or 'LICENSE' in driver_path or not driver_path.endswith('chromedriver'):
                logger.warning(f"⚠️  Invalid driver path detected: {driver_path}")
                logger.info("Searching for actual chromedriver binary...")
                
                # Search in the .wdm cache directory
                base_dir = os.path.dirname(driver_path)
                
                # Try to find the real binary
                real_driver = self._find_chromedriver_binary(base_dir)
                
                if not real_driver:
                    # Search parent directories
                    parent_dir = os.path.dirname(base_dir)
                    real_driver = self._find_chromedriver_binary(parent_dir)
                
                if not real_driver:
                    # Last resort: search the entire .wdm directory
                    wdm_root = os.path.expanduser('~/.wdm')
                    if os.path.exists(wdm_root):
                        logger.info(f"Searching entire .wdm cache: {wdm_root}")
                        real_driver = self._find_chromedriver_binary(wdm_root)
                
                if real_driver:
                    driver_path = real_driver
                    logger.info(f"✅ Found actual chromedriver binary: {driver_path}")
                else:
                    error_msg = "Could not find valid chromedriver binary in .wdm cache"
                    logger.error(error_msg)
                    logger.error("Try manually deleting ~/.wdm directory and running again")
                    raise FileNotFoundError(error_msg)
            
            # Verify it's a valid executable file
            if not os.path.isfile(driver_path):
                raise FileNotFoundError(f"ChromeDriver not found at: {driver_path}")
            
            # Make sure it's executable
            if not os.access(driver_path, os.X_OK):
                logger.info(f"Setting executable permissions: {driver_path}")
                os.chmod(driver_path, 0o755)
            
            logger.info(f"🚀 Using ChromeDriver: {driver_path}")
            service = Service(driver_path)
            logger.info("Creating Chrome WebDriver instance...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(Config.PAGE_LOAD_TIMEOUT)
            logger.info("✅ Chrome WebDriver initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Chrome WebDriver: {e}", exc_info=True)
            logger.error("💡 Try running: rm -rf ~/.wdm && pip install --upgrade webdriver-manager")
            raise
    
    def scrape_page(self, url: str) -> Dict[str, any]:
        """
        Scrape a web page and extract content and links.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dictionary containing HTML, text content, links, and metadata
        """
        logger.info(f"Scraping page: {url}")
        try:
            logger.debug("Loading page with Selenium...")
            self.driver.get(url)
            
            # Wait for page to load
            logger.debug("Waiting for page body to load...")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Give JavaScript time to render
            logger.debug("Waiting for JavaScript to render...")
            time.sleep(2)
            
            # Get page source
            logger.debug("Extracting page source...")
            html = self.driver.page_source
            logger.debug(f"Page source length: {len(html)} characters")
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract text content
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Clean up text
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = ' '.join(chunk for chunk in chunks if chunk)
            
            # Extract all links
            logger.debug("Extracting links...")
            links = self._extract_links(soup, url)
            logger.info(f"Found {len(links)} links")
            
            # Get page title
            title = soup.title.string if soup.title else "No title"
            logger.debug(f"Page title: {title}")
            
            # Get meta description
            meta_desc = ""
            meta_tag = soup.find("meta", attrs={"name": "description"})
            if meta_tag and meta_tag.get("content"):
                meta_desc = meta_tag.get("content")
            
            logger.info(f"Successfully scraped: {url}")
            return {
                "url": url,
                "title": title,
                "meta_description": meta_desc,
                "html": html,
                "text_content": text_content[:50000],  # Limit to 50k chars
                "links": links,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}", exc_info=True)
            return {
                "url": url,
                "title": "",
                "meta_description": "",
                "html": "",
                "text_content": "",
                "links": [],
                "success": False,
                "error": str(e)
            }
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        Extract all links from the page.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            
        Returns:
            List of dictionaries containing link information
        """
        links = []
        seen_urls = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Skip anchors, javascript, and mailto links
            if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                continue
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                from urllib.parse import urljoin
                href = urljoin(base_url, href)
            elif not href.startswith('http'):
                from urllib.parse import urljoin
                href = urljoin(base_url, href)
            
            # Avoid duplicates
            if href in seen_urls:
                continue
            
            seen_urls.add(href)
            
            # Get link text
            link_text = link.get_text(strip=True)
            if not link_text:
                link_text = href
            
            links.append({
                "url": href,
                "text": link_text[:200]  # Limit text length
            })
        
        return links
    
    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()

