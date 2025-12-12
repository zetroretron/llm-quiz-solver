"""
PDF Handler - Extract tables, text, and calculate values from PDFs.
"""
import requests
import pandas as pd
import re
from io import BytesIO
from typing import Optional, List, Dict, Any
import logging

from .base import BaseHandler, TaskContext

logger = logging.getLogger(__name__)


class PDFHandler(BaseHandler):
    """Handler for PDF processing tasks."""
    
    priority = 15
    
    def can_handle(self, task_type: str, context: TaskContext) -> bool:
        page_lower = context.page_text.lower()
        return (
            '.pdf' in page_lower or 
            'invoice' in page_lower or
            ('sum' in page_lower and 'table' in page_lower) or
            task_type == 'pdf'
        )
    
    async def handle(self, context: TaskContext) -> str:
        logger.info("Processing PDF task")
        
        # Find PDF URL
        pdf_url = context.extract_file_url() or self._find_pdf_url(context)
        if not pdf_url:
            raise ValueError("No PDF URL found")
        
        # Download PDF
        r = requests.get(pdf_url)
        
        # Try pdfplumber first (better for tables)
        try:
            import pdfplumber
            return await self._process_with_pdfplumber(r.content, context)
        except ImportError:
            logger.warning("pdfplumber not available, trying PyMuPDF")
        
        # Fallback to PyMuPDF
        try:
            import fitz  # PyMuPDF
            return await self._process_with_pymupdf(r.content, context)
        except ImportError:
            logger.warning("PyMuPDF not available")
        
        raise ImportError("No PDF library available (need pdfplumber or PyMuPDF)")
    
    async def _process_with_pdfplumber(self, pdf_bytes: bytes, context: TaskContext) -> str:
        """Process PDF using pdfplumber."""
        import pdfplumber
        
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            all_tables = []
            all_text = []
            
            for page in pdf.pages:
                # Extract tables
                tables = page.extract_tables()
                if tables:
                    all_tables.extend(tables)
                
                # Extract text
                text = page.extract_text()
                if text:
                    all_text.append(text)
            
            # Determine what calculation is needed
            page_lower = context.page_text.lower()
            
            if 'sum' in page_lower and ('quantity' in page_lower or 'unitprice' in page_lower or 'price' in page_lower):
                return self._calculate_invoice_total(all_tables)
            elif 'sum' in page_lower:
                return self._calculate_sum(all_tables, context)
            elif 'count' in page_lower:
                return self._calculate_count(all_tables, context)
            else:
                # Return extracted text
                return '\n'.join(all_text)
    
    async def _process_with_pymupdf(self, pdf_bytes: bytes, context: TaskContext) -> str:
        """Process PDF using PyMuPDF."""
        import fitz
        
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        all_text = []
        
        for page in doc:
            all_text.append(page.get_text())
        
        return '\n'.join(all_text)
    
    def _calculate_invoice_total(self, tables: List[List[List[str]]]) -> str:
        """Calculate sum(Quantity * UnitPrice) from invoice tables."""
        total = 0.0
        
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            # First row is header
            headers = [str(h).lower().strip() if h else '' for h in table[0]]
            
            # Find quantity and price columns
            qty_idx = None
            price_idx = None
            
            for i, h in enumerate(headers):
                if 'qty' in h or 'quantity' in h:
                    qty_idx = i
                elif 'price' in h or 'unit' in h or 'amount' in h:
                    price_idx = i
            
            if qty_idx is None or price_idx is None:
                # Try numeric columns
                continue
            
            # Calculate sum
            for row in table[1:]:
                try:
                    qty = float(re.sub(r'[^\d.]', '', str(row[qty_idx] or '0')))
                    price = float(re.sub(r'[^\d.]', '', str(row[price_idx] or '0')))
                    total += qty * price
                except (ValueError, IndexError):
                    continue
        
        return str(round(total, 2))
    
    def _calculate_sum(self, tables: List[List[List[str]]], context: TaskContext) -> str:
        """Calculate sum of a specific column."""
        # Find column name from context
        col_match = re.search(r'sum of[:\s]+["\']?(\w+)["\']?', context.page_text, re.IGNORECASE)
        target_col = col_match.group(1).lower() if col_match else 'value'
        
        total = 0.0
        
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            headers = [str(h).lower().strip() if h else '' for h in table[0]]
            
            # Find target column
            col_idx = None
            for i, h in enumerate(headers):
                if target_col in h:
                    col_idx = i
                    break
            
            if col_idx is None:
                continue
            
            for row in table[1:]:
                try:
                    val = float(re.sub(r'[^\d.]', '', str(row[col_idx] or '0')))
                    total += val
                except (ValueError, IndexError):
                    continue
        
        return str(round(total, 2))
    
    def _calculate_count(self, tables: List[List[List[str]]], context: TaskContext) -> str:
        """Count rows in tables."""
        count = 0
        for table in tables:
            if table and len(table) > 1:
                count += len(table) - 1  # Exclude header
        return str(count)
    
    def _find_pdf_url(self, context: TaskContext) -> Optional[str]:
        """Find PDF URL in page content."""
        patterns = [
            r'href=["\']([^"\']+\.pdf)["\']',
            r'(/project2/[^\s"\'<>]+\.pdf)',
            r'(https?://[^\s"\'<>]+\.pdf)',
        ]
        
        for p in patterns:
            match = re.search(p, context.page_text + context.html_content, re.IGNORECASE)
            if match:
                url = match.group(1)
                if not url.startswith('http'):
                    url = context.base_url + url
                return url
        return None
