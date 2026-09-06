"""
Comprehensive Security Audit Test Suite
Tests all security requirements for the Online Examination System
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import User, Exam, Question, Option, ExamSubmission, StudentAnswer, Result
from datetime import datetime, timedelta
from decimal import Decimal
import json

# ============================================================================
# TEST SETUP
# ============================================================================

class SecurityTest:
    def __init__(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Test users and data
        self.admin1 = None
        self.admin2 = None
        self.student1 = None
        self.student2 = None
        self.exam1 = None
        self.exam2 = None
        self.submission1 = None
        self.token_admin1 = None
        self.token_admin2 = None
        self.token_student1 = None
        self.token_student2 = None
        
        self.setup_test_data()
    
    def setup_test_data(self):
        """Create test users and data"""
        # Admin users
        self.admin1 = User(
            username='admin1',
            email='admin1@test.com',
            full_name='Admin One',
            role='admin'
        )
        self.admin1.set_password('admin1pass')
        
        self.admin2 = User(
            username='admin2',
            email='admin2@test.com',
            full_name='Admin Two',
            role='admin'
        )
        self.admin2.set_password('admin2pass')
        
        # Student users
        self.student1 = User(
            username='student1',
            email='student1@test.com',
            full_name='Student One',
            role='student'
        )
        self.student1.set_password('student1pass')
        
        self.student2 = User(
            username='student2',
            email='student2@test.com',
            full_name='Student Two',
            role='student'
        )
        self.student2.set_password('student2pass')
        
        db.session.add_all([self.admin1, self.admin2, self.student1, self.student2])
        db.session.flush()
        
        # Create exam by admin1
        self.exam1 = Exam(
            name='Security Test Exam',
            description='Test exam for security',
            duration_minutes=30,
            created_by=self.admin1.id,
            is_active=True,
            passing_percentage=50
        )
        db.session.add(self.exam1)
        db.session.flush()
        
        # Create questions
        q1 = Question(
            exam_id=self.exam1.id,
            question_text='Q1?',
            order_number=1
        )
        q2 = Question(
            exam_id=self.exam1.id,
            question_text='Q2?',
            order_number=2
        )
        db.session.add_all([q1, q2])
        db.session.flush()
        
        # Create options with correct answers
        opt1_correct = Option(
            question_id=q1.id,
            option_text='Q1 Correct',
            option_order=1,
            is_correct=True
        )
        opt1_incorrect = Option(
            question_id=q1.id,
            option_text='Q1 Incorrect',
            option_order=2,
            is_correct=False
        )
        opt2_correct = Option(
            question_id=q2.id,
            option_text='Q2 Correct',
            option_order=1,
            is_correct=True
        )
        db.session.add_all([opt1_correct, opt1_incorrect, opt2_correct])
        db.session.commit()
        
        # Get tokens
        self.token_admin1 = self._login('admin1', 'admin1pass')
        self.token_admin2 = self._login('admin2', 'admin2pass')
        self.token_student1 = self._login('student1', 'student1pass')
        self.token_student2 = self._login('student2', 'student2pass')
    
    def _login(self, username, password):
        """Helper to login and get token"""
        resp = self.client.post('/api/auth/login', json={
            'username': username,
            'password': password
        })
        if resp.status_code == 200:
            return resp.get_json()['access_token']
        return None
    
    def _get_headers(self, token=None):
        """Get auth headers"""
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        return headers
    
    def cleanup(self):
        """Cleanup test database"""
        db.session.close()
        db.drop_all()
        self.app_context.pop()
    
    # ========================================================================
    # SECURITY TESTS
    # ========================================================================
    
    def test_1_auth_password_hashing(self):
        """Test that passwords are hashed and never returned"""
        print("\n[TEST 1] Password Hashing")
        
        # Try to get user profile
        resp = self.client.get('/api/auth/profile', 
                               headers=self._get_headers(self.token_student1))
        
        user_data = resp.get_json()['user']
        
        # Verify password_hash is not in response
        if 'password_hash' in user_data:
            print("  ✗ FAIL: password_hash leaked in response")
            return False
        
        # Verify password field is not in response
        if 'password' in user_data:
            print("  ✗ FAIL: password leaked in response")
            return False
        
        print("  ✓ PASS: Passwords not returned in API response")
        return True
    
    def test_2_student_cannot_access_admin_apis(self):
        """Test that students cannot access admin APIs"""
        print("\n[TEST 2] Student Cannot Access Admin APIs")
        
        # Try to get admin exams
        resp = self.client.get('/api/admin/exams',
                               headers=self._get_headers(self.token_student1))
        
        if resp.status_code != 403:
            print(f"  ✗ FAIL: Expected 403, got {resp.status_code}")
            return False
        
        # Try to create exam
        resp = self.client.post('/api/admin/exams',
                                headers=self._get_headers(self.token_student1),
                                json={'name': 'Hacked Exam', 'duration_minutes': 60})
        
        if resp.status_code != 403:
            print(f"  ✗ FAIL: Expected 403, got {resp.status_code}")
            return False
        
        print("  ✓ PASS: Students correctly denied admin API access")
        return True
    
    def test_3_unauthenticated_cannot_access_protected_apis(self):
        """Test that unauthenticated users cannot access protected APIs"""
        print("\n[TEST 3] Unauthenticated Users Blocked")
        
        # Try to get exams without token
        resp = self.client.get('/api/student/exams',
                               headers={'Content-Type': 'application/json'})
        
        if resp.status_code not in [401, 422]:  # 422 is Unprocessable Entity for missing JWT
            print(f"  ✗ FAIL: Expected 401/422, got {resp.status_code}")
            return False
        
        print("  ✓ PASS: Unauthenticated access blocked")
        return True
    
    def test_4_student_cannot_access_other_student_results(self):
        """Test IDOR: Student cannot access another student's results"""
        print("\n[TEST 4] Student Cannot Access Other Student's Results (IDOR)")
        
        try:
            # Create submission for student1
            submission = ExamSubmission(
                student_id=self.student1.id,
                exam_id=self.exam1.id,
                duration_minutes=30,
                status='submitted',
                submitted_at=datetime.utcnow()
            )
            db.session.add(submission)
            db.session.flush()
        
        # Create result for student1
        result = Result(
            submission_id=submission.id,
            student_id=self.student1.id,
            exam_id=self.exam1.id,
            total_questions=2,
            correct_answers=1,
            incorrect_answers=1,
            unanswered=0,
            score=1,
            total_marks=2,
            percentage=Decimal('50.00'),
            is_passed=True,
            submitted_at=datetime.utcnow()
        )
        db.session.add(result)
        db.session.commit()
        
        # Try to access student1's result as student2
        resp = self.client.get(f'/api/student/results/{submission.id}',
                               headers=self._get_headers(self.token_student2))
        
        if resp.status_code != 403:
            print(f"  ✗ FAIL: Expected 403, got {resp.status_code}")
            return False
        
        print("  ✓ PASS: Student cannot access other student's results")
        return True
    
    def test_5_student_cannot_access_other_student_submission(self):
        """Test that student cannot access another student's submission"""
        print("\n[TEST 5] Student Cannot Access Other Student's Submission")
        
        # Create submission for student1
        submission = ExamSubmission(
            student_id=self.student1.id,
            exam_id=self.exam1.id,
            duration_minutes=30,
            status='in_progress'
        )
        db.session.add(submission)
        db.session.commit()
        
        # Try to get questions for student1's submission as student2
        resp = self.client.get(f'/api/student/submissions/{submission.id}/questions',
                               headers=self._get_headers(self.token_student2))
        
        if resp.status_code != 403:
            print(f"  ✗ FAIL: Expected 403, got {resp.status_code}")
            return False
        
        print("  ✓ PASS: Student cannot access other student's submission")
        return True
    
    def test_6_correct_answers_never_leaked(self):
        """Test that correct answers are never returned to students"""
        print("\n[TEST 6] Correct Answers Never Leaked to Students")
        
        # Start exam
        resp = self.client.post(f'/api/student/exams/{self.exam1.id}/start',
                                headers=self._get_headers(self.token_student1))
        
        if resp.status_code != 201:
            print(f"  ✗ FAIL: Could not start exam: {resp.status_code}")
            return False
        
        submission_id = resp.get_json()['submission_id']
        
        # Get questions
        resp = self.client.get(f'/api/student/submissions/{submission_id}/questions',
                               headers=self._get_headers(self.token_student1))
        
        questions = resp.get_json()['questions']
        
        # Verify is_correct is not in options
        for q in questions:
            for opt in q.get('options', []):
                if 'is_correct' in opt:
                    print(f"  ✗ FAIL: is_correct leaked in option for question {q['id']}")
                    return False
        
        print("  ✓ PASS: Correct answers not leaked in question options")
        return True
    
    def test_7_duplicate_exam_attempts_prevented(self):
        """Test that unique constraint prevents duplicate exam attempts"""
        print("\n[TEST 7] Duplicate Exam Attempts Prevented")
        
        # Try to create two submissions for same student/exam
        sub1 = ExamSubmission(
            student_id=self.student1.id,
            exam_id=self.exam1.id,
            duration_minutes=30,
            status='submitted'
        )
        db.session.add(sub1)
        db.session.flush()
        
        # Mark as result complete
        result = Result(
            submission_id=sub1.id,
            student_id=self.student1.id,
            exam_id=self.exam1.id,
            total_questions=2,
            correct_answers=0,
            incorrect_answers=0,
            unanswered=2,
            score=0,
            total_marks=2,
            percentage=Decimal('0.00'),
            is_passed=False,
            submitted_at=datetime.utcnow()
        )
        db.session.add(result)
        db.session.commit()
        
        # Try to start same exam again
        resp = self.client.post(f'/api/student/exams/{self.exam1.id}/start',
                                headers=self._get_headers(self.token_student1))
        
        if resp.status_code != 409:  # Conflict
            print(f"  ✗ FAIL: Expected 409, got {resp.status_code}")
            print(f"       Response: {resp.get_json()}")
            return False
        
        print("  ✓ PASS: Duplicate attempt prevented")
        return True
    
    def test_8_submitted_answers_cannot_be_changed(self):
        """Test that answers cannot be changed after submission"""
        print("\n[TEST 8] Submitted Answers Cannot Be Changed")
        
        # Create a new student submission that's already submitted
        submission = ExamSubmission(
            student_id=self.student2.id,
            exam_id=self.exam1.id,
            duration_minutes=30,
            status='submitted',
            submitted_at=datetime.utcnow()
        )
        db.session.add(submission)
        db.session.commit()
        
        # Try to submit answer to submitted exam
        question = Question.query.filter_by(exam_id=self.exam1.id).first()
        option = Option.query.filter_by(question_id=question.id).first()
        
        resp = self.client.post(f'/api/student/submissions/{submission.id}/answer',
                                headers=self._get_headers(self.token_student2),
                                json={'question_id': question.id, 'selected_option_id': option.id})
        
        if resp.status_code != 403:
            print(f"  ✗ FAIL: Expected 403, got {resp.status_code}")
            return False
        
        print("  ✓ PASS: Submitted exam cannot accept new answers")
        return True
    
    def test_9_expired_exam_cannot_accept_answers(self):
        """Test that expired exam cannot accept answers"""
        print("\n[TEST 9] Expired Exam Cannot Accept Answers")
        
        # Create submission that started 40 minutes ago (duration 30 minutes)
        submission = ExamSubmission(
            student_id=self.student1.id,
            exam_id=self.exam1.id,
            duration_minutes=30,
            status='in_progress',
            started_at=datetime.utcnow() - timedelta(minutes=40)
        )
        db.session.add(submission)
        db.session.commit()
        
        # Try to submit answer to expired exam
        question = Question.query.filter_by(exam_id=self.exam1.id).first()
        option = Option.query.filter_by(question_id=question.id).first()
        
        resp = self.client.post(f'/api/student/submissions/{submission.id}/answer',
                                headers=self._get_headers(self.token_student1),
                                json={'question_id': question.id, 'selected_option_id': option.id})
        
        if resp.status_code != 410:  # Gone (expired)
            print(f"  ✗ FAIL: Expected 410, got {resp.status_code}")
            return False
        
        print("  ✓ PASS: Expired exam rejected new answers")
        return True
    
    def test_10_admin_cannot_access_other_admin_exams(self):
        """Test that admin can only access their own exams"""
        print("\n[TEST 10] Admin Cannot Access Other Admin's Exams")
        
        # Create exam by admin1
        exam = Exam(
            name='Admin1 Exam',
            description='Exam by admin1',
            duration_minutes=30,
            created_by=self.admin1.id,
            is_active=True
        )
        db.session.add(exam)
        db.session.commit()
        
        # Try to access admin1's exam as admin2
        resp = self.client.get(f'/api/admin/exams/{exam.id}',
                               headers=self._get_headers(self.token_admin2))
        
        if resp.status_code != 403:
            print(f"  ✗ FAIL: Expected 403, got {resp.status_code}")
            return False
        
        print("  ✓ PASS: Admin can only access own exams")
        return True
    
    def test_11_answer_validation_question_belongs_to_exam(self):
        """Test that answer validation checks question belongs to exam"""
        print("\n[TEST 11] Answer Validation - Question Belongs to Exam")
        
        # Create second exam
        exam2 = Exam(
            name='Exam 2',
            description='Second exam',
            duration_minutes=30,
            created_by=self.admin1.id,
            is_active=True
        )
        db.session.add(exam2)
        db.session.flush()
        
        # Create question for exam2
        q = Question(exam_id=exam2.id, question_text='Q?', order_number=1)
        db.session.add(q)
        db.session.commit()
        
        # Start exam1
        resp = self.client.post(f'/api/student/exams/{self.exam1.id}/start',
                                headers=self._get_headers(self.token_student1))
        submission_id = resp.get_json()['submission_id']
        
        # Try to answer with question from exam2
        resp = self.client.post(f'/api/student/submissions/{submission_id}/answer',
                                headers=self._get_headers(self.token_student1),
                                json={'question_id': q.id, 'selected_option_id': None})
        
        if resp.status_code != 404:
            print(f"  ✗ FAIL: Expected 404, got {resp.status_code}")
            return False
        
        print("  ✓ PASS: Answer validation prevents cross-exam cheating")
        return True
    
    def test_12_answer_validation_option_belongs_to_question(self):
        """Test that option validation checks option belongs to question"""
        print("\n[TEST 12] Answer Validation - Option Belongs to Question")
        
        # Get question from exam1
        q1 = Question.query.filter_by(exam_id=self.exam1.id).first()
        q2 = Question.query.filter_by(exam_id=self.exam1.id).offset(1).first()
        
        if not q2:
            print("  ⊘ SKIP: Not enough questions for test")
            return True
        
        # Get option from q2
        opt_q2 = Option.query.filter_by(question_id=q2.id).first()
        
        # Start exam
        resp = self.client.post(f'/api/student/exams/{self.exam1.id}/start',
                                headers=self._get_headers(self.token_student1))
        
        # Try to answer q1 with option from q2
        resp = self.client.post(f'/api/student/submissions/{resp.get_json()["submission_id"]}/answer',
                                headers=self._get_headers(self.token_student1),
                                json={'question_id': q1.id, 'selected_option_id': opt_q2.id})
        
        if resp.status_code != 400:
            print(f"  ✗ FAIL: Expected 400, got {resp.status_code}")
            return False
        
        print("  ✓ PASS: Option validation prevents cross-question answers")
        return True
    
    def test_13_backend_calculates_score(self):
        """Test that backend calculates score, not frontend"""
        print("\n[TEST 13] Backend Calculates Score (Not Frontend)")
        
        # This is implicit - if frontend can't POST a score, it's working
        # Start exam, submit answers, verify result
        resp = self.client.post(f'/api/student/exams/{self.exam1.id}/start',
                                headers=self._get_headers(self.token_student1))
        submission_id = resp.get_json()['submission_id']
        
        # Get questions
        resp = self.client.get(f'/api/student/submissions/{submission_id}/questions',
                               headers=self._get_headers(self.token_student1))
        questions = resp.get_json()['questions']
        
        # Answer all questions
        for q in questions:
            opts = q.get('options', [])
            if opts:
                resp = self.client.post(f'/api/student/submissions/{submission_id}/answer',
                                        headers=self._get_headers(self.token_student1),
                                        json={'question_id': q['id'], 'selected_option_id': opts[0]['id']})
        
        # Submit
        resp = self.client.post(f'/api/student/submissions/{submission_id}/submit',
                                headers=self._get_headers(self.token_student1),
                                json={})
        
        result = resp.get_json()['result']
        
        # Verify score was calculated (should be 1 correct if we got first option, which might not be correct)
        if 'score' not in result or 'percentage' not in result:
            print("  ✗ FAIL: Score/percentage not in result")
            return False
        
        print("  ✓ PASS: Backend calculates and returns score")
        return True
    
    # ========================================================================
    # RUN ALL TESTS
    # ========================================================================
    
    def run_all_tests(self):
        """Run all security tests"""
        print("\n" + "="*70)
        print("COMPREHENSIVE SECURITY AUDIT TEST SUITE")
        print("="*70)
        
        tests = [
            self.test_1_auth_password_hashing,
            self.test_2_student_cannot_access_admin_apis,
            self.test_3_unauthenticated_cannot_access_protected_apis,
            self.test_4_student_cannot_access_other_student_results,
            self.test_5_student_cannot_access_other_student_submission,
            self.test_6_correct_answers_never_leaked,
            self.test_7_duplicate_exam_attempts_prevented,
            self.test_8_submitted_answers_cannot_be_changed,
            self.test_9_expired_exam_cannot_accept_answers,
            self.test_10_admin_cannot_access_other_admin_exams,
            self.test_11_answer_validation_question_belongs_to_exam,
            self.test_12_answer_validation_option_belongs_to_question,
            self.test_13_backend_calculates_score,
        ]
        
        passed = 0
        failed = 0
        skipped = 0
        
        for test in tests:
            try:
                result = test()
                if result is True:
                    passed += 1
                elif result is False:
                    failed += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"  ✗ EXCEPTION: {str(e)}")
                import traceback
                traceback.print_exc()
                failed += 1
        
        print("\n" + "="*70)
        print(f"RESULTS: {passed} passed, {failed} failed, {skipped} skipped")
        print("="*70)
        
        return failed == 0

if __name__ == '__main__':
    tester = SecurityTest()
    try:
        success = tester.run_all_tests()
        tester.cleanup()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        tester.cleanup()
        sys.exit(1)
