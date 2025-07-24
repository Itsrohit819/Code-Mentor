import subprocess
import tempfile
import os
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class CompilerAnalyzer:
    def __init__(self):
        self.compilers = {
            "cpp": "g++",
            "c": "gcc", 
            "python": "python",
            "java": "javac"
        }
        self.extensions = {
            "cpp": ".cpp",
            "c": ".c",
            "python": ".py",
            "java": ".java"
        }
    
    def analyze_code(self, code: str, language: str) -> Dict:
        """Main method to analyze code using compiler"""
        if language not in self.compilers:
            return {
                "success": False,
                "error": f"Unsupported language: {language}",
                "issues": []
            }
        
        try:
            # Create temporary file
            temp_file = self._create_temp_file(code, language)
            
            # Compile and get feedback
            compile_result = self._compile_code(temp_file, language)
            
            # Parse compiler output
            parsed_result = self._parse_compiler_output(compile_result, language)
            
            # Clean up
            self._cleanup_temp_file(temp_file, language)
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Compiler analysis failed: {str(e)}")
            return {
                "success": False,
                "error": f"Analysis failed: {str(e)}",
                "issues": []
            }
    
    def _create_temp_file(self, code: str, language: str) -> str:
        """Create temporary file with code"""
        suffix = self.extensions[language]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(code)
            return f.name
    
    def _compile_code(self, filepath: str, language: str) -> subprocess.CompletedProcess:
        """Compile the code and capture output"""
        compiler = self.compilers[language]
        
        if language == "cpp":
            cmd = [compiler, "-Wall", "-Wextra", "-std=c++17", filepath, "-o", "/tmp/output"]
        elif language == "c":
            cmd = [compiler, "-Wall", "-Wextra", filepath, "-o", "/tmp/output"]
        elif language == "python":
            cmd = ["python", "-m", "py_compile", filepath]
        elif language == "java":
            cmd = ["javac", filepath]
        
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    
    def _parse_compiler_output(self, result: subprocess.CompletedProcess, language: str) -> Dict:
        """Parse compiler output into structured data"""
        compilation_successful = result.returncode == 0
        issues = []
        
        if not compilation_successful and result.stderr:
            issues = self._extract_issues(result.stderr, language)
        
        # Get exact fixes for common issues
        exact_fixes = self._generate_exact_fixes(issues, language)
        
        return {
            "success": True,
            "compilation_successful": compilation_successful,
            "issues": issues,
            "exact_fixes": exact_fixes,
            "raw_stderr": result.stderr,
            "raw_stdout": result.stdout,
            "primary_issue": issues[0] if issues else None
        }
    
    def _extract_issues(self, stderr: str, language: str) -> List[Dict]:
        """Extract structured issues from stderr"""
        issues = []
        
        if language in ["cpp", "c"]:
            issues = self._parse_gcc_errors(stderr)
        elif language == "python":
            issues = self._parse_python_errors(stderr)
        elif language == "java":
            issues = self._parse_java_errors(stderr)
        
        return issues
    
    def _parse_gcc_errors(self, stderr: str) -> List[Dict]:
        """Parse GCC/G++ error output"""
        issues = []
        lines = stderr.split('\n')
        
        for line in lines:
            if not line.strip():
                continue
            
            # Pattern: filename:line:column: error/warning: message
            pattern = r'(.+):(\d+):(\d+):\s*(error|warning):\s*(.+)'
            match = re.match(pattern, line)
            
            if match:
                issue = {
                    "line": int(match.group(2)),
                    "column": int(match.group(3)),
                    "type": match.group(4),
                    "message": match.group(5).strip(),
                    "confidence": 0.95,
                    "source": "compiler"
                }
                
                # Add specific analysis for common errors
                issue["analysis"] = self._analyze_cpp_error(issue["message"])
                issues.append(issue)
        
        return issues
    
    def _parse_python_errors(self, stderr: str) -> List[Dict]:
        """Parse Python error output"""
        issues = []
        lines = stderr.split('\n')
        
        for i, line in enumerate(lines):
            if 'SyntaxError' in line or 'IndentationError' in line:
                # Look for line number in previous lines
                line_num = None
                for j in range(max(0, i-3), i):
                    if 'line' in lines[j]:
                        line_match = re.search(r'line (\d+)', lines[j])
                        if line_match:
                            line_num = int(line_match.group(1))
                            break
                
                issue = {
                    "line": line_num or 1,
                    "column": 1,
                    "type": "error",
                    "message": line.strip(),
                    "confidence": 0.9,
                    "source": "compiler",
                    "analysis": self._analyze_python_error(line)
                }
                issues.append(issue)
        
        return issues
    
    def _analyze_cpp_error(self, message: str) -> Dict:
        """Provide specific analysis for C++ errors"""
        message_lower = message.lower()
        
        if "expected ';'" in message_lower:
            return {
                "issue_type": "missing_semicolon",
                "fix": "Add semicolon at the end of the statement",
                "explanation": "C++ statements must end with semicolons"
            }
        elif "expected '{'" in message_lower:
            return {
                "issue_type": "missing_brace",
                "fix": "Add opening brace after function/control structure",
                "explanation": "Function bodies and control structures need braces"
            }
        elif "#define" in message_lower and ";" in message_lower:
            return {
                "issue_type": "define_semicolon",
                "fix": "Remove semicolon from #define statement",
                "explanation": "#define is a preprocessor directive, not a C++ statement"
            }
        else:
            return {
                "issue_type": "general",
                "fix": "Check syntax according to error message",
                "explanation": "General compilation error"
            }
    
    def _analyze_python_error(self, message: str) -> Dict:
        """Provide specific analysis for Python errors"""
        if "IndentationError" in message:
            return {
                "issue_type": "indentation",
                "fix": "Fix indentation - use 4 spaces consistently",
                "explanation": "Python uses indentation to define code blocks"
            }
        elif "invalid syntax" in message:
            return {
                "issue_type": "syntax",
                "fix": "Check for missing colons, parentheses, or quotes",
                "explanation": "Python syntax error detected"
            }
        else:
            return {
                "issue_type": "general",
                "fix": "Check Python syntax",
                "explanation": "General Python error"
            }
    
    def _generate_exact_fixes(self, issues: List[Dict], language: str) -> List[Dict]:
        """Generate exact code fixes for issues"""
        fixes = []
        
        for issue in issues:
            analysis = issue.get("analysis", {})
            
            fix = {
                "line": issue["line"],
                "issue_type": analysis.get("issue_type", "unknown"),
                "original_error": issue["message"],
                "fix_description": analysis.get("fix", "Manual fix required"),
                "explanation": analysis.get("explanation", ""),
                "confidence": issue["confidence"]
            }
            
            # Add specific code suggestions
            if analysis.get("issue_type") == "missing_semicolon":
                fix["code_suggestion"] = "Add ';' at the end of line " + str(issue["line"])
            elif analysis.get("issue_type") == "define_semicolon":
                fix["code_suggestion"] = "Remove ';' from #define on line " + str(issue["line"])
            
            fixes.append(fix)
        
        return fixes
    
    def _cleanup_temp_file(self, filepath: str, language: str):
        """Clean up temporary files"""
        try:
            if os.path.exists(filepath):
                os.unlink(filepath)
            
            # Clean up output files
            if language in ["cpp", "c"] and os.path.exists("/tmp/output"):
                os.unlink("/tmp/output")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp files: {str(e)}")

# Global compiler analyzer instance
compiler_analyzer = CompilerAnalyzer()
