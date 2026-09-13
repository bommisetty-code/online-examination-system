from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity

from app import db
from app.models import (
    Exam,
    Question,
    Option,
    ExamSubmission,
    StudentAnswer,
    Result,
    User
)
from app.decorators import student_required

from datetime import datetime
from decimal import Decimal


student_bp = Blueprint(
    'student',
    __name__,
    url_prefix='/api/student'
)


# ============================================================
# HELPER
# ============================================================

def get_current_student():
    """Get currently logged-in student."""
    student_id = int(get_jwt_identity())
    return User.query.get(student_id)


def check_exam_class_access(student, exam):
    """
    Student can access only the exam assigned to
    their class.
    """
    if not student:
        return False

    if student.role != 'student':
        return False

    return student.student_class == exam.student_class


# ============================================================
# EXAM ACCESS ROUTES
# ============================================================

@student_bp.route('/exams', methods=['GET'])
@student_required
def get_available_exams():
    """
    Get exams available for the logged-in student.

    IMPORTANT:
    Only exams matching student's class are returned.
    """

    try:
        student = get_current_student()

        if not student:
            return jsonify({
                'message': 'Student not found'
            }), 404

        if not student.student_class:
            return jsonify({
                'message': 'Student class is not assigned'
            }), 400

        exams = Exam.query.filter(
            Exam.is_active == True,
            Exam.student_class == student.student_class
        ).order_by(
            Exam.created_at.desc()
        ).all()

        exam_list = []

        for exam in exams:

            submission = ExamSubmission.query.filter_by(
                student_id=student.id,
                exam_id=exam.id
            ).first()

            result = Result.query.filter_by(
                student_id=student.id,
                exam_id=exam.id
            ).first()

            exam_data = exam.to_dict()

            exam_data['already_taken'] = result is not None

            exam_data['in_progress'] = (
                submission is not None
                and submission.status == 'in_progress'
            )

            exam_data['submission_id'] = (
                submission.id
                if submission
                and submission.status == 'in_progress'
                else None
            )

            admin = User.query.get(exam.created_by)

            if admin:
                exam_data['admin_name'] = (
                    admin.full_name
                    or admin.username
                    or admin.email
                )
            else:
                exam_data['admin_name'] = 'Admin'

            exam_list.append(exam_data)

        return jsonify({
            'exams': exam_list,
            'student_class': student.student_class
        }), 200

    except Exception as e:

        return jsonify({
            'message': 'Failed to fetch exams',
            'error': str(e)
        }), 500


# ============================================================
# GET SINGLE EXAM DETAILS
# ============================================================

@student_bp.route('/exams/<int:exam_id>', methods=['GET'])
@student_required
def get_exam_details(exam_id):
    """
    Get exam details.

    Student can access only their own class exam.
    """

    try:
        student = get_current_student()

        if not student:
            return jsonify({
                'message': 'Student not found'
            }), 404

        exam = Exam.query.get(exam_id)

        if not exam:
            return jsonify({
                'message': 'Exam not found'
            }), 404

        if not check_exam_class_access(student, exam):
            return jsonify({
                'message': 'You are not authorized to access this exam'
            }), 403

        if not exam.is_active:
            return jsonify({
                'message': 'Exam is not active'
            }), 403

        result = Result.query.filter_by(
            student_id=student.id,
            exam_id=exam_id
        ).first()

        if result:
            return jsonify({
                'message': 'You have already completed this exam'
            }), 403

        return jsonify({
            'exam': exam.to_dict()
        }), 200

    except Exception as e:

        return jsonify({
            'message': 'Failed to fetch exam',
            'error': str(e)
        }), 500


# ============================================================
# START EXAM
# ============================================================

