from typing import Dict, Any
from bs4 import BeautifulSoup, Tag
import re
import aiohttp
from .base_sensor import BaseSensor
from Wappalyzer import Wappalyzer, WebPage

class MobileSensor(BaseSensor):
    """Sensor for detecting mobile-specific features and configurations."""

    def __init__(self):
        super().__init__()
        self.user_agent = "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36"
        try:
            self.wappalyzer = Wappalyzer.latest()
            print("Wappalyzer initialized successfully")
        except Exception as e:
            print(f"Error initializing Wappalyzer: {str(e)}")
            self.wappalyzer = None

        self.mobile_patterns = {
            'url_patterns': {
                'subdomains': ['m.', 'mobile.', 'touch.'],
                'paths': ['/mobile/', '/m/', '/amp/']
            },
            'meta_tags': {
                'viewport': 'viewport',
                'mobile_web_app': 'mobile-web-app-capable',
                'apple_mobile': 'apple-mobile-web-app-capable',
                'format_detection': 'format-detection',
                'theme_color': 'theme-color',
                'application_name': 'application-name'
            },
            'app_links': {
                'ios': {
                    'meta_names': ['apple-itunes-app', 'apple-mobile-web-app-title'],
                    'store_urls': ['apps.apple.com', 'itunes.apple.com']
                },
                'android': {
                    'meta_names': ['google-play-app'],
                    'store_urls': ['play.google.com']
                }
            },
            'responsive_indicators': {
                'meta': ['viewport', 'media'],
                'css_rules': ['@media', 'max-width', 'min-width'],
                'frameworks': ['bootstrap', 'foundation', 'tailwind', 'material-ui']
            }
        }

    async def analyze_technologies(self, url: str, html_content: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Analyze website technologies using Wappalyzer and custom patterns."""
        if not self.wappalyzer:
            return {}

        try:
            # Add our user agent to the headers if not present
            if 'User-Agent' not in headers:
                headers['User-Agent'] = self.user_agent

            webpage = WebPage(url, html_content, headers)
            detected_technologies = self.wappalyzer.analyze_with_categories(webpage)

            print(f"Raw Wappalyzer results for {url}:")
            for tech, cats in detected_technologies.items():
                print(f"- {tech}: {cats}")

            technologies = {
                'frameworks': [],
                'mobile_frameworks': [],
                'javascript_frameworks': [],
                'analytics': [],
                'advertising': [],
                'cms': None,
                'server': None,
                'cdn': None,
                'security': [],
                'ui_frameworks': []
            }

            # Process detected technologies
            for tech, cats in detected_technologies.items():
                if not isinstance(cats, list):
                    continue

                # Map technologies to categories
                tech_mappings = [
                    ('Mobile', 'mobile_frameworks'),
                    ('Web framework', 'frameworks'),
                    ('JavaScript', 'javascript_frameworks'),
                    ('Analytics', 'analytics'),
                    ('Advertising', 'advertising'),
                    ('CMS', 'cms'),
                    ('Web server', 'server'),
                    ('CDN', 'cdn'),
                    ('Security', 'security'),
                    ('UI framework', 'ui_frameworks')
                ]

                for cat_pattern, tech_key in tech_mappings:
                    if any(cat_pattern in cat for cat in cats):
                        if isinstance(technologies[tech_key], list):
                            technologies[tech_key].append(tech)
                        else:
                            technologies[tech_key] = tech

            # Additional pattern matching from HTML
            soup = BeautifulSoup(html_content, 'html.parser')

            # Check for common mobile frameworks
            framework_patterns = {
                'bootstrap': {'class': 'container', 'link': 'bootstrap'},
                'foundation': {'class': 'row', 'link': 'foundation'},
                'material-ui': {'class': 'MuiButton-root', 'link': 'material'},
                'tailwind': {'class': 'text-center', 'link': 'tailwind'}
            }

            for framework, patterns in framework_patterns.items():
                if (soup.find('link', href=re.compile(patterns['link'], re.I)) or 
                    soup.find(class_=re.compile(patterns['class']))):
                    technologies['ui_frameworks'].append(framework)

            # Remove empty lists and None values
            return {k: v for k, v in technologies.items() if v}

        except Exception as e:
            print(f"Error analyzing technologies: {str(e)}")
            return {}

    async def _check_play_store(self, domain: str) -> Dict[str, Any]:
        """Check Google Play Store for mobile app."""
        play_store_info = {
            'has_app': False,
            'app_id': None,
            'details': []
        }

        try:
            search_url = f"https://play.google.com/store/search?q={domain}&c=apps"
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')

                        # Look for app listings that match the domain
                        app_links = soup.find_all('a', href=re.compile(r'/store/apps/details'))
                        for link in app_links:
                            href = link.get('href', '')
                            if isinstance(href, str) and domain.lower() in href.lower():
                                match = re.search(self.mobile_patterns['store_patterns']['play_store'], href)
                                if match:
                                    play_store_info['has_app'] = True
                                    play_store_info['app_id'] = match.group(1)
                                    play_store_info['details'].append(f'Found Android app: {match.group(1)}')
                                    break
        except Exception as e:
            play_store_info['details'].append(f'Error checking Play Store: {str(e)}')

        return play_store_info

    async def detect(self, response: Any, **kwargs) -> Dict[str, Any]:
        """Detect mobile-specific features in the response."""
        result = {
            'has_mobile_version': False,
            'mobile_features': set(),
            'app_links': {
                'ios': set(),
                'android': set()
            },
            'technologies': {},
            'confidence': 0.0,
            'details': []
        }

        try:
            current_url = kwargs.get('url', '')

            # Add user agent to headers if making requests
            headers = response.get('headers', {})
            if 'User-Agent' not in headers:
                headers['User-Agent'] = self.user_agent

            # Analyze technologies using Wappalyzer
            if 'text' in response and current_url:
                print(f"Analyzing technologies for URL: {current_url}")
                result['technologies'] = await self.analyze_technologies(
                    current_url,
                    response['text'],
                    headers
                )
                print(f"Detected technologies: {result['technologies']}")

                if result['technologies'].get('mobile_frameworks'):
                    result['has_mobile_version'] = True
                    result['mobile_features'].add('mobile_framework')
                    result['confidence'] = max(result['confidence'], 0.9)
                    result['details'].append(
                        f"Detected mobile frameworks: {', '.join(result['technologies']['mobile_frameworks'])}"
                    )


            # Get domain for app store checks
            domain = current_url.split('/')[2] if current_url.startswith(('http://', 'https://')) else ''


            # Check Play Store for mobile app
            if domain:
                play_store_info = await self._check_play_store(domain)
                if play_store_info['has_app']:
                    result['has_mobile_version'] = True
                    result['mobile_features'].add('android_app')
                    result['app_links']['android'].add(play_store_info['app_id'])
                    result['confidence'] = max(result['confidence'], 1.0)
                    result['details'].extend(play_store_info['details'])

            # Check response headers
            if 'headers' in response:
                headers = response['headers']
                if 'Vary' in headers and 'User-Agent' in str(headers['Vary']):
                    result['has_mobile_version'] = True
                    result['mobile_features'].add('user_agent_detection')
                    result['confidence'] = max(result['confidence'], 0.7)
                    result['details'].append('Found User-Agent variation header')

            if 'text' in response:
                content = response['text']
                soup = BeautifulSoup(content, 'html.parser')

                # Check meta viewport
                viewport = soup.find('meta', {'name': 'viewport'})
                if viewport and isinstance(viewport, Tag):
                    result['has_mobile_version'] = True
                    result['mobile_features'].add('responsive_design')
                    result['confidence'] = max(result['confidence'], 0.9)
                    result['details'].append('Found responsive viewport meta tag')

                # Check mobile-specific meta tags
                for meta_name in self.mobile_patterns['meta_tags'].values():
                    meta_tag = soup.find('meta', {'name': meta_name})
                    if meta_tag and isinstance(meta_tag, Tag):
                        result['has_mobile_version'] = True
                        result['mobile_features'].add('mobile_optimized')
                        result['confidence'] = max(result['confidence'], 0.8)
                        result['details'].append(f'Found mobile meta tag: {meta_name}')

                # Check for app store links
                for platform, patterns in self.mobile_patterns['app_links'].items():
                    # Check meta tags for app links
                    for meta_name in patterns['meta_names']:
                        meta_tag = soup.find('meta', {'name': meta_name})
                        if meta_tag and isinstance(meta_tag, Tag):
                            content = meta_tag.get('content')
                            if content:
                                result['has_mobile_version'] = True
                                result['mobile_features'].add(f'{platform}_app')
                                result['app_links'][platform].add(content)
                                result['confidence'] = max(result['confidence'], 1.0)
                                result['details'].append(f'Found {platform} app meta tag')

                    # Check for app store URLs in links
                    for store_url in patterns['store_urls']:
                        app_links = soup.find_all('a', href=re.compile(store_url))
                        for link in app_links:
                            if isinstance(link, Tag):
                                href = link.get('href')
                                if href:
                                    result['has_mobile_version'] = True
                                    result['mobile_features'].add(f'{platform}_app')
                                    result['app_links'][platform].add(href)
                                    result['confidence'] = max(result['confidence'], 1.0)
                                    result['details'].append(f'Found {platform} app store link')

                # Check for responsive design indicators in stylesheets
                style_tags = soup.find_all('style')
                for style in style_tags:
                    if style.string:
                        for indicator in self.mobile_patterns['responsive_indicators']['css_rules']:
                            if indicator in style.string:
                                result['has_mobile_version'] = True
                                result['mobile_features'].add('responsive_design')
                                result['confidence'] = max(result['confidence'], 0.8)
                                result['details'].append(f'Found responsive CSS: {indicator}')

                # Check URL patterns
                if current_url:
                    # Check for mobile subdomains
                    for subdomain in self.mobile_patterns['url_patterns']['subdomains']:
                        if re.search(f'^https?://{subdomain}', current_url, re.I):
                            result['has_mobile_version'] = True
                            result['mobile_features'].add('mobile_subdomain')
                            result['confidence'] = max(result['confidence'], 1.0)
                            result['details'].append(f'Found mobile subdomain: {subdomain}')

                    # Check for mobile paths
                    for path in self.mobile_patterns['url_patterns']['paths']:
                        if path in current_url:
                            result['has_mobile_version'] = True
                            result['mobile_features'].add('mobile_path')
                            result['confidence'] = max(result['confidence'], 0.9)
                            result['details'].append(f'Found mobile path: {path}')

        except Exception as e:
            error_msg = f"Error during detection: {str(e)}"
            print(error_msg)
            result['details'].append(error_msg)

        # Convert sets to lists for JSON serialization
        result['mobile_features'] = list(result['mobile_features'])
        result['app_links']['ios'] = list(result['app_links']['ios'])
        result['app_links']['android'] = list(result['app_links']['android'])

        return result

    def get_mitigation_strategy(self) -> Dict[str, Any]:
        """
        Provide strategies for handling mobile version detection.

        Returns:
            Dict containing mitigation strategies
        """
        return {
            'strategies': {
                'user_agent': {
                    'type': 'mobile_user_agent',
                    'priority': 'high',
                    'config': {
                        'rotate_devices': True,
                        'platforms': ['ios', 'android'],
                        'use_real_devices': True
                    }
                },
                'viewport_handling': {
                    'type': 'responsive_viewport',
                    'priority': 'medium',
                    'config': {
                        'widths': [320, 375, 414, 768],
                        'emulate_touch': True
                    }
                },
                'app_deep_linking': {
                    'type': 'app_link_handling',
                    'priority': 'low',
                    'config': {
                        'extract_app_ids': True,
                        'save_deep_links': True
                    }
                }
            },
            'recommendations': [
                'Use mobile User-Agent strings when needed',
                'Handle responsive layouts appropriately',
                'Extract and store mobile app information',
                'Consider testing with real mobile device profiles'
            ]
        }