"""
Confluence Integration Module
Provides functionality to fetch and process Confluence pages.
"""
import re
from typing import Dict, Any, List, Optional
from .utils import setup_logging

logger = setup_logging()


class ConfluenceIntegration:
    """Integration with Confluence Cloud and Server instances."""
    
    def __init__(self, url: str, instance_type: str = "cloud", 
                 api_token: str = None, username: str = None, password: str = None):
        """
        Initialize Confluence connection.
        
        Args:
            url: Confluence instance URL
            instance_type: "cloud" or "server"
            api_token: API token for authentication
            username: Username (for server or cloud with token)
            password: Password (for server, or API token for cloud)
        """
        self.url = url.rstrip('/')
        self.instance_type = instance_type.lower()
        self.api_token = api_token
        self.username = username
        self.password = password
        self._confluence = None
        
        self._initialize_confluence()
    
    def _initialize_confluence(self):
        """Initialize the Confluence client based on instance type."""
        try:
            if self.instance_type == "cloud":
                from atlassian.confluence import ConfluenceCloud
                
                if self.api_token:
                    # Cloud with token
                    self._confluence = ConfluenceCloud(
                        url=self.url,
                        token=self.api_token
                    )
                elif self.username and self.password:
                    # Cloud with username and API token (password field)
                    self._confluence = ConfluenceCloud(
                        url=self.url,
                        username=self.username,
                        password=self.password,
                        cloud=True
                    )
                else:
                    raise ValueError("Cloud instance requires either api_token or username+password (API token)")
            else:
                # Server/Data Center
                from atlassian import Confluence
                
                if self.api_token:
                    # Server with token
                    self._confluence = Confluence(
                        url=self.url,
                        token=self.api_token
                    )
                elif self.username and self.password:
                    # Server with username and password
                    self._confluence = Confluence(
                        url=self.url,
                        username=self.username,
                        password=self.password
                    )
                else:
                    raise ValueError("Server instance requires either api_token or username+password")
            
            logger.info(f"Confluence client initialized for {self.instance_type} instance at {self.url}")
        except ImportError:
            raise ImportError("atlassian-python-api package is required. Install with: pip install atlassian-python-api")
        except Exception as e:
            logger.error(f"Failed to initialize Confluence client: {e}")
            raise
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the Confluence connection.
        
        Returns:
            dict: Connection test result with success status and message
        """
        try:
            # Try to get current user or a simple API call
            if self.instance_type == "cloud":
                # For Cloud, try to get current user info
                try:
                    # Simple test: get all spaces (limited to 1)
                    spaces = self._confluence.get_all_spaces(start=0, limit=1)
                    return {
                        "success": True,
                        "message": "Connection successful",
                        "instance_type": self.instance_type,
                        "url": self.url
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Connection failed: {str(e)}"
                    }
            else:
                # For Server, try to get all spaces
                try:
                    spaces = self._confluence.get_all_spaces(start=0, limit=1)
                    return {
                        "success": True,
                        "message": "Connection successful",
                        "instance_type": self.instance_type,
                        "url": self.url
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Connection failed: {str(e)}"
                    }
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "success": False,
                "message": f"Connection test error: {str(e)}"
            }
    
    def extract_page_id_from_url(self, page_url_or_id: str) -> Optional[str]:
        """
        Extract page ID from Confluence URL or return the ID if it's already numeric.
        
        Args:
            page_url_or_id: Page URL or page ID
            
        Returns:
            str: Page ID or None if extraction fails
        """
        # If it's already a numeric ID, return it
        if page_url_or_id.isdigit():
            return page_url_or_id
        
        # Try to extract from URL patterns
        # Pattern 1: /pages/viewpage.action?pageId=123456
        match = re.search(r'pageId=(\d+)', page_url_or_id)
        if match:
            return match.group(1)
        
        # Pattern 2: /spaces/SPACE/pages/123456/Title
        match = re.search(r'/pages/(\d+)/', page_url_or_id)
        if match:
            return match.group(1)
        
        # Pattern 3: /display/SPACE/Page+Title?pageId=123456
        match = re.search(r'pageId=(\d+)', page_url_or_id)
        if match:
            return match.group(1)
        
        logger.warning(f"Could not extract page ID from: {page_url_or_id}")
        return None
    
    def fetch_page(self, page_id: str, expand: str = "body.storage,space,version") -> Optional[Dict[str, Any]]:
        """
        Fetch a single Confluence page by ID.
        
        Args:
            page_id: Page ID (numeric or extracted from URL)
            expand: Comma-separated list of properties to expand
            
        Returns:
            dict: Page data or None if not found
        """
        try:
            # Extract page ID if URL is provided
            actual_page_id = self.extract_page_id_from_url(page_id)
            if not actual_page_id:
                logger.error(f"Invalid page ID or URL: {page_id}")
                return None
            
            logger.info(f"Fetching Confluence page: {actual_page_id}")
            page = self._confluence.get_page_by_id(
                page_id=actual_page_id,
                expand=expand
            )
            
            if not page:
                logger.warning(f"Page not found: {actual_page_id}")
                return None
            
            return page
        except Exception as e:
            logger.error(f"Error fetching page {page_id}: {e}")
            return None
    
    def fetch_pages(self, page_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch multiple Confluence pages.
        
        Args:
            page_ids: List of page IDs or URLs
            
        Returns:
            list: List of page data dictionaries
        """
        pages = []
        for page_id in page_ids:
            page = self.fetch_page(page_id)
            if page:
                pages.append(page)
            else:
                logger.warning(f"Failed to fetch page: {page_id}")
        return pages
    
    def get_page_content(self, page: Dict[str, Any]) -> str:
        """
        Extract text content from a Confluence page.
        
        Args:
            page: Page data dictionary from Confluence API
            
        Returns:
            str: Extracted text content
        """
        try:
            body = page.get('body', {})
            
            # Try storage format first (most common)
            if 'storage' in body:
                content = body['storage'].get('value', '')
            # Try view format
            elif 'view' in body:
                content = body['view'].get('value', '')
            # Try editor format
            elif 'editor' in body:
                content = body['editor'].get('value', '')
            else:
                logger.warning("No body content found in page")
                return ""
            
            # Basic HTML/XML tag removal (simple approach)
            # For production, consider using html2text or similar library
            import html
            from html.parser import HTMLParser
            
            # Decode HTML entities
            content = html.unescape(content)
            
            # Remove HTML tags (simple regex - for production use proper HTML parser)
            content = re.sub(r'<[^>]+>', '', content)
            
            # Clean up whitespace
            content = re.sub(r'\s+', ' ', content)
            content = content.strip()
            
            return content
        except Exception as e:
            logger.error(f"Error extracting page content: {e}")
            return ""
    
    def get_page_metadata(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from a Confluence page.
        
        Args:
            page: Page data dictionary from Confluence API
            
        Returns:
            dict: Metadata dictionary
        """
        try:
            space = page.get('space', {})
            version = page.get('version', {})
            
            metadata = {
                "source": "confluence",
                "page_id": str(page.get('id', '')),
                "page_title": page.get('title', ''),
                "space_key": space.get('key', '') if isinstance(space, dict) else '',
                "space_name": space.get('name', '') if isinstance(space, dict) else '',
                "version": version.get('number', 1) if isinstance(version, dict) else 1,
                "url": f"{self.url}/pages/viewpage.action?pageId={page.get('id', '')}"
            }
            
            return metadata
        except Exception as e:
            logger.error(f"Error extracting page metadata: {e}")
            return {
                "source": "confluence",
                "page_id": "",
                "page_title": "",
                "space_key": "",
                "space_name": ""
            }

