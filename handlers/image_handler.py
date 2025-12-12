"""
Image Handler - Process images for color analysis, OCR, and feature extraction.
"""
import requests
import re
from io import BytesIO
from typing import Optional, Dict, Tuple
from collections import Counter
import logging

from .base import BaseHandler, TaskContext

logger = logging.getLogger(__name__)


class ImageHandler(BaseHandler):
    """Handler for image processing tasks."""
    
    priority = 20
    
    def can_handle(self, task_type: str, context: TaskContext) -> bool:
        page_lower = context.page_text.lower()
        return (
            'heatmap' in page_lower or
            'most frequent' in page_lower or
            'rgb color' in page_lower or
            'dominant color' in page_lower or
            'hex' in page_lower or
            any(ext in page_lower for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']) or
            task_type == 'image'
        )
    
    async def handle(self, context: TaskContext) -> str:
        logger.info("Processing image task")
        
        page_lower = context.page_text.lower()
        
        # Check for image diff task (before/after comparison)
        if 'before' in page_lower and 'after' in page_lower and 'differ' in page_lower:
            return await self._compare_images(context)
        
        # Find image URL
        image_url = self._find_image_url(context)
        if not image_url:
            logger.warning("No image URL found")
            return "skip"
        
        # Download image
        r = requests.get(image_url)
        
        # Determine task type
        if 'color' in page_lower or 'rgb' in page_lower or 'hex' in page_lower:
            return await self._analyze_colors(r.content, context)
        elif 'text' in page_lower or 'ocr' in page_lower:
            return await self._extract_text(r.content)
        else:
            # Default to color analysis
            return await self._analyze_colors(r.content, context)
    
    async def _compare_images(self, context: TaskContext) -> str:
        """Compare two images and count differing pixels."""
        try:
            from PIL import Image
            import numpy as np
            
            # Find both image URLs
            before_url = None
            after_url = None
            
            patterns = [
                (r'/project2/before\.png', 'before'),
                (r'/project2/after\.png', 'after'),
            ]
            
            for pattern, img_type in patterns:
                match = re.search(pattern, context.page_text + context.html_content, re.IGNORECASE)
                if match:
                    url = context.base_url + match.group(0)
                    if img_type == 'before':
                        before_url = url
                    else:
                        after_url = url
            
            if not before_url:
                before_url = f"{context.base_url}/project2/before.png"
            if not after_url:
                after_url = f"{context.base_url}/project2/after.png"
            
            logger.info(f"Comparing: {before_url} vs {after_url}")
            
            # Download both images
            r1 = requests.get(before_url)
            r2 = requests.get(after_url)
            
            # Load as RGB arrays
            img1 = Image.open(BytesIO(r1.content)).convert('RGB')
            img2 = Image.open(BytesIO(r2.content)).convert('RGB')
            
            arr1 = np.array(img1)
            arr2 = np.array(img2)
            
            # Compare pixel-by-pixel: count where ANY channel differs
            diff = (arr1 != arr2).any(axis=2)
            count = int(diff.sum())
            
            logger.info(f"Differing pixels: {count}")
            return str(count)
            
        except Exception as e:
            logger.error(f"Image comparison failed: {e}")
            return "skip"
    
    async def _analyze_colors(self, image_bytes: bytes, context: TaskContext) -> str:
        """Analyze image colors and return most frequent/dominant color."""
        try:
            from PIL import Image
            
            img = Image.open(BytesIO(image_bytes))
            img = img.convert('RGB')
            
            # Get all pixels
            pixels = list(img.getdata())
            
            # Count colors
            color_counts = Counter(pixels)
            
            # Get most common color
            most_common = color_counts.most_common(1)[0][0]
            
            # Format as hex
            hex_color = '#{:02x}{:02x}{:02x}'.format(*most_common)
            
            logger.info(f"Most frequent color: {hex_color}")
            return hex_color
            
        except ImportError:
            logger.warning("PIL not available, trying OpenCV")
            return await self._analyze_colors_opencv(image_bytes, context)
    
    async def _analyze_colors_opencv(self, image_bytes: bytes, context: TaskContext) -> str:
        """Analyze colors using OpenCV."""
        try:
            import cv2
            import numpy as np
            
            # Decode image
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Reshape to list of pixels
            pixels = img.reshape(-1, 3)
            
            # Count colors (approximate by rounding)
            rounded = (pixels // 1) * 1  # No rounding, keep exact
            unique, counts = np.unique(rounded, axis=0, return_counts=True)
            
            # Get most common
            most_common_idx = np.argmax(counts)
            bgr = unique[most_common_idx]
            
            # Convert BGR to RGB and format as hex
            rgb = bgr[::-1]  # BGR to RGB
            hex_color = '#{:02x}{:02x}{:02x}'.format(*rgb)
            
            return hex_color
            
        except ImportError:
            logger.error("Neither PIL nor OpenCV available")
            return "skip"
    
    async def _extract_text(self, image_bytes: bytes) -> str:
        """Extract text from image using OCR."""
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(BytesIO(image_bytes))
            text = pytesseract.image_to_string(img)
            return text.strip()
            
        except ImportError:
            logger.warning("pytesseract not available")
            return "skip"
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return "skip"
    
    def _find_image_url(self, context: TaskContext) -> Optional[str]:
        """Find image URL in page content."""
        patterns = [
            r'href=["\']([^"\']+\.(?:png|jpg|jpeg|gif|bmp))["\']',
            r'src=["\']([^"\']+\.(?:png|jpg|jpeg|gif|bmp))["\']',
            r'(/project2/[^\s"\'<>]+\.(?:png|jpg|jpeg|gif|bmp))',
            r'(https?://[^\s"\'<>]+\.(?:png|jpg|jpeg|gif|bmp))',
        ]
        
        for p in patterns:
            match = re.search(p, context.page_text + context.html_content, re.IGNORECASE)
            if match:
                url = match.group(1)
                if not url.startswith('http'):
                    url = context.base_url + url
                return url
        return None
