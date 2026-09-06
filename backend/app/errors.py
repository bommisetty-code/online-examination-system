from flask import jsonify

class APIError(Exception):
    """Base API error"""
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code

class ValidationError(APIError):
    """Validation error"""
    def __init__(self, message):
        super().__init__(message, 400)

class AuthenticationError(APIError):
    """Authentication error"""
    def __init__(self, message="Authentication failed"):
        super().__init__(message, 401)

class AuthorizationError(APIError):
    """Authorization error"""
    def __init__(self, message="Access forbidden"):
        super().__init__(message, 403)

class NotFoundError(APIError):
    """Not found error"""
    def __init__(self, message="Resource not found"):
        super().__init__(message, 404)

class ConflictError(APIError):
    """Conflict error"""
    def __init__(self, message="Conflict"):
        super().__init__(message, 409)

class ExamAlreadySubmittedError(APIError):
    """Exam already submitted error"""
    def __init__(self, message="Exam already submitted"):
        super().__init__(message, 409)

class ExamExpiredError(APIError):
    """Exam time expired error"""
    def __init__(self, message="Exam time has expired"):
        super().__init__(message, 410)

def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify({'message': error.message})
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        return jsonify({'message': 'Bad request'}), 400
    
    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({'message': 'Not found'}), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        return jsonify({'message': 'Internal server error'}), 500
