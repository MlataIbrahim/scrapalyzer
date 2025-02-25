# Scrapalyzer
An automated tool that analyzes websites and generates structured JSON profiles containing essential technical insights for building efficient web scrapers. Detects JavaScript rendering, anti-bot systems, CAPTCHA, authentication requirements, and API endpoints to help developers implement robust scraping solutions.

## Features

Scrapalyzer includes multiple specialized sensors to detect and analyze different website characteristics:

- **Antibot Sensor**: Detects anti-bot measures and protection systems
- **API Sensor**: Identifies API endpoints and their requirements
- **Language Sensor**: Analyzes website's programming languages and frameworks
- **Mobile Sensor**: Evaluates mobile-specific behaviors and responsiveness
- **Captcha Sensor**: Detects various types of CAPTCHA implementations
- **JavaScript Sensor**: Analyzes JavaScript dependencies and requirements

## Installation

```bash
pip install scrapalyzer
# or
poetry add scrapalyzer
```

## Requirements

- Python 3.9+
- requests
- beautifulsoup4
- selenium
- playwright

## Usage

```python
import asyncio
from scrapalyzer import Scrapalyzer

async def main():
    scrapalyzer = Scrapalyzer()
    
    result = await scrapalyzer.analyze_url("https://example.com")
    print(result)
    
    results = await scrapalyzer.analyze("https://example.com")
    for result in results:
        print(f"URL: {result.url}")
        print(f"Analyzed at: {result.analyzed_at}")
        print(f"Profile: {result.profile}")

asyncio.run(main())
```

## Output Format

The analyzer generates a JSON output containing the analysis results from all sensors:

```python
{
    "url": "https://example.com",
    "status_code": 200,
    "headers": {
        "server": "nginx/1.18.0",
        "content-type": "text/html; charset=utf-8"
    },
    "restrictions": {
        "captcha": {
            "detected": True,
            "type": "reCAPTCHA",
            "confidence": 0.95
        },
        "javascript": {
            "required": True,
            "frameworks": ["React"],
            "confidence": 0.98
        },
        "antibot": {
            "detected": True,
            "protections": ["cloudflare"],
            "confidence": 0.92
        }
    },
    "features": {
        "language": {
            "frontend": ["React", "TypeScript"],
            "backend": ["Python", "Django"]
        },
        "api": {
            "endpoints": ["/api/v1/data"],
            "authentication": "bearer-token"
        },
        "mobile": {
            "responsive": True,
            "mobileSpecificRoutes": False
        }
    },
    "mitigation_strategies": {
        "captcha": "Use 2captcha service",
        "javascript": "Enable JavaScript execution in Playwright",
        "antibot": "Implement request delay and rotation"
    },
    "overall_confidence": 0.95
}
```

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/scrapalyzer.git
cd scrapalyzer
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

3. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT

## Author

Ibrahim Mlata mlata.ibrahim@gmail.com

## Support

For issues and feature requests, please use the GitHub issue tracker.
