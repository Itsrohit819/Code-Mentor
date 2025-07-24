class CodeMentor {
    constructor() {
        this.initializeElements();
        this.attachEventListeners();
        this.initializeUI();
    }

    initializeElements() {
        this.form = document.getElementById('codeForm');
        this.codeInput = document.getElementById('codeInput');
        this.errorInput = document.getElementById('errorInput');
        this.languageSelect = document.getElementById('languageSelect');
        this.analyzeBtn = document.getElementById('analyzeBtn');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.charCount = document.getElementById('charCount');
        
        // Result elements
        this.resultsSection = document.getElementById('resultsSection');
        this.errorSection = document.getElementById('errorSection');
        this.conceptResult = document.getElementById('conceptResult');
        this.confidenceResult = document.getElementById('confidenceResult');
        this.suggestionResult = document.getElementById('suggestionResult');
        this.processingTime = document.getElementById('processingTime');
        this.submissionId = document.getElementById('submissionId');
        this.errorMessage = document.getElementById('errorMessage');
    }

    attachEventListeners() {
        this.form.addEventListener('submit', this.handleSubmit.bind(this));
        this.codeInput.addEventListener('input', this.updateCharCount.bind(this));
        this.codeInput.addEventListener('paste', this.handlePaste.bind(this));
        
        // Auto-resize textarea
        this.codeInput.addEventListener('input', this.autoResize.bind(this));
        
        // Language change handler
        this.languageSelect.addEventListener('change', this.handleLanguageChange.bind(this));
    }

    initializeUI() {
        this.updateCharCount();
        this.setStatus('ready', 'Ready');
        
        // Add some sample code based on language
        this.updateSampleCode();
    }

    updateCharCount() {
        const count = this.codeInput.value.length;
        this.charCount.textContent = count;
        
        const charCountElement = this.charCount.parentElement;
        charCountElement.classList.remove('char-limit-warning', 'char-limit-danger');
        
        if (count > 8000) {
            charCountElement.classList.add('char-limit-danger');
        } else if (count > 6000) {
            charCountElement.classList.add('char-limit-warning');
        }
    }

    autoResize() {
        this.codeInput.style.height = 'auto';
        this.codeInput.style.height = Math.min(this.codeInput.scrollHeight, 400) + 'px';
    }

    handlePaste(event) {
        // Small delay to let paste complete
        setTimeout(() => {
            this.updateCharCount();
            this.autoResize();
        }, 10);
    }

    handleLanguageChange() {
        this.updateSampleCode();
    }

    updateSampleCode() {
        const language = this.languageSelect.value;
        const samples = {
            python: "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1",
            cpp: "#include <vector>\nusing namespace std;\n\nint binarySearch(vector<int>& arr, int target) {\n    int left = 0, right = arr.size() - 1;\n    while (left <= right) {\n        int mid = left + (right - left) / 2;\n        if (arr[mid] == target) return mid;\n        else if (arr[mid] < target) left = mid + 1;\n        else right = mid - 1;\n    }\n    return -1;\n}",
            java: "public class Solution {\n    public int binarySearch(int[] arr, int target) {\n        int left = 0, right = arr.length - 1;\n        while (left <= right) {\n            int mid = left + (right - left) / 2;\n            if (arr[mid] == target) return mid;\n            else if (arr[mid] < target) left = mid + 1;\n            else right = mid - 1;\n        }\n        return -1;\n    }\n}",
            javascript: "function binarySearch(arr, target) {\n    let left = 0, right = arr.length - 1;\n    while (left <= right) {\n        const mid = Math.floor((left + right) / 2);\n        if (arr[mid] === target) return mid;\n        else if (arr[mid] < target) left = mid + 1;\n        else right = mid - 1;\n    }\n    return -1;\n}",
            c: "#include <stdio.h>\n\nint binary_search(int arr[], int n, int target) {\n    int left = 0, right = n - 1;\n    while (left <= right) {\n        int mid = left + (right - left) / 2;\n        if (arr[mid] == target) return mid;\n        else if (arr[mid] < target) left = mid + 1;\n        else right = mid - 1;\n    }\n    return -1;\n}"
        };

        // Only update if the textarea is empty
        if (!this.codeInput.value.trim()) {
            this.codeInput.placeholder = `Example ${language.toUpperCase()} code:\n\n${samples[language] || samples.python}`;
        }
    }

    setStatus(type, message) {
        this.statusIndicator.className = `badge status-${type}`;
        this.statusIndicator.textContent = message;
    }

    showLoading() {
        this.analyzeBtn.disabled = true;
        this.analyzeBtn.innerHTML = '<span class="loading-spinner"></span> Analyzing...';
        this.setStatus('analyzing', 'Analyzing');
        this.hideResults();
    }

    hideLoading() {
        this.analyzeBtn.disabled = false;
        this.analyzeBtn.innerHTML = '<i class="bi bi-search"></i> Analyze Code';
    }

    async handleSubmit(event) {
        event.preventDefault();
        
        const code = this.codeInput.value.trim();
        const error = this.errorInput.value.trim();
        const language = this.languageSelect.value;

        // Validation
        if (!code) {
            this.showError('Please enter your code before analyzing.');
            return;
        }

        if (code.length > 10000) {
            this.showError('Code is too long. Please limit to 10,000 characters.');
            return;
        }

        try {
            this.showLoading();
            const startTime = Date.now();

            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    code: code,
                    error: error,
                    language: language
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }

            const clientTime = ((Date.now() - startTime) / 1000).toFixed(2);
            this.showResults(data, clientTime);

        } catch (error) {
            console.error('Analysis error:', error);
            this.showError(`Analysis failed: ${error.message}`);
            this.setStatus('error', 'Error');
        } finally {
            this.hideLoading();
        }
    }

    showResults(data, clientTime) {
        // Hide error section
        this.errorSection.style.display = 'none';
        
        // Populate results
        this.conceptResult.textContent = data.concept || 'Unknown';
        this.conceptResult.className = `badge ${this.getConceptColor(data.concept)}`;
        
        this.confidenceResult.textContent = data.confidence ? 
            `${(data.confidence * 100).toFixed(1)}%` : 'N/A';
        this.confidenceResult.className = `badge ${this.getConfidenceColor(data.confidence)}`;
        
        this.suggestionResult.innerHTML = this.formatSuggestion(data.suggestion || 'No suggestion available');
        
        this.processingTime.textContent = data.processing_time ? 
            `${data.processing_time}s (client: ${clientTime}s)` : `${clientTime}s`;
        
        this.submissionId.textContent = data.id || 'Unknown';

        // Show results with animation
        this.resultsSection.style.display = 'block';
        this.resultsSection.classList.add('fade-in');
        
        // Scroll to results
        this.resultsSection.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });

        this.setStatus('ready', 'Complete');

        // Add LLM indicator
        if (data.llm_used) {
            const llmBadge = document.createElement('span');
            llmBadge.className = 'badge bg-success ms-2';
            llmBadge.innerHTML = '<i class="bi bi-robot"></i> AI';
            this.conceptResult.parentElement.appendChild(llmBudge);
        }
    }

    showError(message) {
        this.hideResults();
        this.errorMessage.textContent = message;
        this.errorSection.style.display = 'block';
        this.errorSection.classList.add('slide-up');
        
        // Scroll to error
        this.errorSection.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }

    hideResults() {
        this.resultsSection.style.display = 'none';
        this.errorSection.style.display = 'none';
    }

    formatSuggestion(suggestion) {
        // Convert markdown-like formatting to HTML
        let formatted = suggestion
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/💡/g, '<i class="bi bi-lightbulb text-warning"></i>')
            .replace(/⚠️/g, '<i class="bi bi-exclamation-triangle text-warning"></i>')
            .replace(/✅/g, '<i class="bi bi-check-circle text-success"></i>')
            .replace(/❌/g, '<i class="bi bi-x-circle text-danger"></i>');

        // Add line breaks for better formatting
        formatted = formatted.replace(/\n/g, '<br>');
        
        return formatted;
    }

    getConceptColor(concept) {
        const colors = {
            'Binary Search': 'bg-primary',
            'Dynamic Programming': 'bg-success',
            'Graph Traversal': 'bg-info',
            'Sorting': 'bg-warning',
            'Array Manipulation': 'bg-secondary',
            'String Processing': 'bg-dark',
            'Tree Algorithms': 'bg-success',
            'Greedy Algorithm': 'bg-primary',
            'Backtracking': 'bg-danger',
            'Mathematics': 'bg-info',
            'General Programming': 'bg-secondary'
        };
        return colors[concept] || 'bg-secondary';
    }

    getConfidenceColor(confidence) {
        if (!confidence) return 'bg-secondary';
        if (confidence >= 0.8) return 'bg-success';
        if (confidence >= 0.6) return 'bg-warning';
        return 'bg-danger';
    }
    showResults(data, clientTime) {
        // Hide error section
        this.errorSection.style.display = 'none';
        
        // Populate results
        this.conceptResult.textContent = data.concept || 'Unknown';
        this.conceptResult.className = `badge ${this.getConceptColor(data.concept)}`;
        
        this.confidenceResult.textContent = data.confidence ? 
            `${(data.confidence * 100).toFixed(1)}%` : 'N/A';
        this.confidenceResult.className = `badge ${this.getConfidenceColor(data.confidence)}`;
        
        // Enhanced suggestion display with compiler results
        this.suggestionResult.innerHTML = this.formatSuggestion(data.suggestion || 'No suggestion available');
        
        this.processingTime.textContent = data.processing_time ? 
            `${data.processing_time}s (client: ${clientTime}s)` : `${clientTime}s`;
        
        this.submissionId.textContent = data.id || 'Unknown';

        // Add compiler analysis indicators
        this.addCompilerIndicators(data);
        
        // Show exact fixes if available
        if (data.exact_fixes_available && data.exact_fixes) {
            this.showExactFixes(data.exact_fixes);
        }

        // Show results with animation
        this.resultsSection.style.display = 'block';
        this.resultsSection.classList.add('fade-in');
        
        this.resultsSection.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });

        this.setStatus('ready', 'Complete');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CodeMentor();
});

// Add some useful keyboard shortcuts
document.addEventListener('keydown', (event) => {
    // Ctrl/Cmd + Enter to analyze
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault();
        document.getElementById('analyzeBtn').click();
    }
    
    // Ctrl/Cmd + K to focus on code input
    if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        document.getElementById('codeInput').focus();
    }
});
