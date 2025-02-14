"""
Web content analyzer module.
Responsible for analyzing new URLs and content based on initial seeds and patterns.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import aiohttp
import logging
from .sensors import (
    CaptchaSensor,
    JavaScriptSensor,
    AntiBotSensor,
    LanguageSensor,
    APISensor,
    MobileSensor
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    url: str
    analyzed_at: datetime
    content_type: str
    metadata: Dict[str, Any]
    profile: Dict[str, Any]

class WebAnalyzer:
    """Analyzes new web content based on patterns and initial seeds"""

    def __init__(self):
        self.analyzed_urls: List[str] = []
        self.patterns = []
        # Initialize all sensors
        self.sensors = {
            'captcha': CaptchaSensor(),
            'javascript': JavaScriptSensor(),
            'antibot': AntiBotSensor(),
            'language': LanguageSensor(),
            'api': APISensor(),
            'mobile': MobileSensor()
        }

    async def analyze_url(self, url: str) -> Dict[str, Any]:
        """
        Analyze a URL using all available sensors

        Args:
            url (str): URL to analyze

        Returns:
            Dict containing aggregated sensor results
        """
        profile = {
            'url': url,
            'status_code': None,
            'headers': {},
            'restrictions': {},
            'features': {},
            'mitigation_strategies': {},
            'overall_confidence': 0.0
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    # Create a response-like object with the content
                    response_data = {
                        'status_code': response.status,
                        'headers': dict(response.headers),
                        'text': await response.text(),
                        'url': url
                    }

                    profile['status_code'] = response.status
                    profile['headers'] = dict(response.headers)

                    # Run all sensors
                    total_confidence = 0
                    sensor_count = 0

                    for sensor_name, sensor in self.sensors.items():
                        try:
                            result = await sensor.detect(response_data, url=url)

                            # Add sensor results to profile
                            if sensor_name in ['captcha', 'javascript', 'antibot']:
                                profile['restrictions'][sensor_name] = result
                                total_confidence += result.get('confidence', 0)
                                sensor_count += 1
                            else:
                                profile['features'][sensor_name] = result

                            # Add mitigation strategies
                            mitigation = sensor.get_mitigation_strategy(result)
                            if mitigation:
                                profile['mitigation_strategies'][sensor_name] = mitigation
                        except Exception as e:
                            logger.error(f"Error in {sensor_name} sensor: {str(e)}")
                            continue

                    # Calculate overall confidence
                    if sensor_count > 0:
                        profile['overall_confidence'] = round(total_confidence / sensor_count, 2)

        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch URL {url}: {str(e)}")

        return profile

    async def analyze(self, seed_url: str) -> List[AnalysisResult]:
        """
        Analyze new content starting from a seed URL

        Args:
            seed_url (str): The starting point URL for analysis

        Returns:
            List of analyzed content results
        """
        # Analyze the seed URL first
        profile = await self.analyze_url(seed_url)

        # Create initial Analysis result
        result = AnalysisResult(
            url=seed_url,
            analyzed_at=datetime.utcnow(),
            content_type=profile['headers'].get('content-type', 'unknown'),
            metadata={
                'status_code': profile['status_code'],
                'server': profile['headers'].get('server', 'unknown'),
            },
            profile=profile
        )

        # Store the URL
        if seed_url not in self.analyzed_urls:
            self.analyzed_urls.append(seed_url)

        return [result]

    async def analyze_pattern(self, urls: List[str]):
        """
        Analyze URLs to detect patterns for further analysis

        Args:
            urls (List[str]): List of URLs to analyze
        """
        # TODO: Implement URL pattern analysis and generate rules for the spider
        pass
