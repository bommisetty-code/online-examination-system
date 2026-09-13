from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app import db
from app.models import (
    Exam,
    Question,
    Option,
    User,
    ExamSubmission,
    Result,
    StudentAnswer
)
from app.decorators import admin_required
from app.validators import (
    validate_exam_data,
    validate_question_data,
    error_response
)
from app.errors import ValidationError, NotFoundError, AuthorizationError
from app.services import AuthService
from datetime import datetime
import uuid
from openpyxl import load_workbook


admin_bp = Blueprint(
    'admin',
    __name__,
    url_prefix='/api/admin'
)


# ============================================================
# STUDENT ROUTES
# ============================================================

@admin_bp.route('/students', methods=['GET'])
@admin_required
def get_students():
    """Get all student accounts."""
    try:
        students = (
            User.query
            .filter_by(role='student')
            .order_by(User.created_at.desc())
            .all()
        )

        return jsonify({
            'students': [
                {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'full_name': user.full_name,
                    'student_class': user.student_class,
                    'is_active': user.is_active,
                    'created_at': (
                        user.created_at.isoformat()
                        if user.created_at else None
                    )
                }
                for user in students
            ]
        }), 200

    except Exception as e:
        return jsonify({
            'message': 'Failed to fetch students',
            'error': str(e)
        }), 500


@admin_bp.route('/students', methods=['POST'])
@admin_required
def create_student_account():
    """Admin-only creation of a student account."""
    try:
        data = request.get_json() or {}

        email = (data.get('email') or '').strip()
        username = (data.get('username') or '').strip()
        password = data.get('password') or ''
        full_name = (data.get('full_name') or '').strip()
        student_class = (data.get('student_class') or '').strip()

        # Required fields
        if not email or not username or not password or not student_class:
            return jsonify({
                'message': (
                    'Email, username, password and student class '
                    'are required'
                )
            }), 400

        # Allowed classes
        if student_class not in ['7th', '8th', '10th']:
            return jsonify({
                'message': 'Student class must be 7th, 8th, or 10th'
            }), 400

        # Check duplicate email
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return jsonify({
                'message': 'Email already exists'
            }), 409

        # Check duplicate username
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            return jsonify({
                'message': 'Username already exists'
            }), 409

        # Create user
        user = AuthService.register_user(
            email,
            username,
            password,
            full_name,
            'student'
        )

        # Assign class
        user.student_class = student_class

        db.session.commit()

        return jsonify({
            'message': 'Student account created successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role,
                'student_class': user.student_class,
                'is_active': user.is_active
            }
        }), 201

    except (ValidationError,):
        db.session.rollback()
        raise

    except Exception as e:
        db.session.rollback()

        return jsonify({
            'message': 'Failed to create student account',
            'error': str(e)
        }), 500


# ============================================================
# EXAM ROUTES
# ============================================================

@admin_bp.route('/exams', methods=['GET'])
@admin_required
def get_exams():
    """Get all exams created by the logged-in admin."""
    try:
        admin_id = int(get_jwt_identity())

        exams = (
            Exam.query
            .filter_by(created_by=admin_id)
            .order_by(Exam.created_at.desc())
            .all()
        )

        return jsonify({
            'exams': [
                exam.to_dict()
                for exam in exams
            ]
        }), 200

    except Exception as e:
        return jsonify({
            'message': 'Failed to fetch exams',
            'error': str(e)
        }), 500


