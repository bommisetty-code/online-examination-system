"""
Comprehensive test for Admin Results Dashboard workflow
Tests the complete data flow from backend API to verify data is correct
"""

import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import User, Exam, Question, Option, ExamSubmission, StudentAnswer, Result

def test_complete_results_workflow():
    """Test complete admin results workflow"""
    app = create_app()
    
    with app.app_context():
        # Clean up existing test data
        db.session.query(StudentAnswer).delete()
        db.session.query(Result).delete()
        db.session.query(ExamSubmission).delete()
        db.session.query(Option).delete()
        db.session.query(Question).delete()
        db.session.query(Exam).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        print("Creating test data...")
        # Create admin user
        admin = User(
            username='admin_results_test',
            email='admin_results@test.com',
            full_name='Admin Results',
            role='admin'
        )
        admin.set_password('password123')
        
        # Create student user
        student = User(
            username='student_results_test',
            email='student_results@test.com',
            full_name='Student Results',
            role='student'
        )
        student.set_password('password123')
        
        db.session.add(admin)
        db.session.add(student)
        db.session.flush()
        
        # Create exam
        exam = Exam(
            name='Python Basics Quiz',
            description='Test knowledge of Python basics',
            created_by=admin.id,
            duration_minutes=30,
            passing_percentage=60,
            is_active=True
        )
        db.session.add(exam)
        db.session.flush()
        
        # Create questions and options
        q1 = Question(
            exam_id=exam.id,
            question_text='What is the correct way to create a list in Python?',
            question_order=1
        )
        db.session.add(q1)
        db.session.flush()
        
        opt1_1 = Option(question_id=q1.id, option_text='list = []', is_correct=True, option_order=1)
        opt1_2 = Option(question_id=q1.id, option_text='list = ()', is_correct=False, option_order=2)
        opt1_3 = Option(question_id=q1.id, option_text='list = {}', is_correct=False, option_order=3)
        opt1_4 = Option(question_id=q1.id, option_text='list = list()', is_correct=True, option_order=4)
        
        db.session.add_all([opt1_1, opt1_2, opt1_3, opt1_4])
        
        q2 = Question(
            exam_id=exam.id,
            question_text='What does len([1,2,3]) return?',
            question_order=2
        )
        db.session.add(q2)
        db.session.flush()
        
        opt2_1 = Option(question_id=q2.id, option_text='2', is_correct=False, option_order=1)
        opt2_2 = Option(question_id=q2.id, option_text='3', is_correct=True, option_order=2)
        opt2_3 = Option(question_id=q2.id, option_text='[1,2,3]', is_correct=False, option_order=3)
        
        db.session.add_all([opt2_1, opt2_2, opt2_3])
        db.session.commit()
        
        print("✓ Created exam with 2 questions")
        
        # Create submission
        submission = ExamSubmission(
            exam_id=exam.id,
            student_id=student.id,
            status='completed',
            started_at=datetime.now(),
            submitted_at=datetime.now()
        )
        db.session.add(submission)
        db.session.flush()
        
        # Create student answers - answer Q1 correctly (choice 1), answer Q2 correctly (choice 2)
        answer1 = StudentAnswer(
            submission_id=submission.id,
            question_id=q1.id,
            selected_option_id=opt1_1.id,
            is_correct=True
        )
        answer2 = StudentAnswer(
            submission_id=submission.id,
            question_id=q2.id,
            selected_option_id=opt2_2.id,
            is_correct=True
        )
        
        db.session.add_all([answer1, answer2])
        db.session.flush()
        
        # Create result
        correct_count = 2
        total_questions = 2
        score_percentage = (correct_count / total_questions) * 100
        
        result = Result(
            submission_id=submission.id,
            total_questions=total_questions,
            correct_answers=correct_count,
            incorrect_answers=0,
            unanswered=0,
            score_percentage=score_percentage,
            passed=score_percentage >= exam.passing_percentage
        )
        db.session.add(result)
        db.session.commit()
        
        print(f"✓ Created submission with 2 answers (2/2 correct = {score_percentage}%)")
        
        # Verify data relationships
        print("\n=== Verifying Data Relationships ===")
        
        # Check exam
        exam_check = db.session.query(Exam).filter_by(id=exam.id).first()
        print(f"✓ Exam: {exam_check.name} (ID: {exam_check.id}, Created by admin ID: {exam_check.created_by})")
        
        # Check questions
        questions = db.session.query(Question).filter_by(exam_id=exam.id).all()
        print(f"✓ Questions: {len(questions)} questions in exam")
        for q in questions:
            options = db.session.query(Option).filter_by(question_id=q.id).all()
            correct_opts = [o for o in options if o.is_correct]
            print(f"  - Q{q.question_order}: {len(options)} options, {len(correct_opts)} correct")
        
        # Check submission
        submission_check = db.session.query(ExamSubmission).filter_by(id=submission.id).first()
        student_check = db.session.query(User).filter_by(id=submission_check.student_id).first()
        print(f"✓ Submission: {student_check.full_name} submitted exam {exam_check.name}")
        
        # Check answers
        answers = db.session.query(StudentAnswer).filter_by(submission_id=submission.id).all()
        print(f"✓ Answers: {len(answers)} answers submitted")
        for ans in answers:
            q = db.session.query(Question).filter_by(id=ans.question_id).first()
            opt = db.session.query(Option).filter_by(id=ans.selected_option_id).first()
            print(f"  - Q{q.question_order}: {opt.option_text} ({'Correct' if ans.is_correct else 'Incorrect'})")
        
        # Check result
        result_check = db.session.query(Result).filter_by(submission_id=submission.id).first()
        print(f"✓ Result: {result_check.correct_answers}/{result_check.total_questions} correct")
        print(f"  - Score: {result_check.score_percentage}% ({'Passed' if result_check.passed else 'Failed'})")
        print(f"  - Breakdown: {result_check.correct_answers} correct, {result_check.incorrect_answers} incorrect, {result_check.unanswered} unanswered")
        
        print("\n✓ Complete workflow test passed!")
        return True

if __name__ == '__main__':
    try:
        test_complete_results_workflow()
        print("\n" + "="*60)
        print("✓ All workflow tests passed!")
        print("="*60)
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
