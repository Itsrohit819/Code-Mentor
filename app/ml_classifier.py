import os
import re
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score
from app.config import Config
import logging

logger = logging.getLogger(__name__)

class ConceptClassifier:
    def __init__(self):
        self.pipeline = None
        self.concepts = [
            'Binary Search', 'Dynamic Programming', 'Graph Traversal',
            'Sorting', 'Array Manipulation', 'String Processing',
            'Tree Algorithms', 'Greedy Algorithm', 'Backtracking',
            'Mathematics', 'General Programming'
        ]
        
    def preprocess_code(self, code):
        """Clean and preprocess code for feature extraction"""
        # Remove comments
        code = re.sub(r'#.*?$', '', code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
        
        # Remove string literals
        code = re.sub(r'".*?"', 'STRING', code)
        code = re.sub(r"'.*?'", 'STRING', code)
        
        # Normalize whitespace
        code = ' '.join(code.split())
        
        return code.lower()
    
    def extract_features(self, code):
        """Extract programming-specific features from code"""
        features = []
        code_lower = code.lower()
        
        # Keywords and patterns
        patterns = {
            'binary_search': ['binary', 'left', 'right', 'mid', 'while.*<=', 'mid.*=.*(left.*right|right.*left)'],
            'dynamic_programming': ['dp\\[', 'memo', 'cache', 'for.*in.*range', 'previous', 'optimal'],
            'graph': ['dfs', 'bfs', 'graph', 'visited', 'adjacency', 'node', 'edge', 'queue', 'stack'],
            'sorting': ['sort', 'sorted', 'quicksort', 'mergesort', 'heapsort', 'bubble'],
            'array': ['array', 'list', '\\[.*\\]', 'append', 'index', 'length'],
            'string': ['string', 'str', 'char', 'substring', 'split', 'join'],
            'tree': ['tree', 'root', 'left', 'right', 'parent', 'child', 'leaf'],
            'greedy': ['greedy', 'minimum', 'maximum', 'optimal', 'choice'],
            'backtrack': ['backtrack', 'recursive', 'return.*if', 'branch'],
            'math': ['math', 'formula', 'equation', 'calculate', 'sum', 'product']
        }
        
        for concept, pattern_list in patterns.items():
            count = sum(len(re.findall(pattern, code_lower)) for pattern in pattern_list)
            features.append(count)
        
        return features
    
    def create_training_data(self):
        """Create sample training data if none exists"""
        training_samples = [
            ("def binary_search(arr, target):\n    left, right = 0, len(arr)-1\n    while left <= right:\n        mid = (left + right) // 2", "Binary Search"),
            ("dp = [0] * (n+1)\nfor i in range(1, n+1):\n    dp[i] = dp[i-1] + dp[i-2]", "Dynamic Programming"),
            ("def dfs(graph, node, visited):\n    visited.add(node)\n    for neighbor in graph[node]:", "Graph Traversal"),
            ("arr.sort()\nfor i in range(len(arr)):\n    print(arr[i])", "Sorting"),
            ("result = []\nfor i in range(len(arr)):\n    result.append(arr[i] * 2)", "Array Manipulation"),
            ("text = input().strip()\nwords = text.split()\nresult = ' '.join(words)", "String Processing"),
            ("class TreeNode:\n    def __init__(self, val=0):\n        self.val = val\n        self.left = None", "Tree Algorithms"),
            ("total = 0\nfor item in items:\n    if item > threshold:\n        total += item", "Greedy Algorithm"),
            ("def solve(board, row):\n    if row == n:\n        return True\n    for col in range(n):", "Backtracking"),
            ("import math\nresult = math.sqrt(x**2 + y**2)\nprint(f'Distance: {result}')", "Mathematics"),
            ("x = int(input())\ny = int(input())\nprint(x + y)", "General Programming")
        ]
        
        df = pd.DataFrame(training_samples, columns=['code', 'concept'])
        os.makedirs(os.path.dirname(Config.TRAINING_DATA_PATH), exist_ok=True)
        df.to_csv(Config.TRAINING_DATA_PATH, index=False)
        return df
    
    def train_model(self):
        """Train the concept classification model"""
        try:
            # Load or create training data
            if os.path.exists(Config.TRAINING_DATA_PATH):
                df = pd.read_csv(Config.TRAINING_DATA_PATH)
            else:
                df = self.create_training_data()
                
            if len(df) < 5:
                logger.info("Insufficient training data, using rule-based classification")
                return False
            
            # Preprocess code
            df['processed_code'] = df['code'].apply(self.preprocess_code)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                df['processed_code'], df['concept'], 
                test_size=0.2, random_state=42, stratify=df['concept']
            )
            
            # Create pipeline
            self.pipeline = Pipeline([
                ('tfidf', TfidfVectorizer(
                    max_features=5000,
                    ngram_range=(1, 3),
                    stop_words='english',
                    lowercase=True
                )),
                ('classifier', RandomForestClassifier(
                    n_estimators=100,
                    random_state=42,
                    class_weight='balanced'
                ))
            ])
            
            # Train model
            self.pipeline.fit(X_train, y_train)
            
            # Evaluate
            y_pred = self.pipeline.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            logger.info(f"Model trained with accuracy: {accuracy:.2f}")
            
            # Save model
            os.makedirs(os.path.dirname(Config.MODEL_PATH), exist_ok=True)
            joblib.dump(self.pipeline, Config.MODEL_PATH)
            
            return True
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return False
    
    def load_model(self):
        """Load the trained model"""
        try:
            if os.path.exists(Config.MODEL_PATH):
                self.pipeline = joblib.load(Config.MODEL_PATH)
                return True
            else:
                logger.info("No trained model found, training new model...")
                return self.train_model()
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False
    
    def predict_concept(self, code):
        """Predict the programming concept from code"""
        try:
            if not self.pipeline:
                if not self.load_model():
                    return self._rule_based_classification(code), 0.5
            
            processed_code = self.preprocess_code(code)
            prediction = self.pipeline.predict([processed_code])[0]
            
            # Get confidence score
            try:
                probabilities = self.pipeline.predict_proba([processed_code])[0]
                confidence = max(probabilities)
            except:
                confidence = 0.7
            
            return prediction, confidence
            
        except Exception as e:
            logger.error(f"Error in ML prediction: {str(e)}")
            return self._rule_based_classification(code), 0.5
    
    def _rule_based_classification(self, code):
        """Fallback rule-based classification"""
        code_lower = code.lower()
        
        if any(pattern in code_lower for pattern in ['binary', 'left <= right', 'mid =', 'while left <= right']):
            return 'Binary Search'
        elif any(pattern in code_lower for pattern in ['dp[', 'memo', 'dynamic', 'previous']):
            return 'Dynamic Programming'
        elif any(pattern in code_lower for pattern in ['dfs', 'bfs', 'graph', 'visited']):
            return 'Graph Traversal'
        elif any(pattern in code_lower for pattern in ['sort', 'sorted', 'quicksort', 'mergesort']):
            return 'Sorting'
        elif any(pattern in code_lower for pattern in ['tree', 'root', 'left', 'right', 'node']):
            return 'Tree Algorithms'
        elif any(pattern in code_lower for pattern in ['backtrack', 'recursive']):
            return 'Backtracking'
        elif any(pattern in code_lower for pattern in ['greedy', 'minimum', 'maximum']):
            return 'Greedy Algorithm'
        elif any(pattern in code_lower for pattern in ['string', 'str', 'char', 'split']):
            return 'String Processing'
        elif any(pattern in code_lower for pattern in ['math', 'sqrt', 'formula']):
            return 'Mathematics'
        else:
            return 'General Programming'

# Global classifier instance
classifier = ConceptClassifier()
