import time
import logging
from flask import Blueprint, render_template, request, jsonify, current_app
from app import db
from app.database import CodeSubmission
from app.ml_classifier import classifier  # Enhanced classifier
from app.llm_utils import llm_engine      # Enhanced LLM engine

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@main.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@main.route("/api/analyze", methods=["POST"])
def analyze_code():
    start_time = time.time()
    
    try:
        # Validate request
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.get_json()
        code = data.get('code', '').strip()
        error = data.get('error', '').strip()
        language = data.get('language', 'cpp').lower()
        
        if not code:
            return jsonify({'error': 'Code is required'}), 400
        
        if len(code) > 10000:
            return jsonify({'error': 'Code too long (max 10000 characters)'}), 400
        
        # Enhanced analysis with compiler integration
        concept, confidence, compiler_data = classifier.predict_concept_with_compiler(code, language)
        
        # Get enhanced suggestion with compiler data
        suggestion_result = llm_engine.get_suggestion_with_compiler(
            code=code, 
            error=error, 
            concept=concept, 
            language=language,
            compiler_data=compiler_data
        )
        
        # Calculate total processing time
        total_time = time.time() - start_time
        
        # Save to database
        submission = CodeSubmission(
            code=code,
            error=error,
            concept=concept,
            suggestion=suggestion_result['suggestion'],
            confidence_score=confidence,
            processing_time=total_time
        )
        
        db.session.add(submission)
        db.session.commit()
        
        # Enhanced response with compiler data
        response = {
            'id': submission.id,
            'concept': concept,
            'confidence': round(confidence, 2),
            'suggestion': suggestion_result['suggestion'],
            'processing_time': round(total_time, 2),
            'analysis_source': suggestion_result.get('source', 'rule_based'),
            'compilation_successful': compiler_data.get('compilation_successful', True),
            'compiler_issues': len(compiler_data.get('compiler_issues', [])),
            'exact_fixes_available': len(compiler_data.get('exact_fixes', [])) > 0,
            'timestamp': submission.timestamp.isoformat()
        }
        
        # Add exact fixes if available
        if compiler_data.get('exact_fixes'):
            response['exact_fixes'] = compiler_data['exact_fixes']
        
        logger.info(f"Enhanced analysis completed for submission {submission.id} in {total_time:.2f}s - {concept}")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in analyze_code: {str(e)}")
        return jsonify({
            'error': 'An error occurred while analyzing your code',
            'details': str(e) if current_app.debug else None
        }), 500