@admin_bp.route('/exams', methods=['POST'])
@admin_required
def create_exam():
    """Create a new exam for 7th, 8th or 10th class."""
    try:
        admin_id = int(get_jwt_identity())
        data = request.get_json() or {}

        if not data:
            return jsonify({
                'message': 'No data provided'
            }), 400

        # Validate existing exam fields
        errors = validate_exam_data(data)

        if errors:
            return error_response(errors)

        # Get class
        student_class = (data.get('student_class') or '').strip()

        if student_class not in ['7th', '8th', '10th']:
            return jsonify({
                'message': 'student_class must be 7th, 8th, or 10th'
            }), 400

        # Generate exam code
        exam_code = (
            data.get('exam_code')
            or 'EXAM_' + str(uuid.uuid4())[:8].upper()
        )

        # Check duplicate exam code
        existing_exam = Exam.query.filter_by(
            exam_code=exam_code
        ).first()

        if existing_exam:
            return jsonify({
                'message': 'Exam code already exists'
            }), 409

        # Create exam
        exam = Exam(
            name=data['name'],
            description=data.get('description', ''),
            duration_minutes=data['duration_minutes'],
            student_class=student_class,
            created_by=admin_id,
            exam_code=exam_code,
            is_active=data.get('is_active', False),
            passing_percentage=data.get(
                'passing_percentage',
                50.0
            )
        )

        db.session.add(exam)
        db.session.commit()

        return jsonify({
            'message': 'Exam created successfully',
            'exam': exam.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()

        return jsonify({
            'message': 'Failed to create exam',
            'error': str(e)
        }), 500


@admin_bp.route('/exams/<int:exam_id>', methods=['GET'])
@admin_required
def get_exam(exam_id):
    """Get exam details including questions."""
    try:
        admin_id = int(get_jwt_identity())

        exam = Exam.query.get(exam_id)

        if not exam:
            return jsonify({
                'message': 'Exam not found'
            }), 404

        if exam.created_by != admin_id:
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        return jsonify({
            'exam': exam.to_dict(
                include_questions=True
            )
        }), 200

    except Exception as e:
        return jsonify({
            'message': 'Failed to fetch exam',
            'error': str(e)
        }), 500


@admin_bp.route('/exams/<int:exam_id>', methods=['PUT'])
@admin_required
def update_exam(exam_id):
    """Update exam details."""
    try:
        admin_id = int(get_jwt_identity())

        exam = Exam.query.get(exam_id)

        if not exam:
            return jsonify({
                'message': 'Exam not found'
            }), 404

        if exam.created_by != admin_id:
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        data = request.get_json() or {}

        if not data:
            return jsonify({
                'message': 'No data provided'
            }), 400

        # Validate existing exam data
        errors = validate_exam_data(data)

        if errors:
            return error_response(errors)

        # Update basic fields
        exam.name = data.get(
            'name',
            exam.name
        )

        exam.description = data.get(
            'description',
            exam.description
        )

        exam.duration_minutes = data.get(
            'duration_minutes',
            exam.duration_minutes
        )

        exam.is_active = data.get(
            'is_active',
            exam.is_active
        )

        exam.passing_percentage = data.get(
            'passing_percentage',
            exam.passing_percentage
        )

        # Update class only when supplied
        if 'student_class' in data:
            student_class = (
                data.get('student_class') or ''
            ).strip()

            if student_class not in ['7th', '8th', '10th']:
                return jsonify({
                    'message': (
                        'student_class must be 7th, 8th, or 10th'
                    )
                }), 400

            exam.student_class = student_class

        exam.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'message': 'Exam updated successfully',
            'exam': exam.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()

        return jsonify({
            'message': 'Failed to update exam',
            'error': str(e)
        }), 500


@admin_bp.route('/exams/<int:exam_id>/activate', methods=['PATCH'])
@admin_required
def activate_exam(exam_id):
    """Activate or deactivate an exam."""
    try:
        admin_id = int(get_jwt_identity())

        exam = Exam.query.get(exam_id)

        if not exam:
            return jsonify({
                'message': 'Exam not found'
            }), 404

        if exam.created_by != admin_id:
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        data = request.get_json() or {}

        is_active = data.get(
            'is_active',
            not exam.is_active
        )

        exam.is_active = is_active
        exam.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'message': (
                f'Exam '
                f'{"activated" if is_active else "deactivated"} '
                f'successfully'
            ),
            'exam': exam.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()

        return jsonify({
            'message': 'Failed to update exam',
            'error': str(e)
        }), 500


@admin_bp.route('/exams/<int:exam_id>', methods=['DELETE'])
@admin_required
def delete_exam(exam_id):
    """Delete exam."""
    try:
        admin_id = int(get_jwt_identity())

        exam = Exam.query.get(exam_id)

        if not exam:
            return jsonify({
                'message': 'Exam not found'
            }), 404

        if exam.created_by != admin_id:
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        db.session.delete(exam)
        db.session.commit()

        return jsonify({
            'message': 'Exam deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()

        return jsonify({
            'message': 'Failed to delete exam',
            'error': str(e)
        }), 500


# ============================================================
# QUESTION ROUTES
# ============================================================

@admin_bp.route('/exams/<int:exam_id>/questions', methods=['GET'])
@admin_required
def get_questions(exam_id):
    """Get all questions for an exam."""
    try:
        admin_id = int(get_jwt_identity())

        exam = Exam.query.get(exam_id)

        if not exam:
            return jsonify({
                'message': 'Exam not found'
            }), 404

        if exam.created_by != admin_id:
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        questions = (
            Question.query
            .filter_by(exam_id=exam_id)
            .order_by(Question.order_number)
            .all()
        )

        return jsonify({
            'questions': [
                q.to_dict(include_options=True)
                for q in questions
            ]
        }), 200

    except Exception as e:
        return jsonify({
            'message': 'Failed to fetch questions',
            'error': str(e)
        }), 500


@admin_bp.route('/exams/<int:exam_id>/questions', methods=['POST'])
@admin_required
def create_question(exam_id):
    """Create a new question."""
    try:
        admin_id = int(get_jwt_identity())

        exam = Exam.query.get(exam_id)

        if not exam:
            return jsonify({
                'message': 'Exam not found'
            }), 404

        if exam.created_by != admin_id:
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        data = request.get_json() or {}

        if not data:
            return jsonify({
                'message': 'No data provided'
            }), 400

        errors = validate_question_data(data)

        if errors:
            return error_response(errors)

        last_question = (
            Question.query
            .filter_by(exam_id=exam_id)
            .order_by(Question.order_number.desc())
            .first()
        )

        order_number = (
            last_question.order_number + 1
            if last_question
            else 1
        )

        question = Question(
            exam_id=exam_id,
            question_text=data['question_text'],
            marks=data.get('marks', 1),
            order_number=order_number
        )

        db.session.add(question)
        db.session.flush()

        for idx, opt_data in enumerate(
            data['options'],
            start=1
        ):
            option = Option(
                question_id=question.id,
                option_text=opt_data['option_text'],
                option_order=idx,
                is_correct=opt_data.get(
                    'is_correct',
                    False
                )
            )

            db.session.add(option)

        # Correct total count
        exam.total_questions = (
            Question.query
            .filter_by(exam_id=exam_id)
            .count() + 1
        )

        db.session.commit()

        return jsonify({
            'message': 'Question created successfully',
            'question': question.to_dict(
                include_options=True
            )
        }), 201

    except Exception as e:
        db.session.rollback()

        return jsonify({
            'message': 'Failed to create question',
            'error': str(e)
        }), 500



# ============================================================
# BULK QUESTION EXCEL UPLOAD
# ============================================================

@admin_bp.route(
    '/exams/<int:exam_id>/questions/bulk-upload',
    methods=['POST']
)
@admin_required
def bulk_upload_questions(exam_id):
    """
    Upload multiple questions from an Excel (.xlsx) file.

    Required Excel columns:
    Question | Option A | Option B | Option C | Option D | Correct Option

    Correct Option must be A, B, C, or D.
    Each imported question receives 1 mark.
    """

    try:
        admin_id = int(get_jwt_identity())

        # ----------------------------------------------------
        # Check exam
        # ----------------------------------------------------

        exam = Exam.query.get(exam_id)

        if not exam:
            return jsonify({
                'message': 'Exam not found'
            }), 404

        # ----------------------------------------------------
        # Check admin ownership
        # ----------------------------------------------------

        if exam.created_by != admin_id:
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        # ----------------------------------------------------
        # Check uploaded file
        # ----------------------------------------------------

        if 'file' not in request.files:
            return jsonify({
                'message': 'Please upload an Excel file'
            }), 400

        file = request.files['file']

        if not file or not file.filename:
            return jsonify({
                'message': 'Please select an Excel file'
            }), 400

        # ----------------------------------------------------
        # Only XLSX allowed
        # ----------------------------------------------------

        if not file.filename.lower().endswith('.xlsx'):
            return jsonify({
                'message': 'Only .xlsx Excel files are allowed'
            }), 400

        # ----------------------------------------------------
        # Load workbook
        # ----------------------------------------------------

        try:
            workbook = load_workbook(
                file,
                read_only=True,
                data_only=True
            )
        except Exception:
            return jsonify({
                'message': (
                    'Invalid Excel file. '
                    'Please upload a valid .xlsx file'
                )
            }), 400

        worksheet = workbook.active

        # ----------------------------------------------------
        # Required headers
        # ----------------------------------------------------

        required_headers = [
            'Question',
            'Option A',
            'Option B',
            'Option C',
            'Option D',
            'Correct Option'
        ]

        # Read first row
        header_row = next(
            worksheet.iter_rows(
                min_row=1,
                max_row=1,
                values_only=True
            ),
            None
        )

        if not header_row:
            workbook.close()

            return jsonify({
                'message': 'Excel file is empty'
            }), 400

        # Normalize headers
        actual_headers = [
            str(value).strip()
            if value is not None
            else ''
            for value in header_row
        ]

        # ----------------------------------------------------
        # Validate headers
        # ----------------------------------------------------

        missing_headers = [
            header
            for header in required_headers
            if header not in actual_headers
        ]

        if missing_headers:
            workbook.close()

            return jsonify({
                'message': 'Invalid Excel headers',
                'missing_headers': missing_headers,
                'required_headers': required_headers
            }), 400

        # Create header -> column index mapping
        header_indexes = {
            header: actual_headers.index(header)
            for header in required_headers
        }

        # ----------------------------------------------------
        # Read Excel rows first
        # ----------------------------------------------------

        rows_to_import = []
        validation_errors = []

        for row_number, row in enumerate(
            worksheet.iter_rows(
                min_row=2,
                values_only=True
            ),
            start=2
        ):

            # Skip completely empty rows
            if not any(
                value is not None and str(value).strip()
                for value in row
            ):
                continue

            def get_cell(header):
                index = header_indexes[header]

                if index >= len(row):
                    return ''

                value = row[index]

                if value is None:
                    return ''

                return str(value).strip()

            question_text = get_cell('Question')
            option_a = get_cell('Option A')
            option_b = get_cell('Option B')
            option_c = get_cell('Option C')
            option_d = get_cell('Option D')
            correct_option = get_cell('Correct Option').upper()

            # ------------------------------------------------
            # Validate question
            # ------------------------------------------------

            if not question_text:
                validation_errors.append(
                    f'Row {row_number}: Question is required'
                )
                continue

            # ------------------------------------------------
            # Validate all four options
            # ------------------------------------------------

            if not option_a:
                validation_errors.append(
                    f'Row {row_number}: Option A is required'
                )
                continue

            if not option_b:
                validation_errors.append(
                    f'Row {row_number}: Option B is required'
                )
                continue

            if not option_c:
                validation_errors.append(
                    f'Row {row_number}: Option C is required'
                )
                continue

            if not option_d:
                validation_errors.append(
                    f'Row {row_number}: Option D is required'
                )
                continue

            # ------------------------------------------------
            # Validate correct option
            # ------------------------------------------------

            if correct_option not in ['A', 'B', 'C', 'D']:
                validation_errors.append(
                    f'Row {row_number}: '
                    f'Correct Option must be A, B, C, or D'
                )
                continue

            rows_to_import.append({
                'question_text': question_text,
                'options': [
                    {
                        'option_text': option_a,
                        'option_order': 1,
                        'is_correct': correct_option == 'A'
                    },
                    {
                        'option_text': option_b,
                        'option_order': 2,
                        'is_correct': correct_option == 'B'
                    },
                    {
                        'option_text': option_c,
                        'option_order': 3,
                        'is_correct': correct_option == 'C'
                    },
                    {
                        'option_text': option_d,
                        'option_order': 4,
                        'is_correct': correct_option == 'D'
                    }
                ]
            })

        workbook.close()

        # ----------------------------------------------------
        # Stop if validation errors exist
        # ----------------------------------------------------

        if validation_errors:
            return jsonify({
                'message': 'Excel validation failed',
                'errors': validation_errors
            }), 400

        if not rows_to_import:
            return jsonify({
                'message': 'No questions found in the Excel file'
            }), 400

        # ----------------------------------------------------
        # Get next question order number
        # ----------------------------------------------------

        last_question = (
            Question.query
            .filter_by(exam_id=exam_id)
            .order_by(
                Question.order_number.desc()
            )
            .first()
        )

        next_order_number = (
            last_question.order_number + 1
            if last_question
            else 1
        )

        # ----------------------------------------------------
        # Create questions and options
        # ----------------------------------------------------

        for question_data in rows_to_import:

            question = Question(
                exam_id=exam_id,
                question_text=question_data['question_text'],
                marks=1,
                order_number=next_order_number
            )

            db.session.add(question)
            db.session.flush()

            for option_data in question_data['options']:

                option = Option(
                    question_id=question.id,
                    option_text=option_data['option_text'],
                    option_order=option_data['option_order'],
                    is_correct=option_data['is_correct']
                )

                db.session.add(option)

            next_order_number += 1

        # ----------------------------------------------------
        # Update total questions
        # ----------------------------------------------------

        db.session.flush()

        exam.total_questions = (
            Question.query
            .filter_by(exam_id=exam_id)
            .count()
        )

        exam.updated_at = datetime.utcnow()

        # ----------------------------------------------------
        # Commit everything together
        # ----------------------------------------------------

        db.session.commit()

        return jsonify({
            'message': (
                f'{len(rows_to_import)} questions '
                f'imported successfully'
            ),
            'imported_count': len(rows_to_import),
            'total_questions': exam.total_questions
        }), 201

    except Exception as e:
        db.session.rollback()

        return jsonify({
            'message': 'Failed to import questions',
            'error': str(e)
        }), 500






@admin_bp.route(
    '/exams/<int:exam_id>/questions/<int:question_id>',
    methods=['GET']
)
@admin_required
def get_question(exam_id, question_id):
    """Get a single question."""
    try:
        admin_id = int(get_jwt_identity())

        exam = Exam.query.get(exam_id)

        if not exam:
            return jsonify({
                'message': 'Exam not found'
            }), 404

        if exam.created_by != admin_id:
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        question = Question.query.get(question_id)

        if not question or question.exam_id != exam_id:
            return jsonify({
                'message': 'Question not found'
            }), 404

        return jsonify({
            'question': question.to_dict(
                include_options=True
            )
        }), 200

    except Exception as e:
        return jsonify({
            'message': 'Failed to fetch question',
            'error': str(e)
        }), 500


@admin_bp.route(
    '/exams/<int:exam_id>/questions/<int:question_id>',
    methods=['PUT']
)
@admin_required
def update_question(exam_id, question_id):
    """Update an existing question."""
    try:
        admin_id = int(get_jwt_identity())

        exam = Exam.query.get(exam_id)

        if not exam:
            return jsonify({
                'message': 'Exam not found'
            }), 404

        if exam.created_by != admin_id:
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        question = Question.query.get(question_id)

        if not question or question.exam_id != exam_id:
            return jsonify({
                'message': 'Question not found'
            }), 404

        data = request.get_json() or {}

        if not data:
            return jsonify({
                'message': 'No data provided'
            }), 400

        errors = validate_question_data(data)

        if errors:
            return error_response(errors)

        question.question_text = data.get(
            'question_text',
            question.question_text
        )

        question.marks = data.get(
            'marks',
            question.marks
        )

        question.updated_at = datetime.utcnow()

        # Remove old options
        Option.query.filter_by(
            question_id=question_id
        ).delete()

        # Add new options
        for idx, opt_data in enumerate(
            data['options'],
            start=1
        ):
            option = Option(
                question_id=question.id,
                option_text=opt_data['option_text'],
                option_order=idx,
                is_correct=opt_data.get(
                    'is_correct',
                    False
                )
            )

            db.session.add(option)

        db.session.commit()

        return jsonify({
            'message': 'Question updated successfully',
            'question': question.to_dict(
                include_options=True
            )
        }), 200

    except Exception as e:
        db.session.rollback()

        return jsonify({
            'message': 'Failed to update question',
            'error': str(e)
        }), 500


@admin_bp.route(
    '/exams/<int:exam_id>/questions/<int:question_id>',
    methods=['DELETE']
)
@admin_required
def delete_question(exam_id, question_id):
    """Delete a question."""
    try:
        admin_id = int(get_jwt_identity())

        exam = Exam.query.get(exam_id)

        if not exam:
            return jsonify({
                'message': 'Exam not found'
            }), 404

        if exam.created_by != admin_id:
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        question = Question.query.get(question_id)

        if not question or question.exam_id != exam_id:
            return jsonify({
                'message': 'Question not found'
            }), 404

        db.session.delete(question)

        db.session.flush()

        # Recalculate exact question count
        exam.total_questions = (
            Question.query
            .filter_by(exam_id=exam_id)
            .count()
        )

        db.session.commit()

        return jsonify({
            'message': 'Question deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()

        return jsonify({
            'message': 'Failed to delete question',
            'error': str(e)
        }), 500


# ============================================================
# RESULTS ROUTES
# ============================================================

@admin_bp.route('/exams/<int:exam_id>/results', methods=['GET'])
@admin_required
def get_exam_results(exam_id):
    """Get all student results for an exam."""
    try:
        admin_id = int(get_jwt_identity())

        # Check exam
        exam = Exam.query.get(exam_id)

        if not exam:
            return jsonify({
                'message': 'Exam not found'
            }), 404

        # Only exam owner/admin can view results
        if exam.created_by != admin_id:
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        # Get all results for this exam
        results = (
            Result.query
            .filter_by(exam_id=exam_id)
            .order_by(Result.submitted_at.desc())
            .all()
        )

        result_data = []

        for result in results:
            student = User.query.get(result.student_id)

            if not student:
                continue

            result_data.append({
                'result': result.to_dict(),
                'student': {
                    'id': student.id,
                    'email': student.email,
                    'username': student.username,
                    'full_name': student.full_name,
                    'student_class': student.student_class
                }
            })

        return jsonify({
            'results': result_data
        }), 200

    except Exception as e:
        return jsonify({
            'message': 'Failed to fetch exam results',
            'error': str(e)
        }), 500


@admin_bp.route(
    '/exams/<int:exam_id>/results/<int:student_id>',
    methods=['GET']
)
@admin_required
def get_student_result(exam_id, student_id):
    """Get detailed result and answer review for one student."""
    try:
        admin_id = int(get_jwt_identity())

        # Check exam
        exam = Exam.query.get(exam_id)

        if not exam:
            return jsonify({
                'message': 'Exam not found'
            }), 404

        # Check admin ownership
        if exam.created_by != admin_id:
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        # Get result
        result = (
            Result.query
            .filter_by(
                exam_id=exam_id,
                student_id=student_id
            )
            .first()
        )

        if not result:
            return jsonify({
                'message': 'Result not found'
            }), 404

        # Get student
        student = User.query.get(student_id)

        if not student:
            return jsonify({
                'message': 'Student not found'
            }), 404

        # Get all exam questions
        questions = (
            Question.query
            .filter_by(exam_id=exam_id)
            .order_by(Question.order_number)
            .all()
        )

        answers = []

        for question in questions:

            # Student answer for this question
            student_answer = (
                StudentAnswer.query
                .filter_by(
                    submission_id=result.submission_id,
                    question_id=question.id
                )
                .first()
            )

            # Get selected option
            selected_option = None

            if student_answer and student_answer.selected_option_id:
                selected_option = Option.query.get(
                    student_answer.selected_option_id
                )

            # Get correct option
            correct_option = (
                Option.query
                .filter_by(
                    question_id=question.id,
                    is_correct=True
                )
                .first()
            )

            answers.append({
                'question_id': question.id,
                'question_text': question.question_text,
                'is_correct': (
                    bool(student_answer.is_correct)
                    if student_answer
                    else False
                ),
                'student_answer': {
                    'id': (
                        selected_option.id
                        if selected_option
                        else None
                    ),
                    'option_text': (
                        selected_option.option_text
                        if selected_option
                        else None
                    )
                },
                'correct_answer': {
                    'id': (
                        correct_option.id
                        if correct_option
                        else None
                    ),
                    'option_text': (
                        correct_option.option_text
                        if correct_option
                        else None
                    )
                }
            })

        return jsonify({
            'result': result.to_dict(),
            'student': {
                'id': student.id,
                'email': student.email,
                'username': student.username,
                'full_name': student.full_name,
                'student_class': student.student_class
            },
            'answers': answers
        }), 200

    except Exception as e:
        return jsonify({
            'message': 'Failed to fetch student result',
            'error': str(e)
        }), 500