"""Test data creation for results API testing"""
import sys
sys.path.insert(0, '.')

from app import create_app, db
from app.models import User, Exam, Question, Option, ExamSubmission, StudentAnswer, Result
from datetime import datetime, timedelta

# Create test app
app = create_app('testing')

with app.app_context():
    # Create test admin
    admin = User(
        email='admin@test.com',
        username='testadmin',
        full_name='Test Admin',
        role='admin',
        is_active=True
    )
    admin.set_password('Password1')
    db.session.add(admin)
    db.session.flush()

    # Create test student
    student = User(
        email='student@test.com',
        username='teststudent',
        full_name='Test Student',
        role='student',
        is_active=True
    )
    student.set_password('Password1')
    db.session.add(student)
    db.session.flush()

    # Create test exam
    exam = Exam(
        name='Test Exam',
        description='Test Exam Description',
        duration_minutes=30,
        created_by=admin.id,
        is_active=True,
        total_questions=2,
        passing_percentage=50.0,
        exam_code='TEST001'
    )
    db.session.add(exam)
    db.session.flush()

    # Create test questions
    q1 = Question(
        exam_id=exam.id,
        question_text='What is 2+2?',
        marks=1,
        order_number=1
    )
    db.session.add(q1)
    db.session.flush()

    q2 = Question(
        exam_id=exam.id,
        question_text='What is 3+3?',
        marks=1,
        order_number=2
    )
    db.session.add(q2)
    db.session.flush()

    # Create options
    opt1_correct = Option(question_id=q1.id, option_text='4', option_order=1, is_correct=True)
    opt1_wrong = Option(question_id=q1.id, option_text='5', option_order=2, is_correct=False)
    db.session.add_all([opt1_correct, opt1_wrong])
    db.session.flush()

    opt2_correct = Option(question_id=q2.id, option_text='6', option_order=1, is_correct=True)
    opt2_wrong = Option(question_id=q2.id, option_text='7', option_order=2, is_correct=False)
    db.session.add_all([opt2_correct, opt2_wrong])
    db.session.flush()

    # Create submission
    submission = ExamSubmission(
        student_id=student.id,
        exam_id=exam.id,
        duration_minutes=30,
        status='submitted',
        started_at=datetime.utcnow() - timedelta(minutes=5),
        submitted_at=datetime.utcnow(),
        time_spent_seconds=300,
        ip_address='127.0.0.1',
        user_agent='Test'
    )
    db.session.add(submission)
    db.session.flush()

    # Create student answers (1 correct, 1 incorrect)
    answer1 = StudentAnswer(
        submission_id=submission.id,
        question_id=q1.id,
        selected_option_id=opt1_correct.id,
        is_correct=True
    )
    answer2 = StudentAnswer(
        submission_id=submission.id,
        question_id=q2.id,
        selected_option_id=opt2_wrong.id,
        is_correct=False
    )
    db.session.add_all([answer1, answer2])
    db.session.flush()

    # Create result
    result = Result(
        submission_id=submission.id,
        student_id=student.id,
        exam_id=exam.id,
        total_questions=2,
        correct_answers=1,
        incorrect_answers=1,
        unanswered=0,
        score=1,
        total_marks=2,
        percentage=50.0,
        is_passed=True,
        submitted_at=datetime.utcnow()
    )
    db.session.add(result)
    db.session.commit()

    print("✓ Test data created successfully")
    print(f"  Admin ID: {admin.id}, Student ID: {student.id}")
    print(f"  Exam ID: {exam.id}, Submission ID: {submission.id}")
    print(f"  Results: {result.correct_answers}/{result.total_questions} = {result.percentage}%")
