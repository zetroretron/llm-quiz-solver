"""
Chart Handler - Generate visualizations and encode as base64.
"""
import requests
import json
import re
import pandas as pd
import base64
from io import StringIO, BytesIO
from typing import Optional, Dict, Any, List
import logging

from .base import BaseHandler, TaskContext

logger = logging.getLogger(__name__)


class ChartHandler(BaseHandler):
    """Handler for chart and visualization tasks."""
    
    priority = 35
    
    def can_handle(self, task_type: str, context: TaskContext) -> bool:
        page_lower = context.page_text.lower()
        return (
            'chart' in page_lower or
            'plot' in page_lower or
            'graph' in page_lower or
            'visualization' in page_lower or
            'visualize' in page_lower or
            'base64' in page_lower or
            task_type == 'chart'
        )
    
    async def handle(self, context: TaskContext) -> str:
        logger.info("Processing chart task")
        
        # Download data
        data_url = context.extract_file_url()
        if data_url:
            r = requests.get(data_url)
            if '.csv' in data_url:
                df = pd.read_csv(StringIO(r.text))
            elif '.json' in data_url:
                df = pd.DataFrame(r.json())
            else:
                df = None
        else:
            df = None
        
        # Determine chart type
        page_lower = context.page_text.lower()
        
        if 'bar' in page_lower:
            return await self._create_bar_chart(df, context)
        elif 'line' in page_lower:
            return await self._create_line_chart(df, context)
        elif 'scatter' in page_lower:
            return await self._create_scatter_chart(df, context)
        elif 'pie' in page_lower:
            return await self._create_pie_chart(df, context)
        elif 'histogram' in page_lower or 'hist' in page_lower:
            return await self._create_histogram(df, context)
        else:
            # Default to bar chart
            return await self._create_bar_chart(df, context)
    
    async def _create_bar_chart(self, df: Optional[pd.DataFrame], context: TaskContext) -> str:
        """Create a bar chart."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(10, 6))
            
            if df is not None and len(df.columns) >= 2:
                x_col = df.columns[0]
                y_col = df.columns[1]
                plt.bar(df[x_col].astype(str), df[y_col])
                plt.xlabel(x_col)
                plt.ylabel(y_col)
            else:
                # Create sample chart
                plt.bar(['A', 'B', 'C', 'D'], [10, 20, 15, 25])
            
            plt.title('Bar Chart')
            plt.tight_layout()
            
            return self._fig_to_base64(plt)
            
        except ImportError:
            logger.error("matplotlib not available")
            return "skip"
    
    async def _create_line_chart(self, df: Optional[pd.DataFrame], context: TaskContext) -> str:
        """Create a line chart."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(10, 6))
            
            if df is not None and len(df.columns) >= 2:
                x_col = df.columns[0]
                y_col = df.columns[1]
                plt.plot(df[x_col], df[y_col], marker='o')
                plt.xlabel(x_col)
                plt.ylabel(y_col)
            else:
                plt.plot([1, 2, 3, 4], [10, 20, 15, 25], marker='o')
            
            plt.title('Line Chart')
            plt.tight_layout()
            
            return self._fig_to_base64(plt)
            
        except ImportError:
            logger.error("matplotlib not available")
            return "skip"
    
    async def _create_scatter_chart(self, df: Optional[pd.DataFrame], context: TaskContext) -> str:
        """Create a scatter plot."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(10, 6))
            
            if df is not None and len(df.columns) >= 2:
                x_col = df.columns[0]
                y_col = df.columns[1]
                plt.scatter(df[x_col], df[y_col])
                plt.xlabel(x_col)
                plt.ylabel(y_col)
            else:
                plt.scatter([1, 2, 3, 4], [10, 20, 15, 25])
            
            plt.title('Scatter Plot')
            plt.tight_layout()
            
            return self._fig_to_base64(plt)
            
        except ImportError:
            logger.error("matplotlib not available")
            return "skip"
    
    async def _create_pie_chart(self, df: Optional[pd.DataFrame], context: TaskContext) -> str:
        """Create a pie chart."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(10, 6))
            
            if df is not None and len(df.columns) >= 2:
                labels = df.iloc[:, 0].astype(str)
                values = df.iloc[:, 1]
                plt.pie(values, labels=labels, autopct='%1.1f%%')
            else:
                plt.pie([30, 20, 25, 25], labels=['A', 'B', 'C', 'D'], autopct='%1.1f%%')
            
            plt.title('Pie Chart')
            plt.tight_layout()
            
            return self._fig_to_base64(plt)
            
        except ImportError:
            logger.error("matplotlib not available")
            return "skip"
    
    async def _create_histogram(self, df: Optional[pd.DataFrame], context: TaskContext) -> str:
        """Create a histogram."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(10, 6))
            
            if df is not None:
                # Use first numeric column
                numeric_cols = df.select_dtypes(include='number').columns
                if len(numeric_cols) > 0:
                    plt.hist(df[numeric_cols[0]], bins=20, edgecolor='black')
                    plt.xlabel(numeric_cols[0])
                else:
                    plt.hist([1, 2, 2, 3, 3, 3, 4, 4, 5], bins=5, edgecolor='black')
            else:
                plt.hist([1, 2, 2, 3, 3, 3, 4, 4, 5], bins=5, edgecolor='black')
            
            plt.ylabel('Frequency')
            plt.title('Histogram')
            plt.tight_layout()
            
            return self._fig_to_base64(plt)
            
        except ImportError:
            logger.error("matplotlib not available")
            return "skip"
    
    def _fig_to_base64(self, plt) -> str:
        """Convert matplotlib figure to base64 data URI."""
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"
