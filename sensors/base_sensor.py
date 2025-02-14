from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseSensor(ABC):
    """Base class for all website restriction sensors."""
    
    def __init__(self):
        self.name = self.__class__.__name__
        
    @abstractmethod
    async def detect(self, response: Any, **kwargs) -> Dict[str, Any]:
        """
        Detect specific restrictions on the website.
        
        Args:
            response: The HTTP response or page content to analyze
            **kwargs: Additional parameters needed for detection
            
        Returns:
            Dict containing detection results and metadata
        """
        pass
    
    @abstractmethod
    def get_mitigation_strategy(self) -> Dict[str, Any]:
        """
        Provide strategy to handle detected restrictions.
        
        Returns:
            Dict containing mitigation steps and configuration
        """
        pass
