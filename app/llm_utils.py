import os
import time
import logging
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import Config

logger = logging.getLogger(__name__)

class EnhancedLLMSuggestionEngine:
    def __init__(self):
        self.llm = None
        self.chain = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM and chain"""
        try:
            if not Config.OPENAI_API_KEY:
                logger.warning("OpenAI API key not found, LLM suggestions disabled")
                return
            
            self.llm = ChatOpenAI(
                api_key=Config.OPENAI_API_KEY,
                model="gpt-3.5-turbo",
                temperature=0.2,
                max_tokens=500
            )
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert competitive programming mentor and debugging assistant. 
                 Analyze code issues with precision and provide specific, actionable fixes.
                 Focus on the most critical issue first, especially syntax and compilation errors."""),
                ("human", """
                Code:
                ```
                {code}
                ```
                
                Error/Issue: {error}
                Detected Issue Type: {concept}
                Confidence: {confidence}%
                
                Please provide:
                1. **Root Cause**: What exactly is wrong
                2. **Fix**: Specific code correction needed
                3. **Explanation**: Why this error occurs
                4. **Prevention**: How to avoid this in future
                
                Be concise and focus on the primary issue.
                """)
            ])
            
            # Create chain
            output_parser = StrOutputParser()
            self.chain = prompt | self.llm | output_parser
            
            logger.info("Enhanced LLM initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            self.llm = None
            self.chain = None
    
    def get_suggestion(self, code: str, error: str, concept: str, language: str = "cpp", confidence: float = 0.5) -> Dict[str, Any]:
        """Get intelligent suggestion from LLM with error type awareness"""
        start_time = time.time()
        
        try:
            if not self.chain:
                return self._enhanced_fallback_suggestion(concept, error, code)
            
            # Truncate code if too long
            if len(code) > 2000:
                code = code[:2000] + "\n... (truncated)"
            
            # Get suggestion from LLM
            suggestion = self.chain.invoke({
                "code": code,
                "error": error or "No specific error provided",
                "concept": concept,
                "language": language,
                "confidence": int(confidence * 100)
            })
            
            processing_time = time.time() - start_time
            
            return {
                "suggestion": suggestion.strip(),
                "source": "llm",
                "processing_time": processing_time,
                "success": True,
                "error_type": concept
            }
            
        except Exception as e:
            logger.error(f"LLM suggestion failed: {str(e)}")
            return self._enhanced_fallback_suggestion(concept, error, code)
    
    def _enhanced_fallback_suggestion(self, concept: str, error: str, code: str) -> Dict[str, Any]:
        """Enhanced fallback suggestions with error-specific advice"""
        
        # Error-specific suggestions
        error_suggestions = {
            "Syntax Error": {
                "suggestion": self._get_syntax_error_suggestion(code),
                "tip": "💡 Always check for missing semicolons, brackets, and typos in keywords!"
            },
            "Compilation Error": {
                "suggestion": self._get_compilation_error_suggestion(code),
                "tip": "💡 Make sure all required headers are included and types match!"
            },
            "Logic Error": {
                "suggestion": self._get_logic_error_suggestion(code),
                "tip": "💡 Test with small inputs and trace through your algorithm step by step!"
            }
        }
        
        # Algorithmic suggestions (existing ones)
        algorithmic_suggestions = {
            "Binary Search": {
                "suggestion": "**Binary Search Issues:**\n• Check loop condition (left <= right vs left < right)\n• Use `mid = left + (right - left) / 2` to prevent overflow\n• Ensure array is sorted before searching\n• Handle edge cases: empty array, single element\n• Verify search condition logic",
                "tip": "💡 Always verify your array is sorted before binary search!"
            },
            "Dynamic Programming": {
                "suggestion": "**DP Debugging Checklist:**\n• Verify base cases are correct\n• Check state transitions and recurrence relation\n• Ensure you're not accessing out-of-bounds indices\n• Consider bottom-up vs top-down approach\n• Check if you need 1D or 2D DP array",
                "tip": "💡 Draw out small examples to verify your DP logic!"
            },
            # ... (keep existing algorithmic suggestions)
        }
        
        # Get appropriate suggestion
        if concept in error_suggestions:
            concept_info = error_suggestions[concept]
        else:
            concept_info = algorithmic_suggestions.get(concept, {
                "suggestion": "**General Debugging:**\n• Add debug prints to trace execution\n• Test with simple inputs first\n• Check variable types and values\n• Verify logic step by step\n• Consider edge cases",
                "tip": "💡 Break down complex problems into smaller parts!"
            })
        
        full_suggestion = concept_info['suggestion']
        
        if error and error.strip():
            full_suggestion = f"**Error Analysis:** {error}\n\n{full_suggestion}"
        
        full_suggestion += f"\n\n{concept_info['tip']}"
        
        return {
            "suggestion": full_suggestion,
            "source": "rule_based_enhanced",
            "processing_time": 0.1,
            "success": True,
            "error_type": concept
        }
    
    def _get_syntax_error_suggestion(self, code):
        """Specific suggestions for syntax errors"""
        suggestions = []
        
        # Check for #define semicolon error
        if re.search(r'#define\s+\w+\s+[^;]*;', code):
            suggestions.append("❌ **Critical Error:** Remove semicolon after `#define`")
            suggestions.append("✅ **Fix:** Change `#define int long long;` to `#define int long long`")
            suggestions.append("⚠️ **Also:** Use `signed main()` instead of `int main()` when redefining int")
        
        # Check for missing colons in Python
        if any(keyword in code for keyword in ['def ', 'if ', 'for ', 'while ']):
            missing_colons = re.findall(r'(if|for|while|def|class|try|except|with|elif|else)\s+[^:\n]*[^:]$', code, re.MULTILINE)
            if missing_colons:
                suggestions.append("❌ **Missing Colons:** Add ':' after control structures")
                suggestions.append(f"✅ **Fix:** Found {len(missing_colons)} lines missing colons")
        
        # Check for bracket mismatches
        if self._check_bracket_mismatch(code):
            suggestions.append("❌ **Bracket Mismatch:** Check for unmatched brackets/braces")
            suggestions.append("✅ **Fix:** Count opening and closing brackets carefully")
        
        if not suggestions:
            suggestions.append("**Common Syntax Issues to Check:**")
            suggestions.append("• Missing semicolons at end of statements")
            suggestions.append("• Unmatched brackets: (), [], {}")
            suggestions.append("• Typos in keywords (return, include, etc.)")
            suggestions.append("• Missing colons after if/for/while in Python")
        
        return "\n".join(suggestions)
    
    def _get_compilation_error_suggestion(self, code):
        """Specific suggestions for compilation errors"""
        suggestions = ["**Compilation Error Analysis:**"]
        
        if '#include' in code:
            if 'vector' in code and '#include <vector>' not in code and '#include <bits/stdc++.h>' not in code:
                suggestions.append("❌ **Missing Header:** Add `#include <vector>`")
            
            if 'sort(' in code and '#include <algorithm>' not in code and '#include <bits/stdc++.h>' not in code:
                suggestions.append("❌ **Missing Header:** Add `#include <algorithm>` for sort()")
            
            if re.search(r'#define\s+int\s+long\s+long', code) and 'int main(' in code:
                suggestions.append("❌ **Type Conflict:** `#define int long long` conflicts with `int main()`")
                suggestions.append("✅ **Fix:** Use `signed main()` instead of `int main()`")
        
        suggestions.extend([
            "**General Compilation Fixes:**",
            "• Check all variable declarations",
            "• Ensure function signatures match calls",
            "• Verify all required headers are included",
            "• Check for type mismatches"
        ])
        
        return "\n".join(suggestions)
    
    def _get_logic_error_suggestion(self, code):
        """Specific suggestions for logic errors"""
        suggestions = ["**Logic Error Analysis:**"]
        
        # Array bounds
        if re.search(r'for.*<=.*n', code):
            suggestions.append("❌ **Array Bounds:** Using `<= n` may cause out-of-bounds access")
            suggestions.append("✅ **Fix:** Use `< n` for 0-indexed arrays")
        
        # Binary search overflow
        if 'mid = (left + right) / 2' in code:
            suggestions.append("❌ **Integer Overflow:** `(left + right) / 2` can overflow")
            suggestions.append("✅ **Fix:** Use `mid = left + (right - left) / 2`")
        
        suggestions.extend([
            "**Common Logic Issues:**",
            "• Off-by-one errors in loops",
            "• Integer overflow in calculations",
            "• Wrong loop conditions",
            "• Incorrect array indexing"
        ])
        
        return "\n".join(suggestions)
    
    def _check_bracket_mismatch(self, code):
        """Simple bracket mismatch check"""
        stack = []
        pairs = {'(': ')', '[': ']', '{': '}'}
        
        for char in code:
            if char in pairs:
                stack.append(char)
            elif char in pairs.values():
                if not stack:
                    return True
                opening = stack.pop()
                if pairs[opening] != char:
                    return True
        
        return len(stack) > 0

# Global enhanced LLM engine instance
llm_engine = EnhancedLLMSuggestionEngine()
