import unittest
import asyncio
from unittest.mock import patch, MagicMock
from analyzer import WebAnalyzer

class TestWebAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = WebAnalyzer()

    @patch('aiohttp.ClientSession.get')
    async def test_analyze_url_captcha(self, mock_get):
        mock_response = asyncio.Future()
        mock_response_data = {
            'status_code': 200,
            'headers': {'Content-Type': 'text/html'},
            'text': '<html><head><title>Test</title></head><body><script src="https://www.google.com/recaptcha/api.js"></script></body></html>',
            'url': 'https://example.com'
        }
        mock_response.set_result(mock_response_data)
        mock_get.return_value.__aenter__.return_value = mock_response

        profile = await self.analyzer.analyze_url('https://example.com')
        self.assertEqual(profile['url'], 'https://example.com')
        self.assertEqual(profile['status_code'], 200)
        self.assertIn('restrictions', profile)
        self.assertIn('features', profile)
        self.assertIn('mitigation_strategies', profile)
        self.assertTrue(profile['restrictions']['captcha']['has_captcha'])
        self.assertEqual(profile['restrictions']['captcha']['captcha_type'], 'recaptcha')
        self.assertEqual(profile['restrictions']['captcha']['confidence'], 1.0)

    @patch('aiohttp.ClientSession.get')
    async def test_analyze_url_no_captcha(self, mock_get):
        mock_response = asyncio.Future()
        mock_response_data = {
            'status_code': 200,
            'headers': {'Content-Type': 'text/html'},
            'text': '<html><head><title>Test</title></head><body><script>alert("test");</script></body></html>',
            'url': 'https://example.com'
        }
        mock_response.set_result(mock_response_data)
        mock_get.return_value.__aenter__.return_value = mock_response

        profile = await self.analyzer.analyze_url('https://example.com')
        self.assertEqual(profile['url'], 'https://example.com')
        self.assertEqual(profile['status_code'], 200)
        self.assertIn('restrictions', profile)
        self.assertIn('features', profile)
        self.assertIn('mitigation_strategies', profile)
        self.assertFalse(profile['restrictions']['captcha']['has_captcha'])
        self.assertIsNone(profile['restrictions']['captcha']['captcha_type'])
        self.assertEqual(profile['restrictions']['captcha']['confidence'], 0.0)

    @patch('aiohttp.ClientSession.get')
    async def test_analyze_url_error(self, mock_get):
        mock_get.return_value.__aenter__.side_effect = Exception("Mocked error")
        profile = await self.analyzer.analyze_url('https://example.com')
        self.assertEqual(profile['url'], 'https://example.com')
        self.assertEqual(profile['status_code'], None)
        self.assertIn('restrictions', profile)
        self.assertIn('features', profile)
        self.assertIn('mitigation_strategies', profile)
        self.assertFalse(profile['restrictions']['captcha']['has_captcha'])
        self.assertIsNone(profile['restrictions']['captcha']['captcha_type'])
        self.assertEqual(profile['restrictions']['captcha']['confidence'], 0.0)
        self.assertIn("Error processing response: Mocked error", profile['restrictions']['captcha']['details'])

if __name__ == '__main__':
    unittest.main(argv=[''], exit=False)
