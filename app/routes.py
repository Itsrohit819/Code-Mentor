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
        
        # 🔍 Run classifier for concept + confidence
        analysis = classifier.get_detailed_analysis(code)
        concept = analysis['concept']
        confidence = analysis['confidence']
        
        # 💡 Generate suggestion using LLM
        suggestion_result = llm_engine.get_suggestion(
            code=code,
            error=error,
            concept=concept,
            language=language,
            confidence=confidence
        )
        
        total_time = time.time() - start_time
        
        # 🗃️ Save in database
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
        
        response = {
            'id': submission.id,
            'concept': concept,
            'confidence': round(confidence, 2),
            'suggestion': suggestion_result['suggestion'],
            'processing_time': round(total_time, 2),
            'llm_used': suggestion_result['source'] == 'llm',
            'error_type': concept,
            'detailed_analysis': {
                'syntax_errors': len(analysis['syntax_errors']),
                'compilation_errors': len(analysis['compilation_errors']),
                'logic_errors': len(analysis['logic_errors'])
            },
            'timestamp': submission.timestamp.isoformat()
        }
        
        logger.info(f"Enhanced analysis completed for submission {submission.id} in {total_time:.2f}s - {concept}")
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in analyze_code: {str(e)}")
        return jsonify({
            'error': 'An error occurred while analyzing your code',
            'details': str(e) if current_app.debug else None
        }), 500
