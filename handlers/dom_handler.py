"""
DOM Handler - Extract data from JavaScript-rendered pages.
"""
import re
import json
from typing import Optional, List, Dict, Any
import logging

from .base import BaseHandler, TaskContext

logger = logging.getLogger(__name__)


class DOMHandler(BaseHandler):
    """Handler for DOM extraction tasks from JS-rendered pages."""
    
    priority = 25
    
    def can_handle(self, task_type: str, context: TaskContext) -> bool:
        page_lower = context.page_text.lower()
        return (
            'dom' in page_lower or
            'javascript' in page_lower or
            'innerhtml' in page_lower or
            'queryselector' in page_lower or
            'atob' in page_lower or
            'rendered' in page_lower or
            task_type == 'dom'
        )
    
    async def handle(self, context: TaskContext) -> str:
        logger.info("Processing DOM task")
        
        # The page is already rendered by Playwright
        # We just need to extract the required data
        
        page_lower = context.page_text.lower()
        
        # Check for specific extraction patterns
        if 'table' in page_lower:
            return self._extract_table(context)
        elif 'list' in page_lower:
            return self._extract_list(context)
        elif 'text' in page_lower:
            return self._extract_text(context)
        elif 'count' in page_lower:
            return self._count_elements(context)
        else:
            # Return the main content
            return self._extract_main_content(context)
    
    def _extract_table(self, context: TaskContext) -> str:
        """Extract table data from HTML."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(context.html_content, 'html.parser')
        tables = soup.find_all('table')
        
        result = []
        for table in tables:
            rows = []
            for tr in table.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            
            if rows:
                # Convert to dict format
                if len(rows) > 1:
                    headers = rows[0]
                    for row in rows[1:]:
                        row_dict = {}
                        for i, cell in enumerate(row):
                            if i < len(headers):
                                row_dict[headers[i]] = cell
                        result.append(row_dict)
        
        return json.dumps(result)
    
    def _extract_list(self, context: TaskContext) -> str:
        """Extract list items from HTML."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(context.html_content, 'html.parser')
        
        items = []
        for li in soup.find_all('li'):
            items.append(li.get_text(strip=True))
        
        return json.dumps(items)
    
    def _extract_text(self, context: TaskContext) -> str:
        """Extract main text content."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(context.html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()
        
        text = soup.get_text(separator=' ', strip=True)
        return text
    
    def _count_elements(self, context: TaskContext) -> str:
        """Count specific elements in the DOM."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(context.html_content, 'html.parser')
        
        # Determine what to count
        page_lower = context.page_text.lower()
        
        if 'div' in page_lower:
            return str(len(soup.find_all('div')))
        elif 'span' in page_lower:
            return str(len(soup.find_all('span')))
        elif 'link' in page_lower or 'a' in page_lower:
            return str(len(soup.find_all('a')))
        elif 'image' in page_lower or 'img' in page_lower:
            return str(len(soup.find_all('img')))
        else:
            # Count all elements
            return str(len(soup.find_all()))
    
    def _extract_main_content(self, context: TaskContext) -> str:
        """Extract the main content area."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(context.html_content, 'html.parser')
        
        # Look for common content containers
        for selector in ['main', 'article', '#content', '.content', '#result', '.result']:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        # Fallback to body
        body = soup.find('body')
        if body:
            for script in body(['script', 'style']):
                script.decompose()
            return body.get_text(strip=True)
        
        return context.page_text