@student_bp.route('/exams/<int:exam_id>/start', methods=['POST'])
@student_required
def start_exam(exam_id):
    """
    Start an exam.

    Duration is captured at the time the exam starts.
    """

    try:
        student = get_current_student()

        if not student:
            return jsonify({
                'message': 'Student not found'
            }), 404

        exam = Exam.query.get(exam_id)

        if not exam:
            return jsonify({
                'message': 'Exam not found'
            }), 404

        if not check_exam_class_access(student, exam):
            return jsonify({
                'message': 'You are not authorized to take this exam'
            }), 403

        if not exam.is_active:
            return jsonify({
                'message': 'Exam is not active'
            }), 403

        result = Result.query.filter_by(
            student_id=student.id,
            exam_id=exam_id
        ).first()

        if result:
            return jsonify({
                'message': (
                    'You have already completed this exam '
                    'and cannot retake it'
                )
            }), 409

        existing_submission = ExamSubmission.query.filter_by(
            student_id=student.id,
            exam_id=exam_id,
            status='in_progress'
        ).first()

        if existing_submission:

            elapsed = (
                datetime.utcnow()
                - existing_submission.started_at
            ).total_seconds()

            remaining = (
                existing_submission.duration_minutes * 60
            ) - int(elapsed)

            if remaining <= 0:

                existing_submission.status = 'auto_submitted'
                existing_submission.submitted_at = datetime.utcnow()
                existing_submission.time_spent_seconds = (
                    existing_submission.duration_minutes * 60
                )

                db.session.commit()

                result = _calculate_and_save_result(
                    existing_submission
                )

                return jsonify({
                    'message': 'Exam time expired',
                    'status': 'auto_submitted',
                    'result': result.to_dict()
                }), 410

            return jsonify({
                'message': 'Exam already started',
                'submission_id': existing_submission.id,
                'exam_started_at': (
                    existing_submission.started_at.isoformat()
                ),
                'duration_minutes': (
                    existing_submission.duration_minutes
                ),
                'elapsed_seconds': int(elapsed),
                'remaining_seconds': max(0, int(remaining))
            }), 200

        submission = ExamSubmission(
            student_id=student.id,
            exam_id=exam.id,
            duration_minutes=exam.duration_minutes,
            status='in_progress',
            ip_address=request.remote_addr,
            user_agent=request.headers.get(
                'User-Agent',
                ''
            )
        )

        db.session.add(submission)
        db.session.commit()

        return jsonify({
            'message': 'Exam started successfully',
            'submission_id': submission.id,
            'exam_started_at': submission.started_at.isoformat(),
            'duration_minutes': submission.duration_minutes
        }), 201

    except Exception as e:

        db.session.rollback()

        return jsonify({
            'message': 'Failed to start exam',
            'error': str(e)
        }), 500


# ============================================================
# GET QUESTIONS
# ============================================================

@student_bp.route(
    '/submissions/<int:submission_id>/questions',
    methods=['GET']
)
@student_required
def get_submission_questions(submission_id):
    """
    Get exam questions for an active submission.

    IMPORTANT:
    Correct answers are NEVER sent to student here.
    """

    try:
        student = get_current_student()

        if not student:
            return jsonify({
                'message': 'Student not found'
            }), 404

        submission = ExamSubmission.query.get(
            submission_id
        )

        if not submission:
            return jsonify({
                'message': 'Submission not found'
            }), 404

        if submission.student_id != student.id:
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        if submission.status != 'in_progress':
            return jsonify({
                'message': 'Exam has already been submitted'
            }), 403

        exam = Exam.query.get(submission.exam_id)

        if not exam:
            return jsonify({
                'message': 'Exam not found'
            }), 404

        if not check_exam_class_access(student, exam):
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        elapsed_seconds = (
            datetime.utcnow()
            - submission.started_at
        ).total_seconds()

        max_seconds = (
            submission.duration_minutes * 60
        )

        if elapsed_seconds >= max_seconds:

            submission.status = 'auto_submitted'
            submission.submitted_at = datetime.utcnow()
            submission.time_spent_seconds = int(
                max_seconds
            )

            db.session.commit()

            result = _calculate_and_save_result(
                submission
            )

            return jsonify({
                'message': 'Exam time expired',
                'status': 'auto_submitted',
                'result': result.to_dict()
            }), 410

        questions = Question.query.filter_by(
            exam_id=submission.exam_id
        ).order_by(
            Question.order_number
        ).all()

        question_data = []

        for question in questions:

            # IMPORTANT:
            # This does NOT expose is_correct.
            q_data = question.to_dict(
                include_options=True
            )

            student_answer = StudentAnswer.query.filter_by(
                submission_id=submission_id,
                question_id=question.id
            ).first()

            q_data['student_answer'] = (
                student_answer.selected_option_id
                if student_answer
                else None
            )

            question_data.append(q_data)

        remaining_seconds = (
            max_seconds - int(elapsed_seconds)
        )

        return jsonify({
            'questions': question_data,
            'submission_id': submission_id,
            'exam_id': submission.exam_id,
            'remaining_seconds': max(
                0,
                int(remaining_seconds)
            )
        }), 200

    except Exception as e:

        return jsonify({
            'message': 'Failed to fetch questions',
            'error': str(e)
        }), 500


