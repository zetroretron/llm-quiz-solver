"""
Base Handler Class for Quiz Solver v2.0
All task handlers inherit from this base class.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class TaskContext:
    """Context object passed to handlers containing all task information."""
    current_url: str
    page_text: str
    html_content: str
    email: str
    secret: str
    submission_url: str
    base_url: str = "https://tds-llm-analysis.s-anand.net"
    
    def extract_file_url(self, pattern: str = None) -> Optional[str]:
        """Extract file URL from page text."""
        if pattern:
            match = re.search(pattern, self.page_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Generic file URL patterns
        patterns = [
            r'href=["\']([^"\']+\.(?:csv|json|pdf|zip|xlsx|txt|png|jpg|jpeg|gif|mp3|wav|opus))["\']',
            r'download\s+([^\s]+\.(?:csv|json|pdf|zip|xlsx|txt|png|jpg|jpeg|gif|mp3|wav|opus))',
            r'(/project2/[^\s"\'<>]+\.(?:csv|json|pdf|zip|xlsx|txt|png|jpg|jpeg|gif|mp3|wav|opus))',
        ]
        
        for p in patterns:
            match = re.search(p, self.page_text + self.html_content, re.IGNORECASE)
            if match:
                url = match.group(1)
                if not url.startswith('http'):
                    url = self.base_url + url
                return url
        return None
    
    def extract_all_file_urls(self) -> List[str]:
        """Extract all file URLs from page."""
        urls = []
        patterns = [
            r'href=["\']([^"\']+\.(?:csv|json|pdf|zip|xlsx|txt|png|jpg|jpeg|gif|mp3|wav|opus))["\']',
            r'(/project2/[^\s"\'<>]+\.(?:csv|json|pdf|zip|xlsx|txt|png|jpg|jpeg|gif|mp3|wav|opus))',
        ]
        
        for p in patterns:
            matches = re.findall(p, self.page_text + self.html_content, re.IGNORECASE)
            for url in matches:
                if not url.startswith('http'):
                    url = self.base_url + url
                if url not in urls:
                    urls.append(url)
        return urls


class BaseHandler(ABC):
    """Abstract base class for all task handlers."""
    
    # Priority for handler selection (lower = higher priority)
    priority: int = 100
    
    @abstractmethod
    def can_handle(self, task_type: str, context: TaskContext) -> bool:
        """Check if this handler can process the given task type."""
        pass
    
    @abstractmethod
    async def handle(self, context: TaskContext) -> str:
        """
        Process the task and return the answer.
        
        Returns:
            str: The answer to submit
            
        Raises:
            Exception: If handler fails (will trigger fallback)
        """
        pass
    
    def get_name(self) -> str:
        """Get handler name for logging."""
        return self.__class__.__name__
    
    async def safe_handle(self, context: TaskContext) -> Optional[str]:
        """
        Safely execute handler with error catching.
        Returns None on failure instead of raising.
        """
        try:
            logger.info(f"🔧 {self.get_name()}: Attempting to handle task")
            result = await self.handle(context)
            logger.info(f"✅ {self.get_name()}: Success - Answer: {str(result)[:100]}...")
            return result
        except Exception as e:
            logger.error(f"❌ {self.get_name()}: Failed - {e}")
            return None


class HandlerRegistry:
    """Registry for all task handlers with automatic selection."""
    
    def __init__(self):
        self.handlers: List[BaseHandler] = []
    
    def register(self, handler: BaseHandler):
        """Register a handler."""
        self.handlers.append(handler)
        # Sort by priority
        self.handlers.sort(key=lambda h: h.priority)
    
    def get_handler(self, task_type: str, context: TaskContext) -> Optional[BaseHandler]:
        """Get the first handler that can process the task."""
        for handler in self.handlers:
            if handler.can_handle(task_type, context):
                return handler
        return None
    
    def get_all_handlers(self, task_type: str, context: TaskContext) -> List[BaseHandler]:
        """Get all handlers that can process the task (for fallback chain)."""
        return [h for h in self.handlers if h.can_handle(task_type, context)]
