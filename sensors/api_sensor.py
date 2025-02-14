from typing import Dict, Any
from bs4 import BeautifulSoup, Tag
import re
from .base_sensor import BaseSensor

class APISensor(BaseSensor):
    """Sensor for detecting various types of APIs and endpoints."""
    
    def __init__(self):
        super().__init__()
        self.api_patterns = {
            'rest_endpoints': {
                'paths': ['/api/', '/rest/', '/v1/', '/v2/', '/graphql'],
                'keywords': ['api', 'rest', 'endpoints', 'swagger', 'openapi']
            },
            'graphql': {
                'endpoints': ['/graphql', '/gql'],
                'indicators': ['query', 'mutation', '__schema']
            },
            'xhr_patterns': {
                'functions': ['XMLHttpRequest', 'fetch', 'axios', '$http', 'ajax'],
                'headers': ['X-Requested-With', 'Content-Type']
            },
            'documentation': {
                'paths': ['/docs', '/swagger', '/api-docs', '/redoc'],
                'keywords': ['swagger', 'openapi', 'api-documentation']
            }
        }
    
    async def detect(self, response: Any, **kwargs) -> Dict[str, Any]:
        """
        Detect API-related features in the response.
        
        Args:
            response: HTTP response or page content
            **kwargs: Additional parameters
            
        Returns:
            Dict containing detection results
        """
        result = {
            'has_api': False,
            'api_types': set(),
            'endpoints': set(),
            'confidence': 0.0,
            'details': []
        }
        
        # Check response headers
        if hasattr(response, 'headers'):
            headers = response.headers
            for header in self.api_patterns['xhr_patterns']['headers']:
                if header in headers:
                    result['has_api'] = True
                    result['api_types'].add('xhr')
                    result['confidence'] = max(result['confidence'], 0.8)
                    result['details'].append(f'Found API header: {header}')
        
        if hasattr(response, 'text'):
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check for API endpoints in scripts
            scripts = soup.find_all('script')
            for script in scripts:
                if isinstance(script, Tag):
                    script_content = script.string if script.string else ''
                    if isinstance(script_content, str):
                        # Check for XHR/fetch calls
                        for func in self.api_patterns['xhr_patterns']['functions']:
                            if func in script_content:
                                result['has_api'] = True
                                result['api_types'].add('xhr')
                                result['confidence'] = max(result['confidence'], 0.7)
                                result['details'].append(f'Found {func} usage')
                        
                        # Look for API endpoints in script content
                        endpoint_matches = re.finditer(r'["\'](/(?:api|v[0-9]+)/[^"\']+)["\']', script_content)
                        for match in endpoint_matches:
                            result['has_api'] = True
                            result['api_types'].add('rest')
                            result['endpoints'].add(match.group(1))
                            result['confidence'] = max(result['confidence'], 0.9)
                            result['details'].append(f'Found API endpoint: {match.group(1)}')
            
            # Check for GraphQL indicators
            for indicator in self.api_patterns['graphql']['indicators']:
                if indicator in content:
                    result['has_api'] = True
                    result['api_types'].add('graphql')
                    result['confidence'] = max(result['confidence'], 0.8)
                    result['details'].append(f'Found GraphQL indicator: {indicator}')
            
            # Check current URL for API patterns
            current_url = kwargs.get('url', '')
            if current_url:
                for api_type, patterns in self.api_patterns.items():
                    if 'paths' in patterns:
                        for path in patterns['paths']:
                            if path in current_url:
                                result['has_api'] = True
                                result['api_types'].add(api_type)
                                result['confidence'] = max(result['confidence'], 0.9)
                                result['details'].append(f'URL contains {api_type} path: {path}')
        
        # Convert sets to lists for JSON serialization
        result['api_types'] = list(result['api_types'])
        result['endpoints'] = list(result['endpoints'])
        
        return result
    
    def get_mitigation_strategy(self) -> Dict[str, Any]:
        """
        Provide strategies for handling API detection.
        
        Returns:
            Dict containing mitigation strategies
        """
        return {
            'strategies': {
                'authentication': {
                    'type': 'api_auth',
                    'priority': 'high',
                    'config': {
                        'auth_methods': ['bearer', 'api_key', 'oauth'],
                        'retry_on_401': True
                    }
                },
                'rate_limiting': {
                    'type': 'request_throttling',
                    'priority': 'high',
                    'config': {
                        'max_requests': 100,
                        'time_window': 60,
                        'backoff_factor': 2
                    }
                },
                'documentation': {
                    'type': 'api_docs_extraction',
                    'priority': 'medium',
                    'config': {
                        'save_swagger': True,
                        'extract_endpoints': True
                    }
                }
            },
            'recommendations': [
                'Implement proper API authentication',
                'Respect rate limits and implement backoff',
                'Extract and save API documentation if available',
                'Consider using dedicated API clients for different API types'
            ]
        }