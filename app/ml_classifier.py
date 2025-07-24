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

class EnhancedConceptClassifier:
    def __init__(self):
        self.pipeline = None
        self.concepts = [
            'Syntax Error', 'Compilation Error', 'Logic Error',
            'Binary Search', 'Dynamic Programming', 'Graph Traversal',
            'Sorting', 'Array Manipulation', 'String Processing',
            'Tree Algorithms', 'Greedy Algorithm', 'Backtracking',
            'Mathematics', 'General Programming'
        ]
        
    def detect_syntax_errors(self, code):
        """Detect common syntax errors with high priority"""
        errors = []
        
        # C/C++ specific syntax errors
        if any(lang in code.lower() for lang in ['#include', 'using namespace', 'cout', 'cin']):
            # Check for semicolon after #define
            if re.search(r'#define\s+\w+\s+[^;]*;', code):
                errors.append({
                    'type': 'Syntax Error',
                    'issue': 'Semicolon after #define',
                    'confidence': 0.95,
                    'line': self._find_line_with_pattern(code, r'#define.*?;')
                })
            
            # Check for missing semicolons
            cpp_statements = re.findall(r'(cout|cin|return|int|long|char|float|double).*?[^;{}\n]$', code, re.MULTILINE)
            if cpp_statements:
                errors.append({
                    'type': 'Syntax Error',
                    'issue': 'Possibly missing semicolon',
                    'confidence': 0.7,
                    'details': f"Found {len(cpp_statements)} suspicious lines"
                })
        
        # Python specific syntax errors
        elif any(keyword in code for keyword in ['def ', 'import ', 'print(', 'if __name__']):
            # Check for missing colons
            missing_colons = re.findall(r'(if|for|while|def|class|try|except|with|elif|else)\s+[^:\n]*[^:]$', code, re.MULTILINE)
            if missing_colons:
                errors.append({
                    'type': 'Syntax Error',
                    'issue': 'Missing colon after control structure',
                    'confidence': 0.9,
                    'details': f"Found {len(missing_colons)} lines missing colons"
                })
            
            # Check for incorrect indentation patterns
            lines = code.split('\n')
            indentation_errors = self._check_python_indentation(lines)
            if indentation_errors:
                errors.append({
                    'type': 'Syntax Error',
                    'issue': 'Indentation error',
                    'confidence': 0.8,
                    'details': f"Found {len(indentation_errors)} indentation issues"
                })
        
        # Common syntax errors across languages
        # Unmatched brackets/braces
        bracket_errors = self._check_bracket_matching(code)
        if bracket_errors:
            errors.append({
                'type': 'Syntax Error',
                'issue': 'Unmatched brackets/braces',
                'confidence': 0.9,
                'details': bracket_errors
            })
        
        # Check for common typos in keywords
        typo_errors = self._check_keyword_typos(code)
        if typo_errors:
            errors.extend(typo_errors)
        
        return errors
    
    def detect_compilation_errors(self, code):
        """Detect common compilation errors"""
        errors = []
        
        # Undefined variables/functions
        if '#include' in code:  # C/C++
            # Check for missing headers
            if 'vector' in code and '#include <vector>' not in code:
                errors.append({
                    'type': 'Compilation Error',
                    'issue': 'Missing #include <vector>',
                    'confidence': 0.85
                })
            
            if 'sort(' in code and '#include <algorithm>' not in code and '#include <bits/stdc++.h>' not in code:
                errors.append({
                    'type': 'Compilation Error',
                    'issue': 'Missing #include <algorithm> for sort()',
                    'confidence': 0.85
                })
            
            # Check for type mismatches
            if re.search(r'#define\s+int\s+long\s+long', code):
                if re.search(r'int\s+main\s*\(', code):
                    errors.append({
                        'type': 'Compilation Error',
                        'issue': 'Type conflict: #define int long long with int main()',
                        'confidence': 0.9,
                        'suggestion': 'Use signed main() instead of int main()'
                    })
        
        return errors
    
    def detect_logic_errors(self, code):
        """Detect common logic errors"""
        errors = []
        
        # Array bounds issues
        if re.search(r'for\s*\(\s*int\s+\w+\s*=\s*0\s*;\s*\w+\s*<=?\s*n\s*;', code):
            if 'vector<' in code or 'array[' in code:
                errors.append({
                    'type': 'Logic Error',
                    'issue': 'Potential array bounds error (using <= n instead of < n)',
                    'confidence': 0.75
                })
        
        # Off-by-one errors in binary search
        if 'binary' in code.lower() or ('left' in code and 'right' in code and 'mid' in code):
            if re.search(r'mid\s*=\s*\(\s*left\s*\+\s*right\s*\)\s*/\s*2', code):
                errors.append({
                    'type': 'Logic Error',
                    'issue': 'Potential integer overflow in mid calculation',
                    'confidence': 0.7,
                    'suggestion': 'Use mid = left + (right - left) / 2'
                })
        
        return errors
    
    def _find_line_with_pattern(self, code, pattern):
        """Find line number containing a pattern"""
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line):
                return i
        return None
    
    def _check_python_indentation(self, lines):
        """Check for Python indentation errors"""
        errors = []
        expected_indent = 0
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            
            # Calculate current indentation
            current_indent = len(line) - len(line.lstrip())
            
            # Check for control structures that should increase indentation
            if re.search(r'(if|for|while|def|class|try|except|with|elif).*:$', line.strip()):
                expected_indent += 4
            elif line.strip() in ['else:', 'finally:']:
                expected_indent += 4
            elif line.strip().startswith(('except', 'elif')):
                # These should be at the same level as the try/if
                pass
            
            # Check if indentation matches expectation
            if current_indent != expected_indent and line.strip():
                errors.append(f"Line {i+1}: Expected {expected_indent} spaces, got {current_indent}")
        
        return errors
    
    def _check_bracket_matching(self, code):
        """Check for unmatched brackets and braces"""
        stack = []
        pairs = {'(': ')', '[': ']', '{': '}'}
        
        for i, char in enumerate(code):
            if char in pairs:
                stack.append((char, i))
            elif char in pairs.values():
                if not stack:
                    return f"Unmatched closing '{char}' at position {i}"
                
                opening, pos = stack.pop()
                if pairs[opening] != char:
                    return f"Mismatched brackets: '{opening}' at {pos} and '{char}' at {i}"
        
        if stack:
            opening, pos = stack[-1]
            return f"Unmatched opening '{opening}' at position {pos}"
        
        return None
    
    def _check_keyword_typos(self, code):
        """Check for common keyword typos"""
        errors = []
        
        # Common C/C++ typos
        cpp_typos = {
            'inlcude': 'include',
            'reutrn': 'return',
            'unsined': 'unsigned',
            'singned': 'signed',
            'vecotr': 'vector',
            'stirng': 'string'
        }
        
        # Common Python typos
        python_typos = {
            'dfe': 'def',
            'prnit': 'print',
            'improt': 'import',
            'retrun': 'return',
            'fro': 'for'
        }
        
        all_typos = {**cpp_typos, **python_typos}
        
        for typo, correct in all_typos.items():
            if typo in code:
                errors.append({
                    'type': 'Syntax Error',
                    'issue': f"Possible typo: '{typo}' should be '{correct}'",
                    'confidence': 0.8
                })
        
        return errors
    
    def predict_concept(self, code):
        """Enhanced prediction with syntax error priority"""
        try:
            # First, check for syntax errors (highest priority)
            syntax_errors = self.detect_syntax_errors(code)
            if syntax_errors:
                # Return the highest confidence syntax error
                best_error = max(syntax_errors, key=lambda x: x.get('confidence', 0))
                return 'Syntax Error', best_error['confidence']
            
            # Then check for compilation errors
            compilation_errors = self.detect_compilation_errors(code)
            if compilation_errors:
                best_error = max(compilation_errors, key=lambda x: x.get('confidence', 0))
                return 'Compilation Error', best_error['confidence']
            
            # Then check for logic errors
            logic_errors = self.detect_logic_errors(code)
            if logic_errors:
                best_error = max(logic_errors, key=lambda x: x.get('confidence', 0))
                return 'Logic Error', best_error['confidence']
            
            # If no errors found, proceed with algorithmic classification
            if self.pipeline:
                processed_code = self.preprocess_code(code)
                prediction = self.pipeline.predict([processed_code])[0]
                
                try:
                    probabilities = self.pipeline.predict_proba([processed_code])[0]
                    confidence = max(probabilities)
                except:
                    confidence = 0.7
                
                return prediction, confidence
            else:
                return self._rule_based_classification(code), 0.5
                
        except Exception as e:
            logger.error(f"Error in enhanced prediction: {str(e)}")
            return self._rule_based_classification(code), 0.5
    
    def get_detailed_analysis(self, code):
        """Get detailed analysis including all detected issues"""
        analysis = {
            'syntax_errors': self.detect_syntax_errors(code),
            'compilation_errors': self.detect_compilation_errors(code),
            'logic_errors': self.detect_logic_errors(code),
            'concept': None,
            'confidence': 0
        }
        
        # Get primary classification
        concept, confidence = self.predict_concept(code)
        analysis['concept'] = concept
        analysis['confidence'] = confidence
        
        return analysis
    
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
    
    def _rule_based_classification(self, code):
        """Enhanced rule-based classification"""
        code_lower = code.lower()
        
        # Check for specific algorithmic patterns
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

# Global enhanced classifier instance
classifier = EnhancedConceptClassifier()
