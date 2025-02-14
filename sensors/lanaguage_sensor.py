from typing import Dict, Any, Optional
from bs4 import BeautifulSoup, Tag
import re
from .base_sensor import BaseSensor

class LanguageSensor(BaseSensor):
    """Sensor for detecting website language settings and requirements."""

    def __init__(self):
        super().__init__()
        self.language_patterns = {
            'html_attrs': ['lang', 'xml:lang', 'data-lang'],
            'meta_names': [
                'language', 
                'content-language',
                'og:locale',
                'dc.language',
                'language-detection'
            ],
            'header_names': ['content-language', 'accept-language'],
            'common_paths': ['/ar/', '/fr/', '/en/', '/es/', '/de/', '/zh/'],
            'language_codes': {
                'ar': 'Arabic',
                'fr': 'French',
                'en': 'English',
                'es': 'Spanish',
                'de': 'German',
                'zh': 'Chinese'
            },
            'language_keywords': [
                'language', 'langue', 'idioma', 'sprache', 'لغة',
                'languages', 'langues', 'idiomas', 'sprachen', 'اللغات'
            ]
        }

    async def detect(self, response: Any, **kwargs) -> Dict[str, Any]:
        """
        Detect language settings and requirements in the response.

        Args:
            response: HTTP response or page content
            **kwargs: Additional parameters

        Returns:
            Dict containing detection results
        """
        result = {
            'detected_language': None,
            'has_language_redirect': False,
            'available_languages': set(),
            'confidence': 0.0,
            'details': []
        }

        # Check response headers
        if 'headers' in response:
            headers = response['headers']
            for header in self.language_patterns['header_names']:
                if header.lower() in {k.lower(): v for k, v in headers.items()}:
                    lang = str(headers[header]).split(',')[0].strip().split('-')[0]
                    result['detected_language'] = lang
                    result['confidence'] = 0.9
                    result['details'].append(f'Found language in header: {lang}')

        if 'text' in response:
            content = response['text']
            soup = BeautifulSoup(content, 'html.parser')

            # Check HTML lang attribute
            html_tag = soup.find('html')
            if html_tag and isinstance(html_tag, Tag):
                for attr in self.language_patterns['html_attrs']:
                    lang_attr = html_tag.get(attr)
                    if lang_attr and isinstance(lang_attr, str):
                        lang = lang_attr.split('-')[0].lower()
                        if lang in self.language_patterns['language_codes']:
                            result['detected_language'] = lang
                            result['confidence'] = 1.0
                            result['details'].append(
                                f'Found language in HTML {attr}: {self.language_patterns["language_codes"][lang]}'
                            )

            # Check meta tags with improved detection
            for meta_tag in soup.find_all('meta'):
                if isinstance(meta_tag, Tag):
                    for attr in ['name', 'property', 'http-equiv']:
                        meta_name = meta_tag.get(attr, '').lower()
                        if any(pattern in meta_name for pattern in self.language_patterns['meta_names']):
                            content = meta_tag.get('content')
                            if content:
                                lang = content.split('-')[0].lower()
                                if lang in self.language_patterns['language_codes']:
                                    result['detected_language'] = lang
                                    result['confidence'] = 0.8
                                    result['details'].append(
                                        f'Found language in meta tag: {self.language_patterns["language_codes"][lang]}'
                                    )

            # Enhanced language switcher detection
            language_links = []
            # Method 1: Check for links with language keywords
            for keyword in self.language_patterns['language_keywords']:
                language_links.extend(
                    soup.find_all('a', text=re.compile(keyword, re.I))
                )

            # Method 2: Check for links with language codes
            for lang_code in self.language_patterns['language_codes']:
                language_links.extend(
                    soup.find_all('a', href=re.compile(f'[/\?]({lang_code}|lang={lang_code}|locale={lang_code})', re.I))
                )

            # Process found language links
            for link in language_links:
                if isinstance(link, Tag):
                    # Extract language from href
                    href = link.get('href', '')
                    if isinstance(href, str):
                        for lang_code in self.language_patterns['language_codes']:
                            if re.search(f'[/\?]({lang_code}|lang={lang_code}|locale={lang_code})', href, re.I):
                                result['available_languages'].add(lang_code)
                                result['confidence'] = max(result['confidence'], 0.7)
                                result['details'].append(
                                    f'Found language option: {self.language_patterns["language_codes"][lang_code]}'
                                )

            # Check URL path for language indicators
            current_url = kwargs.get('url', '')
            if current_url:
                # Check for language code in path
                for path in self.language_patterns['common_paths']:
                    lang_code = path.strip('/').lower()
                    if f'/{lang_code}/' in current_url.lower():
                        result['has_language_redirect'] = True
                        result['detected_language'] = lang_code
                        result['confidence'] = max(result['confidence'], 0.9)
                        result['details'].append(
                            f'Found language in URL path: {self.language_patterns["language_codes"][lang_code]}'
                        )

                # Check for language parameters
                lang_param_match = re.search(r'[?&](?:lang|locale)=(\w+)', current_url)
                if lang_param_match:
                    lang_code = lang_param_match.group(1).lower()
                    if lang_code in self.language_patterns['language_codes']:
                        result['detected_language'] = lang_code
                        result['confidence'] = max(result['confidence'], 0.8)
                        result['details'].append(
                            f'Found language in URL parameter: {self.language_patterns["language_codes"][lang_code]}'
                        )

        # Convert set to list for JSON serialization
        result['available_languages'] = list(result['available_languages'])

        return result

    def get_mitigation_strategy(self) -> Dict[str, Any]:
        """
        Provide strategies for handling language requirements.

        Returns:
            Dict containing mitigation strategies
        """
        return {
            'strategies': {
                'header_modification': {
                    'type': 'request_headers',
                    'priority': 'high',
                    'config': {
                        'accept-language': 'en-US,en;q=0.9,ar;q=0.8,fr;q=0.7',
                        'content-language': 'en-US'
                    }
                },
                'url_handling': {
                    'type': 'url_parameters',
                    'priority': 'medium',
                    'config': {
                        'append_language': True,
                        'default_language': 'en',
                        'supported_languages': list(self.language_patterns['language_codes'].keys())
                    }
                },
                'cookie_management': {
                    'type': 'language_cookies',
                    'priority': 'low',
                    'config': {
                        'set_language_cookie': True,
                        'cookie_name': 'preferred_language',
                        'cookie_value': 'en'
                    }
                }
            },
            'recommendations': [
                'Set appropriate Accept-Language header',
                'Handle language-specific redirects',
                'Maintain consistent language preferences across sessions',
                'Consider using translation services if needed'
            ]
        }