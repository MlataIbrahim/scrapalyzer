from typing import Dict, Any, List
from bs4 import BeautifulSoup
import re
from .base_sensor import BaseSensor
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthSensor(BaseSensor):
    """Sensor for detecting various types of authentication mechanisms."""
    
    def __init__(self):
        super().__init__()
        self.auth_patterns = {
            'login_form': {
                'form_action_keywords': ['login', 'signin', 'auth', 'authenticate'],
                'input_types': ['text', 'password', 'email'],
                'buttons': ['login', 'sign in', 'submit']
            },
            'oauth': {
                'providers': ['google', 'facebook', 'twitter', 'github'],
                'classes': ['btn-google', 'btn-facebook', 'btn-twitter', 'btn-github'],
                'links': ['login/oauth', 'oauth/login']
            },
            'http_basic': {
                'headers': ['basic realm'],
                'status_codes': [401]
            },
            'token_based': {
                'header_names': ['authorization', 'token']
            }
        }
    
    async def detect(self, response: Any, **kwargs) -> Dict[str, Any]:
        """
        Detect presence of authentication mechanisms in the response.
        
        Args:
            response: HTTP response or page content
            **kwargs: Additional parameters
            
        Returns:
            Dict containing detection results
        """
        try:
            if hasattr(response, 'text'):
                content = response.text
            else:
                content = str(response)
            
            soup = BeautifulSoup(content, 'html.parser')
            headers = dict(response.get('headers', {}))
            
            result = {
                'has_auth': False,
                'auth_type': [],
                'confidence': 0.0,
                'details': []
            }
            
            # Check for login forms
            if self._detect_login_form(soup):
                result['has_auth'] = True
                result['auth_type'].append('login_form')
                result['details'].append("Found login form")
            
            # Check for OAuth providers
            oauth_details = self._detect_oauth(soup)
            if oauth_details:
                result['has_auth'] = True
                result['auth_type'].extend(oauth_details)
                result['details'].extend(oauth_details)
            
            # Check for HTTP Basic Auth
            if self._detect_http_basic(headers):
                result['has_auth'] = True
                result['auth_type'].append('http_basic')
                result['details'].append("Found HTTP Basic Auth")
            
            # Check for token-based authentication
            if self._detect_token_based(headers):
                result['has_auth'] = True
                result['auth_type'].append('token_based')
                result['details'].append("Found token-based authentication")
            
            # Set confidence based on the number of detected auth types
            result['confidence'] = round(min(1.0, len(result['auth_type']) * 0.3), 2)
            
            return result
        
        except Exception as e:
            logger.error(f"Error detecting authentication: {str(e)}")
            return {
                'has_auth': False,
                'auth_type': [],
                'confidence': 0.0,
                'details': [f"Error processing response: {str(e)}"]
            }
    
    def _detect_login_form(self, soup: BeautifulSoup) -> bool:
        forms = soup.find_all('form', method=lambda m: m and m.lower() in ['post', 'get'])
        for form in forms:
            action = form.get('action', '').lower()
            if any(keyword in action for keyword in self.auth_patterns['login_form']['form_action_keywords']):
                inputs = form.find_all('input', type=lambda t: t and t.lower() in self.auth_patterns['login_form']['input_types'])
                buttons = form.find_all('button', {'type': 'submit'}) + form.find_all('input', type='submit')
                buttons += form.find_all('input', type='button', value=lambda v: v and v.lower() in self.auth_patterns['login_form']['buttons'])
                if inputs and buttons:
                    return True
        return False
    
    def _detect_oauth(self, soup: BeautifulSoup) -> List[str]:
        details = []
        for provider in self.auth_patterns['oauth']['providers']:
            buttons = soup.find_all('button', class_=re.compile(provider, re.IGNORECASE))
            links = soup.find_all('a', href=re.compile(provider, re.IGNORECASE))
            classes = soup.find_all(class_=re.compile('|'.join(self.auth_patterns['oauth']['classes']), re.IGNORECASE))
            oauth_links = soup.find_all('a', href=re.compile('|'.join(self.auth_patterns['oauth']['links']), re.IGNORECASE))
            
            if buttons or links or classes or oauth_links:
                details.append(f"Found OAuth provider: {provider}")
        
        return details
    
    def _detect_http_basic(self, headers: Dict[str, Any]) -> bool:
        content_type = headers.get('content-type', '').lower()
        www_authenticate = headers.get('www-authenticate', '').lower()
        status_code = headers.get('status_code', 200)
        
        if any(auth_type in www_authenticate for auth_type in self.auth_patterns['http_basic']['headers']) and status_code == 401:
            return True
        return False
    
    def _detect_token_based(self, headers: Dict[str, Any]) -> bool:
        for header in self.auth_patterns['token_based']['header_names']:
            if header in headers:
                return True
        return False
    
    def get_mitigation_strategy(self) -> Dict[str, Any]:
        """
        Provide strategies for handling different types of authentication.
        
        Returns:
            Dict containing mitigation strategies
        """
        return {
            'strategies': {
                'login_form': {
                    'type': 'submit_form',
                    'method': 'POST',
                    'priority': 'medium'
                },
                'oauth': {
                    'type': 'external_service',
                    'priority': 'high'
                },
                'http_basic': {
                    'type': 'basic_auth',
                    'priority': 'medium'
                },
                'token_based': {
                    'type': 'bearer_token',
                    'priority': 'high'
                }
            },
            'recommendations': [
                'Use secure and valid credentials',
                'Handle redirects properly',
                'Ensure secure HTTPS browsing'
            ]
        }
