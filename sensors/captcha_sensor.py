from typing import Dict, Any
from bs4 import BeautifulSoup
import re
from .base_sensor import BaseSensor

class CaptchaSensor(BaseSensor):
    """Sensor for detecting various types of CAPTCHA systems."""
    
    def __init__(self):
        super().__init__()
        self.captcha_patterns = {
            'recaptcha': {
                'classes': ['g-recaptcha', 'recaptcha'],
                'scripts': ['www.google.com/recaptcha', 'recaptcha.net']
            },
            'hcaptcha': {
                'classes': ['h-captcha'],
                'scripts': ['hcaptcha.com']
            },
            'generic': {
                'keywords': ['captcha', 'verify human', 'prove you are human']
            }
        }
    
    async def detect(self, response: Any, **kwargs) -> Dict[str, Any]:
        """
        Detect presence of CAPTCHA systems in the response.
        
        Args:
            response: HTTP response or page content
            **kwargs: Additional parameters
            
        Returns:
            Dict containing detection results
        """
        if hasattr(response, 'text'):
            content = response.text
        else:
            content = str(response)
            
        soup = BeautifulSoup(content, 'html.parser')
        
        result = {
            'has_captcha': False,
            'captcha_type': None,
            'confidence': 0.0,
            'details': []
        }
        
        # Check for known CAPTCHA implementations
        for captcha_type, patterns in self.captcha_patterns.items():
            if captcha_type != 'generic':
                # Check for CAPTCHA-specific classes
                for class_name in patterns['classes']:
                    elements = soup.find_all(class_=re.compile(class_name, re.I))
                    if elements:
                        result['has_captcha'] = True
                        result['captcha_type'] = captcha_type
                        result['confidence'] = 0.9
                        result['details'].append(f'Found {class_name} element')
                
                # Check for CAPTCHA-specific scripts
                for script_pattern in patterns['scripts']:
                    scripts = soup.find_all('script', src=re.compile(script_pattern, re.I))
                    if scripts:
                        result['has_captcha'] = True
                        result['captcha_type'] = captcha_type
                        result['confidence'] = 1.0
                        result['details'].append(f'Found {script_pattern} script')
            
            else:
                # Check for generic CAPTCHA keywords
                for keyword in patterns['keywords']:
                    if re.search(keyword, content, re.I):
                        result['has_captcha'] = True
                        result['captcha_type'] = 'unknown'
                        result['confidence'] = 0.7
                        result['details'].append(f'Found keyword: {keyword}')
        
        return result
    
    def get_mitigation_strategy(self) -> Dict[str, Any]:
        """
        Provide strategies for handling different types of CAPTCHAs.
        
        Returns:
            Dict containing mitigation strategies
        """
        return {
            'strategies': {
                'recaptcha': {
                    'type': 'service_required',
                    'service': '2captcha/anticaptcha',
                    'priority': 'high'
                },
                'hcaptcha': {
                    'type': 'service_required',
                    'service': '2captcha/anticaptcha',
                    'priority': 'high'
                },
                'unknown': {
                    'type': 'manual_review',
                    'priority': 'medium'
                }
            },
            'recommendations': [
                'Implement delay between requests',
                'Use rotating proxies',
                'Add human-like browser fingerprints'
            ]
        }