# ============================================================
# SAVE ANSWER
# ============================================================

@student_bp.route(
    '/submissions/<int:submission_id>/answer',
    methods=['POST']
)
@student_required
def submit_answer(submission_id):
    """
    Save/update one student answer.
    """

    try:
        student = get_current_student()

        if not student:
            return jsonify({
                'message': 'Student not found'
            }), 404

        submission = ExamSubmission.query.get(
            submission_id
        )

        if not submission:
            return jsonify({
                'message': 'Submission not found'
            }), 404

        if submission.student_id != student.id:
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        if submission.status != 'in_progress':
            return jsonify({
                'message': 'Exam has already been submitted'
            }), 403

        elapsed_seconds = (
            datetime.utcnow()
            - submission.started_at
        ).total_seconds()

        if elapsed_seconds >= (
            submission.duration_minutes * 60
        ):
            return jsonify({
                'message': 'Exam time expired'
            }), 410

        data = request.get_json()

        if not data:
            return jsonify({
                'message': 'No data provided'
            }), 400

        question_id = data.get(
            'question_id'
        )

        selected_option_id = data.get(
            'selected_option_id'
        )

        if not question_id:
            return jsonify({
                'message': 'Question ID is required'
            }), 400

        question = Question.query.get(
            question_id
        )

        if not question:
            return jsonify({
                'message': 'Question not found'
            }), 404

        if question.exam_id != submission.exam_id:
            return jsonify({
                'message': 'Question does not belong to this exam'
            }), 403

        is_correct = False

        if selected_option_id is not None:

            option = Option.query.get(
                selected_option_id
            )

            if not option:
                return jsonify({
                    'message': 'Option not found'
                }), 404

            if option.question_id != question_id:
                return jsonify({
                    'message': 'Invalid option'
                }), 400

            # Backend knows the correct answer.
            # Student does NOT receive this value.
            is_correct = bool(
                option.is_correct
            )

        student_answer = StudentAnswer.query.filter_by(
            submission_id=submission_id,
            question_id=question_id
        ).first()

        if student_answer:

            student_answer.selected_option_id = (
                selected_option_id
            )

            student_answer.is_correct = (
                is_correct
            )

            student_answer.answered_at = (
                datetime.utcnow()
            )

        else:

            student_answer = StudentAnswer(
                submission_id=submission_id,
                question_id=question_id,
                selected_option_id=selected_option_id,
                is_correct=is_correct
            )

            db.session.add(student_answer)

        db.session.commit()

        return jsonify({
            'message': 'Answer saved successfully',
            'saved_at': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({
            'message': 'Failed to save answer',
            'error': str(e)
        }), 500


# ============================================================
# SUBMISSION STATUS
# ============================================================

@student_bp.route(
    '/submissions/<int:submission_id>/status',
    methods=['GET']
)
@student_required
def get_submission_status(submission_id):
    """
    Get backend-calculated remaining time.
    """

    try:
        student = get_current_student()

        if not student:
            return jsonify({
                'message': 'Student not found'
            }), 404

        submission = ExamSubmission.query.get(
            submission_id
        )

        if not submission:
            return jsonify({
                'message': 'Submission not found'
            }), 404

        if submission.student_id != student.id:
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        elapsed_seconds = int(
            (
                datetime.utcnow()
                - submission.started_at
            ).total_seconds()
        )

        total_seconds = (
            submission.duration_minutes * 60
        )

        remaining_seconds = (
            total_seconds - elapsed_seconds
        )

        is_expired = remaining_seconds <= 0

        return jsonify({
            'submission_id': submission_id,
            'status': submission.status,
            'elapsed_seconds': elapsed_seconds,
            'remaining_seconds': max(
                0,
                remaining_seconds
            ),
            'is_active': (
                submission.status == 'in_progress'
                and not is_expired
            ),
            'is_expired': is_expired
        }), 200

    except Exception as e:

        return jsonify({
            'message': 'Failed to get status',
            'error': str(e)
        }), 500


# ============================================================
# SUBMIT EXAM
# ============================================================

@student_bp.route(
    '/submissions/<int:submission_id>/submit',
    methods=['POST']
)
@student_required
def submit_exam(submission_id):
    """
    Submit exam manually or automatically.
    """

    try:
        student = get_current_student()

        if not student:
            return jsonify({
                'message': 'Student not found'
            }), 404

        submission = ExamSubmission.query.get(
            submission_id
        )

        if not submission:
            return jsonify({
                'message': 'Submission not found'
            }), 404

        if submission.student_id != student.id:
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        if submission.status != 'in_progress':
            return jsonify({
                'message': 'Exam already submitted'
            }), 409

        data = request.get_json() or {}

        auto_submit = bool(
            data.get('auto_submit', False)
        )

        elapsed_seconds = int(
            (
                datetime.utcnow()
                - submission.started_at
            ).total_seconds()
        )

        max_seconds = (
            submission.duration_minutes * 60
        )

        if elapsed_seconds >= max_seconds:
            auto_submit = True

        submission.status = (
            'auto_submitted'
            if auto_submit
            else 'submitted'
        )

        submission.submitted_at = datetime.utcnow()

        submission.time_spent_seconds = min(
            elapsed_seconds,
            max_seconds
        )

        db.session.commit()

        result = _calculate_and_save_result(
            submission
        )

        return jsonify({
            'message': 'Exam submitted successfully',
            'submission_id': submission_id,
            'status': submission.status,
            'result': result.to_dict()
        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({
            'message': 'Failed to submit exam',
            'error': str(e)
        }), 500


# ======================

# ============================================================
# RESULT HISTORY
# ============================================================

@student_bp.route(
    '/results/history',
    methods=['GET']
)
@student_required
def get_result_history():
    """
    Get result history for the logged-in student.
    """

    try:
        student = get_current_student()

        if not student:
            return jsonify({
                'message': 'Student not found'
            }), 404

        results = Result.query.filter_by(
            student_id=student.id
        ).order_by(
            Result.id.desc()
        ).all()

        result_list = []

        for result in results:

            result_data = result.to_dict()

            # Make sure frontend gets submission_id
            result_data['submission_id'] = result.submission_id

            exam = Exam.query.get(result.exam_id)

            if exam:
                result_data['exam_name'] = exam.name
                result_data['exam_id'] = exam.id

            result_list.append(result_data)

        return jsonify({
            'results': result_list
        }), 200

    except Exception as e:

        return jsonify({
            'message': 'Failed to fetch result history',
            'error': str(e)
        }), 500



# ============================================================
# STUDENT ANSWER REVIEW
# ============================================================

@student_bp.route(
    '/results/<int:submission_id>/review',
    methods=['GET']
)
@student_required
def get_result_review(submission_id):
    """
    Get question-wise answer review for a completed exam.

    IMPORTANT:
    Correct answers are available ONLY after submission.
    """

    try:
        student = get_current_student()

        if not student:
            return jsonify({
                'message': 'Student not found'
            }), 404

        # ----------------------------------------------------
        # Get submission
        # ----------------------------------------------------

        submission = ExamSubmission.query.get(
            submission_id
        )

        if not submission:
            return jsonify({
                'message': 'Submission not found'
            }), 404

        # ----------------------------------------------------
        # Student ownership check
        # ----------------------------------------------------

        if submission.student_id != student.id:
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        # ----------------------------------------------------
        # Review allowed only after submission
        # ----------------------------------------------------

        if submission.status not in [
            'submitted',
            'auto_submitted'
        ]:
            return jsonify({
                'message': (
                    'Answer review is available only '
                    'after exam submission'
                )
            }), 403

        # ----------------------------------------------------
        # Get exam
        # ----------------------------------------------------

        exam = Exam.query.get(
            submission.exam_id
        )

        if not exam:
            return jsonify({
                'message': 'Exam not found'
            }), 404

        # ----------------------------------------------------
        # Class access check
        # ----------------------------------------------------

        if not check_exam_class_access(
            student,
            exam
        ):
            return jsonify({
                'message': 'Access forbidden'
            }), 403

        # ----------------------------------------------------
        # Get result
        # ----------------------------------------------------

        result = Result.query.filter_by(
            student_id=student.id,
            exam_id=submission.exam_id
        ).first()

        if not result:
            return jsonify({
                'message': 'Result not found'
            }), 404

        # ----------------------------------------------------
        # Get questions
        # ----------------------------------------------------

        questions = Question.query.filter_by(
            exam_id=submission.exam_id
        ).order_by(
            Question.order_number
        ).all()

        review_list = []

        correct_count = 0
        incorrect_count = 0
        unanswered_count = 0

        # ----------------------------------------------------
        # Build question-wise review
        # ----------------------------------------------------

        for index, question in enumerate(
            questions,
            start=1
        ):

            student_answer = StudentAnswer.query.filter_by(
                submission_id=submission_id,
                question_id=question.id
            ).first()

            # Correct option
            correct_option = Option.query.filter_by(
                question_id=question.id,
                is_correct=True
            ).first()

            # ------------------------------------------------
            # Unanswered
            # ------------------------------------------------

            if (
                not student_answer
                or student_answer.selected_option_id is None
            ):

                answer_status = 'unanswered'

                student_answer_text = None

                unanswered_count += 1

            else:

                selected_option = Option.query.get(
                    student_answer.selected_option_id
                )

                if selected_option:

                    student_answer_text = (
                        selected_option.option_text
                    )

                else:

                    student_answer_text = None

                # --------------------------------------------
                # Correct / Incorrect
                # --------------------------------------------

                if student_answer.is_correct:

                    answer_status = 'correct'

                    correct_count += 1

                else:

                    answer_status = 'incorrect'

                    incorrect_count += 1

            # ------------------------------------------------
            # Correct answer text
            # ------------------------------------------------

            correct_answer_text = None

            if correct_option:
                correct_answer_text = (
                    correct_option.option_text
                )

            # ------------------------------------------------
            # Add review item
            # ------------------------------------------------

            review_list.append({
                'question_id': question.id,

                'question_number': (
                    question.order_number
                    or index
                ),

                'question_text': question.question_text,

                'answer_status': answer_status,

                'student_answer': student_answer_text,

                'student_answer_option_id': (
                    student_answer.selected_option_id
                    if student_answer
                    else None
                ),

                'correct_answer': correct_answer_text,

                'correct_answer_option_id': (
                    correct_option.id
                    if correct_option
                    else None
                )
            })

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return jsonify({

            'review': review_list,

            'summary': {
                'total_questions': len(questions),
                'correct': correct_count,
                'incorrect': incorrect_count,
                'unanswered': unanswered_count
            },

            'result': result.to_dict(),

            'exam': {
                'id': exam.id,
                'name': exam.name
            },

            'submission': {
                'id': submission.id,
                'status': submission.status,
                'submitted_at': (
                    submission.submitted_at.isoformat()
                    if submission.submitted_at
                    else None
                )
            }

        }), 200

    except Exception as e:

        return jsonify({
            'message': 'Failed to load answer review',
            'error': str(e)
        }), 500