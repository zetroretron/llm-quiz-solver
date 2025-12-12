"""
Diff Handler - Compare files and find differences.
"""
import requests
import json
import re
import difflib
from typing import Optional, List, Dict, Any
import logging

from .base import BaseHandler, TaskContext

logger = logging.getLogger(__name__)


class DiffHandler(BaseHandler):
    """Handler for file comparison and diff tasks."""
    
    priority = 35
    
    def can_handle(self, task_type: str, context: TaskContext) -> bool:
        page_lower = context.page_text.lower()
        return (
            'diff' in page_lower or
            'compare' in page_lower or
            'difference' in page_lower or
            'changed' in page_lower or
            task_type == 'diff'
        )
    
    async def handle(self, context: TaskContext) -> str:
        logger.info("Processing diff task")
        
        # Get all file URLs
        file_urls = context.extract_all_file_urls()
        
        if len(file_urls) < 2:
            raise ValueError("Need at least 2 files to compare")
        
        # Download files
        files = []
        for url in file_urls[:2]:  # Compare first two
            r = requests.get(url)
            files.append(r.text)
        
        page_lower = context.page_text.lower()
        
        if 'line' in page_lower and 'count' in page_lower:
            return self._count_diff_lines(files[0], files[1])
        elif 'changed' in page_lower:
            return self._get_changed_lines(files[0], files[1])
        elif 'added' in page_lower:
            return self._get_added_lines(files[0], files[1])
        elif 'removed' in page_lower or 'deleted' in page_lower:
            return self._get_removed_lines(files[0], files[1])
        else:
            return self._get_unified_diff(files[0], files[1])
    
    def _count_diff_lines(self, file1: str, file2: str) -> str:
        """Count the number of different lines."""
        lines1 = file1.splitlines()
        lines2 = file2.splitlines()
        
        diff = list(difflib.unified_diff(lines1, lines2, lineterm=''))
        
        # Count lines that start with + or - (excluding headers)
        count = sum(1 for line in diff[2:] if line.startswith(('+', '-')) and not line.startswith(('+++', '---')))
        
        return str(count)
    
    def _get_changed_lines(self, file1: str, file2: str) -> str:
        """Get lines that changed between files."""
        lines1 = file1.splitlines()
        lines2 = file2.splitlines()
        
        diff = list(difflib.unified_diff(lines1, lines2, lineterm=''))
        
        changed = []
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                changed.append(line[1:])
            elif line.startswith('-') and not line.startswith('---'):
                changed.append(line[1:])
        
        return json.dumps(changed)
    
    def _get_added_lines(self, file1: str, file2: str) -> str:
        """Get lines added in file2."""
        lines1 = file1.splitlines()
        lines2 = file2.splitlines()
        
        diff = list(difflib.unified_diff(lines1, lines2, lineterm=''))
        
        added = []
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                added.append(line[1:])
        
        return json.dumps(added)
    
    def _get_removed_lines(self, file1: str, file2: str) -> str:
        """Get lines removed from file1."""
        lines1 = file1.splitlines()
        lines2 = file2.splitlines()
        
        diff = list(difflib.unified_diff(lines1, lines2, lineterm=''))
        
        removed = []
        for line in diff:
            if line.startswith('-') and not line.startswith('---'):
                removed.append(line[1:])
        
        return json.dumps(removed)
    
    def _get_unified_diff(self, file1: str, file2: str) -> str:
        """Get unified diff output."""
        lines1 = file1.splitlines()
        lines2 = file2.splitlines()
        
        diff = difflib.unified_diff(lines1, lines2, lineterm='')
        return '\n'.join(diff)
