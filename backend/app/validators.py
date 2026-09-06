import re
from flask import jsonify

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validate username: 3-50 characters, letters, numbers, spaces and underscore"""
    pattern = r'^[a-zA-Z0-9_ ]{3,50}$'
    return re.match(pattern, username) is not None

def validate_password(password):
    """
    Validate password:
    - At least 6 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    """
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    return True, "Password is valid"

def validate_exam_data(data):
    """Validate exam data"""
    errors = []
    
    if not data.get('name') or len(data['name'].strip()) == 0:
        errors.append("Exam name is required")
    
    if not isinstance(data.get('duration_minutes'), int) or data['duration_minutes'] <= 0:
        errors.append("Duration must be a positive integer (minutes)")
    
    if data.get('passing_percentage'):
        try:
            pp = float(data['passing_percentage'])
            if pp < 0 or pp > 100:
                errors.append("Passing percentage must be between 0 and 100")
        except (ValueError, TypeError):
            errors.append("Passing percentage must be a number")
    
    return errors

def validate_question_data(data):
    """Validate question data"""
    errors = []
    
    if not data.get('question_text') or len(data['question_text'].strip()) == 0:
        errors.append("Question text is required")
    
    options = data.get('options', [])
    if len(options) < 2:
        errors.append("At least 2 options are required")
    
    if len(options) > 10:
        errors.append("Maximum 10 options allowed")
    
    correct_count = sum(1 for opt in options if opt.get('is_correct', False))
    if correct_count != 1:
        errors.append("Exactly one option must be marked as correct")
    
    for i, opt in enumerate(options):
        if not opt.get('option_text') or len(opt['option_text'].strip()) == 0:
            errors.append(f"Option {i+1} text is required")
    
    return errors

def validate_answer_submission(data):
    """Validate answer submission"""
    errors = []
    
    if data.get('selected_option_id') is not None and not isinstance(data['selected_option_id'], int):
        errors.append("Invalid option ID")
    
    return errors

def error_response(errors, status_code=400):
    """Generate error response"""
    return jsonify({'errors': errors}), status_code
