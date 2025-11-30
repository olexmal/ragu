"""
Web Scraper Module
Crawls and extracts content from websites for embedding.
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from typing import List, Dict, Set, Optional, Any
from .utils import setup_logging

logger = setup_logging()

class WebScraper:
    """
    Scrapes content from websites, following links within the same domain.
    """
    
    def __init__(self, max_depth: int = 3, timeout: int = 10, delay: float = 1.0):
        """
        Initialize the web scraper.
        
        Args:
            max_depth: Maximum depth to crawl (0 = only start URL)
            timeout: Request timeout in seconds
            delay: Delay between requests in seconds (rate limiting)
        """
        self.max_depth = max_depth
        self.timeout = timeout
        self.delay = delay
        self.visited_urls: Set[str] = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Ragu-WebScraper/1.0 (Documentation Crawler)'
        })

    def scrape_url(self, start_url: str, same_domain_only: bool = True) -> List[Dict[str, Any]]:
        """
        Scrape content starting from a URL.
        
        Args:
            start_url: The starting URL
            same_domain_only: Whether to restrict crawling to the same domain
            
        Returns:
            List of dictionaries containing scraped page data
        """
        self.visited_urls.clear()
        results = []
        queue = [(start_url, 0)]  # (url, current_depth)
        
        # Validate start URL
        if not self._is_valid_url(start_url):
            logger.error(f"Invalid start URL: {start_url}")
            return []
            
        base_domain = urlparse(start_url).netloc
        
        while queue:
            current_url, depth = queue.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            if depth > self.max_depth:
                continue
            
            # Rate limiting
            time.sleep(self.delay)
            
            logger.info(f"Scraping: {current_url} (Depth: {depth})")
            
            try:
                page_data = self._fetch_page(current_url)
                if not page_data:
                    continue
                    
                self.visited_urls.add(current_url)
                page_data['depth'] = depth
                results.append(page_data)
                
                # If not at max depth, find links
                if depth < self.max_depth:
                    links = self._extract_links(page_data['html'], current_url)
                    
                    for link in links:
                        if link not in self.visited_urls:
                            # Check domain restriction
                            if same_domain_only:
                                if urlparse(link).netloc == base_domain:
                                    queue.append((link, depth + 1))
                            else:
                                queue.append((link, depth + 1))
                                
            except Exception as e:
                logger.error(f"Failed to scrape {current_url}: {e}")
                
        logger.info(f"Scraping completed. Visited {len(self.visited_urls)} pages.")
        return results

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except:
            return False

    def _fetch_page(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch and parse a single page."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type:
                logger.warning(f"Skipping non-HTML content at {url}: {content_type}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                script.decompose()
                
            # Extract title
            title = soup.title.string if soup.title else url
            title = title.strip() if title else url
            
            # Get text content
            text = soup.get_text(separator='\n', strip=True)
            
            # Basic cleaning
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return {
                'url': url,
                'title': title,
                'content': text,
                'html': response.text  # Kept for link extraction
            }
            
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract valid links from HTML content."""
        links = set()
        soup = BeautifulSoup(html, 'html.parser')
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Skip anchors, mailto, tel, javascript
            if href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                continue
                
            # Convert relative URLs to absolute
            full_url = urljoin(base_url, href)
            
            # Clean fragment
            full_url = full_url.split('#')[0]
            
            if self._is_valid_url(full_url):
                links.add(full_url)
                
        return list(links)

