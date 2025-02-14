from typing import Dict, Any
import re
from .base_sensor import BaseSensor

class AntiBotSensor(BaseSensor):
    """Sensor for detecting anti-bot measures."""
    
    def __init__(self):
        super().__init__()
        self.antibot_patterns = {
            'headers': {
                'cf-ray': 'Cloudflare',
                'server': ['cloudflare', 'akamai', 'incapsula'],
                'x-bot-protection': None,
                'x-fw-protection': None
            },
            'response_codes': {
                403: 'Forbidden',
                429: 'Too Many Requests',
                503: 'Service Unavailable'
            },
            'content_patterns': [
                'automated access',
                'bot detected',
                'suspicious activity',
                'access denied',
                'rate limit exceeded',
                'ip blocked'
            ]
        }
    
    async def detect(self, response: Any, **kwargs) -> Dict[str, Any]:
        """
        Detect anti-bot measures in the response.
        
        Args:
            response: HTTP response or page content
            **kwargs: Additional parameters
            
        Returns:
            Dict containing detection results
        """
        result = {
            'has_antibot': False,
            'protection_type': [],
            'confidence': 0.0,
            'details': []
        }
        
        # Check response headers
        if hasattr(response, 'headers'):
            headers = response.headers
            for header, protection in self.antibot_patterns['headers'].items():
                if header in headers:
                    if isinstance(protection, list):
                        for p in protection:
                            if p.lower() in str(headers[header]).lower():
                                result['has_antibot'] = True
                                result['protection_type'].append(p)
                                result['confidence'] = 0.9
                                result['details'].append(f'Found {p} protection header')
                    elif protection:
                        result['has_antibot'] = True
                        result['protection_type'].append(protection)
                        result['confidence'] = 0.9
                        result['details'].append(f'Found {protection} protection header')
        
        # Check response status code
        if hasattr(response, 'status_code'):
            status_code = response.status_code
            if status_code in self.antibot_patterns['response_codes']:
                result['has_antibot'] = True
                result['protection_type'].append(f'Status {status_code}')
                result['confidence'] = 0.8
                result['details'].append(
                    f'Response code {status_code}: {self.antibot_patterns["response_codes"][status_code]}'
                )
        
        # Check content for anti-bot messages
        if hasattr(response, 'text'):
            content = response.text.lower()
            for pattern in self.antibot_patterns['content_patterns']:
                if re.search(pattern, content, re.I):
                    result['has_antibot'] = True
                    result['protection_type'].append('Content Protection')
                    result['confidence'] = max(result['confidence'], 0.7)
                    result['details'].append(f'Found anti-bot message: {pattern}')
        
        return result
    
    def get_mitigation_strategy(self) -> Dict[str, Any]:
        """
        Provide strategies for handling anti-bot measures.
        
        Returns:
            Dict containing mitigation strategies
        """
        return {
            'strategies': {
                'proxy_rotation': {
                    'type': 'rotating_proxies',
                    'priority': 'high',
                    'config': {
                        'rotation_interval': '5-10 minutes',
                        'proxy_types': ['residential', 'datacenter']
                    }
                },
                'request_delay': {
                    'type': 'dynamic_delay',
                    'priority': 'high',
                    'config': {
                        'min_delay': 2,
                        'max_delay': 10,
                        'random_factor': True
                    }
                },
                'browser_fingerprint': {
                    'type': 'fingerprint_rotation',
                    'priority': 'medium',
                    'config': {
                        'rotate_user_agents': True,
                        'mimic_real_browser': True
                    }
                }
            },
            'recommendations': [
                'Implement exponential backoff for rate limits',
                'Use residential proxies for better success rate',
                'Rotate browser fingerprints regularly',
                'Consider using specialized anti-bot bypass services'
            ]
        }
