import os
import time
import logging
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import Config

logger = logging.getLogger(__name__)

class LLMSuggestionEngine:
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
                temperature=0.3,
                max_tokens=500
            )
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert competitive programming mentor. 
                 Your task is to analyze code and provide concise, actionable debugging suggestions.
                 Focus on common issues, edge cases, and best practices."""),
                ("human", """
                Code:
                ```
                {code}
                ```
                
                Error/Issue: {error}
                Detected Concept: {concept}
                
                Please provide:
                1. Brief analysis of the issue
                2. Specific suggestion to fix it
                3. One coding tip related to this concept
                
                Keep response under 150 words and be practical.
                """)
            ])
            
            # Create chain
            output_parser = StrOutputParser()
            self.chain = prompt | self.llm | output_parser
            
            logger.info("LLM initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            self.llm = None
            self.chain = None
    
    def get_suggestion(self, code: str, error: str, concept: str, language: str = "python") -> Dict[str, Any]:
        """Get intelligent suggestion from LLM"""
        start_time = time.time()
        
        try:
            if not self.chain:
                return self._fallback_suggestion(concept, error)
            
            # Truncate code if too long
            if len(code) > 2000:
                code = code[:2000] + "\n... (truncated)"
            
            # Get suggestion from LLM
            suggestion = self.chain.invoke({
                "code": code,
                "error": error or "No specific error provided",
                "concept": concept,
                "language": language
            })
            
            processing_time = time.time() - start_time
            
            return {
                "suggestion": suggestion.strip(),
                "source": "llm",
                "processing_time": processing_time,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"LLM suggestion failed: {str(e)}")
            return self._fallback_suggestion(concept, error)
    
    def _fallback_suggestion(self, concept: str, error: str) -> Dict[str, Any]:
        """Fallback suggestions when LLM is not available"""
        suggestions = {
            "Binary Search": {
                "suggestion": "Common binary search issues:\n• Check loop condition (left <= right vs left < right)\n• Verify mid calculation: mid = left + (right - left) // 2\n• Ensure array is sorted\n• Handle edge cases: empty array, single element\n• Check if you're searching for the right condition",
                "tip": "Always verify your array is sorted before binary search!"
            },
            "Dynamic Programming": {
                "suggestion": "DP debugging checklist:\n• Verify base cases are correct\n• Check state transitions\n• Ensure you're not accessing out-of-bounds indices\n• Consider bottom-up vs top-down approach\n• Check if you need 1D or 2D DP array",
                "tip": "Draw out small examples to verify your DP logic!"
            },
            "Graph Traversal": {
                "suggestion": "Graph traversal issues:\n• Ensure visited set/array is properly initialized\n• Check if you're handling disconnected components\n• Verify adjacency list/matrix construction\n• For DFS: watch for stack overflow on large graphs\n• For BFS: ensure queue operations are correct",
                "tip": "Always mark nodes as visited before adding to queue/stack!"
            },
            "Sorting": {
                "suggestion": "Sorting algorithm checklist:\n• Verify comparison logic (< vs <= vs >)\n• Check array bounds in loops\n• Ensure proper swapping mechanism\n• For recursive sorts: check base cases\n• Test with edge cases: empty, single element, duplicates",
                "tip": "Test your sorting with arrays containing duplicates!"
            },
            "Array Manipulation": {
                "suggestion": "Array operation issues:\n• Check for index out of bounds\n• Verify loop conditions and increments\n• Ensure proper array initialization\n• Consider edge cases: empty arrays, single elements\n• Check if you need to handle negative indices",
                "tip": "Always validate array bounds before accessing elements!"
            },
            "String Processing": {
                "suggestion": "String processing checklist:\n• Handle empty strings and single characters\n• Check string indexing and slicing\n• Verify string concatenation logic\n• Consider case sensitivity\n• Watch for off-by-one errors in substring operations",
                "tip": "Remember strings are immutable in most languages!"
            },
            "Tree Algorithms": {
                "suggestion": "Tree algorithm issues:\n• Check for null/None node handling\n• Verify recursive base cases\n• Ensure proper tree traversal order\n• Check if tree is balanced/complete as expected\n• Handle edge case: empty tree or single node",
                "tip": "Always check for null nodes before accessing properties!"
            },
            "Greedy Algorithm": {
                "suggestion": "Greedy approach verification:\n• Confirm greedy choice property holds\n• Verify optimal substructure\n• Check sorting criteria if applicable\n• Test with counterexamples\n• Ensure you're making locally optimal choices",
                "tip": "Not all problems have greedy solutions - verify optimality!"
            },
            "Backtracking": {
                "suggestion": "Backtracking debugging:\n• Verify base case and termination condition\n• Check if you're properly undoing changes\n• Ensure all possible choices are explored\n• Verify pruning conditions\n• Test with small inputs first",
                "tip": "Remember to undo changes when backtracking!"
            },
            "Mathematics": {
                "suggestion": "Mathematical algorithm issues:\n• Check for integer overflow\n• Verify mathematical formulas\n• Handle edge cases: zero, negative numbers\n• Consider precision issues with floating point\n• Test boundary conditions",
                "tip": "Use modular arithmetic to prevent overflow!"
            }
        }
        
        default_suggestion = {
            "suggestion": "General debugging tips:\n• Add print statements to trace execution\n• Test with simple inputs first\n• Check variable types and values\n• Verify logic step by step\n• Consider edge cases and boundary conditions",
            "tip": "Break down complex problems into smaller parts!"
        }
        
        concept_info = suggestions.get(concept, default_suggestion)
        
        full_suggestion = f"{concept_info['suggestion']}\n\n💡 Tip: {concept_info['tip']}"
        
        if error and error.strip():
            full_suggestion = f"Error Analysis: {error}\n\n{full_suggestion}"
        
        return {
            "suggestion": full_suggestion,
            "source": "rule_based",
            "processing_time": 0.1,
            "success": True
        }

# Global LLM engine instance
llm_engine = LLMSuggestionEngine()
