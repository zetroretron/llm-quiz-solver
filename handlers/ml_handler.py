"""
ML Handler - Machine learning tasks including training, prediction, and metrics.
"""
import requests
import json
import re
import pandas as pd
from io import StringIO
from typing import Optional, Dict, Any, List
import logging

from .base import BaseHandler, TaskContext

logger = logging.getLogger(__name__)


class MLHandler(BaseHandler):
    """Handler for machine learning tasks."""
    
    priority = 30
    
    def can_handle(self, task_type: str, context: TaskContext) -> bool:
        page_lower = context.page_text.lower()
        return (
            'predict' in page_lower or
            'model' in page_lower or
            'train' in page_lower or
            'regression' in page_lower or
            'classification' in page_lower or
            'f1' in page_lower or
            'accuracy' in page_lower or
            'weather' in page_lower or
            'forecast' in page_lower or
            task_type in ['ml', 'weather_ml', 'f1']
        )
    
    async def handle(self, context: TaskContext) -> str:
        logger.info("Processing ML task")
        
        # Download data
        data_url = context.extract_file_url()
        if not data_url:
            raise ValueError("No data file found for ML task")
        
        r = requests.get(data_url)
        
        if '.csv' in data_url:
            df = pd.read_csv(StringIO(r.text))
        elif '.json' in data_url:
            df = pd.DataFrame(r.json())
        else:
            raise ValueError(f"Unknown data format: {data_url}")
        
        page_lower = context.page_text.lower()
        
        # Determine task type
        if 'f1' in page_lower:
            return await self._calculate_f1(df, context)
        elif 'accuracy' in page_lower:
            return await self._calculate_accuracy(df, context)
        elif 'predict' in page_lower:
            return await self._make_prediction(df, context)
        elif 'train' in page_lower:
            return await self._train_and_evaluate(df, context)
        else:
            return await self._train_and_evaluate(df, context)
    
    async def _calculate_f1(self, df: pd.DataFrame, context: TaskContext) -> str:
        """Calculate F1 score from predictions."""
        try:
            from sklearn.metrics import f1_score
            
            # Find prediction and actual columns
            y_true = None
            y_pred = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'actual' in col_lower or 'true' in col_lower or 'label' in col_lower:
                    y_true = df[col]
                elif 'predict' in col_lower or 'pred' in col_lower:
                    y_pred = df[col]
            
            if y_true is None or y_pred is None:
                # Assume first two columns
                y_true = df.iloc[:, 0]
                y_pred = df.iloc[:, 1]
            
            # Calculate F1
            f1 = f1_score(y_true, y_pred, average='weighted')
            return str(round(f1, 4))
            
        except ImportError:
            logger.error("scikit-learn not available")
            raise
    
    async def _calculate_accuracy(self, df: pd.DataFrame, context: TaskContext) -> str:
        """Calculate accuracy from predictions."""
        try:
            from sklearn.metrics import accuracy_score
            
            y_true = None
            y_pred = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'actual' in col_lower or 'true' in col_lower or 'label' in col_lower:
                    y_true = df[col]
                elif 'predict' in col_lower or 'pred' in col_lower:
                    y_pred = df[col]
            
            if y_true is None or y_pred is None:
                y_true = df.iloc[:, 0]
                y_pred = df.iloc[:, 1]
            
            acc = accuracy_score(y_true, y_pred)
            return str(round(acc, 4))
            
        except ImportError:
            logger.error("scikit-learn not available")
            raise
    
    async def _make_prediction(self, df: pd.DataFrame, context: TaskContext) -> str:
        """Make predictions using a trained model."""
        try:
            from sklearn.linear_model import LinearRegression, LogisticRegression
            from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
            from sklearn.model_selection import train_test_split
            
            # Determine target column
            target_col = self._find_target_column(df, context)
            feature_cols = [c for c in df.columns if c != target_col]
            
            X = df[feature_cols]
            y = df[target_col]
            
            # Handle non-numeric features
            X = pd.get_dummies(X)
            
            # Determine if classification or regression
            page_lower = context.page_text.lower()
            is_classification = (
                'class' in page_lower or 
                'category' in page_lower or
                y.dtype == 'object' or
                y.nunique() < 10
            )
            
            # Train model
            if is_classification:
                model = RandomForestClassifier(n_estimators=100, random_state=42)
            else:
                model = RandomForestRegressor(n_estimators=100, random_state=42)
            
            # Fit on all data (for prediction task)
            model.fit(X, y)
            
            # Make predictions on test data if provided
            # Otherwise return the last prediction
            predictions = model.predict(X)
            
            if is_classification:
                return str(int(predictions[-1]))
            else:
                return str(round(float(predictions[-1]), 2))
            
        except ImportError:
            logger.error("scikit-learn not available")
            raise
    
    async def _train_and_evaluate(self, df: pd.DataFrame, context: TaskContext) -> str:
        """Train a model and return evaluation metrics."""
        try:
            from sklearn.linear_model import LinearRegression, LogisticRegression
            from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import mean_squared_error, accuracy_score, f1_score
            import numpy as np
            
            target_col = self._find_target_column(df, context)
            feature_cols = [c for c in df.columns if c != target_col]
            
            X = df[feature_cols]
            y = df[target_col]
            X = pd.get_dummies(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            page_lower = context.page_text.lower()
            is_classification = (
                'class' in page_lower or 
                y.dtype == 'object' or
                y.nunique() < 10
            )
            
            if is_classification:
                model = RandomForestClassifier(n_estimators=100, random_state=42)
                model.fit(X_train, y_train)
                predictions = model.predict(X_test)
                
                if 'f1' in page_lower:
                    score = f1_score(y_test, predictions, average='weighted')
                else:
                    score = accuracy_score(y_test, predictions)
            else:
                model = RandomForestRegressor(n_estimators=100, random_state=42)
                model.fit(X_train, y_train)
                predictions = model.predict(X_test)
                
                if 'rmse' in page_lower:
                    score = np.sqrt(mean_squared_error(y_test, predictions))
                else:
                    score = mean_squared_error(y_test, predictions)
            
            return str(round(score, 4))
            
        except ImportError:
            logger.error("scikit-learn not available")
            raise
    
    def _find_target_column(self, df: pd.DataFrame, context: TaskContext) -> str:
        """Find the target column for ML tasks."""
        # Check context for hints
        target_match = re.search(
            r'predict\s+["\']?(\w+)["\']?', 
            context.page_text, 
            re.IGNORECASE
        )
        if target_match:
            target = target_match.group(1)
            if target in df.columns:
                return target
        
        # Common target column names
        for col in df.columns:
            col_lower = col.lower()
            if any(t in col_lower for t in ['target', 'label', 'class', 'y', 'output']):
                return col
        
        # Default to last column
        return df.columns[-1]
