import unittest
from unittest.mock import patch, MagicMock
from src.web_scraper import WebScraper

class TestWebScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = WebScraper(max_depth=1)

    def test_is_valid_url(self):
        self.assertTrue(self.scraper._is_valid_url("https://example.com"))
        self.assertTrue(self.scraper._is_valid_url("http://example.com/page"))
        self.assertFalse(self.scraper._is_valid_url("javascript:void(0)"))
        self.assertFalse(self.scraper._is_valid_url("mailto:user@example.com"))

    @patch('src.web_scraper.requests.Session.get')
    def test_scrape_url(self, mock_get):
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.text = '<html><head><title>Test Page</title></head><body><p>Hello World</p><a href="/link">Link</a></body></html>'
        mock_get.return_value = mock_response

        results = self.scraper.scrape_url("https://example.com")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['url'], "https://example.com")
        self.assertEqual(results[0]['title'], "Test Page")
        self.assertIn("Hello World", results[0]['content'])

if __name__ == '__main__':
    unittest.main()

