from typing import Dict, Any
from bs4 import BeautifulSoup
import re
from .base_sensor import BaseSensor

class JavaScriptSensor(BaseSensor):
    """Sensor for detecting JavaScript requirements and restrictions."""
    
    def __init__(self):
        super().__init__()
        self.js_patterns = {
            'noscript_warning': {
                'tags': ['noscript'],
                'keywords': ['javascript is required', 'enable javascript', 'js is required']
            },
            'dynamic_content': {
                'attributes': ['onclick', 'onload', 'onchange', 'data-react', 'ng-', 'v-'],
                'frameworks': ['react', 'angular', 'vue', 'jquery']
            }
        }
    
    async def detect(self, response: Any, **kwargs) -> Dict[str, Any]:
        """
        Detect JavaScript requirements in the response.
        
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
            'requires_js': False,
            'js_features': [],
            'confidence': 0.0,
            'details': []
        }
        
        # Check for noscript warnings
        noscript_elements = soup.find_all('noscript')
        for element in noscript_elements:
            for keyword in self.js_patterns['noscript_warning']['keywords']:
                if re.search(keyword, element.text, re.I):
                    result['requires_js'] = True
                    result['confidence'] = 0.9
                    result['details'].append(f'Found noscript warning: {keyword}')
        
        # Check for dynamic content indicators
        for attr in self.js_patterns['dynamic_content']['attributes']:
            elements = soup.find_all(attrs={re.compile(f'^{attr}'): True})
            if elements:
                result['requires_js'] = True
                result['js_features'].append(f'dynamic_attribute:{attr}')
                result['confidence'] = max(result['confidence'], 0.8)
                result['details'].append(f'Found dynamic attribute: {attr}')
        
        # Check for JavaScript frameworks
        scripts = soup.find_all('script')
        for script in scripts:
            for framework in self.js_patterns['dynamic_content']['frameworks']:
                if script.get('src') and framework in script['src'].lower():
                    result['requires_js'] = True
                    result['js_features'].append(f'framework:{framework}')
                    result['confidence'] = 1.0
                    result['details'].append(f'Found {framework} framework')
        
        return result
    
    def get_mitigation_strategy(self) -> Dict[str, Any]:
        """
        Provide strategies for handling JavaScript requirements.
        
        Returns:
            Dict containing mitigation strategies
        """
        return {
            'strategies': {
                'headless_browser': {
                    'type': 'puppeteer/selenium',
                    'priority': 'high',
                    'config': {
                        'wait_for_network_idle': True,
                        'timeout': 30000
                    }
                },
                'js_rendering': {
                    'type': 'prerender_service',
                    'priority': 'medium',
                    'options': ['rendertron', 'prerender.io']
                }
            },
            'recommendations': [
                'Use headless browser with JavaScript enabled',
                'Implement wait conditions for dynamic content',
                'Consider using a pre-rendering service'
            ]
        }
