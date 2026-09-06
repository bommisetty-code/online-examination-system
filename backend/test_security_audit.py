"""
Security Audit Test Suite - Simplified
Tests key security requirements for the Online Examination System
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import User, Exam, Question, Option, ExamSubmission, Result
from datetime import datetime, timedelta
from decimal import Decimal

class SecurityAuditTests:
    def __init__(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        self.admin_token = None
        self.student1_token = None
        self.student2_token = None
        
        self._setup()
    
    def _setup(self):
        """Setup test data"""
        # Create admin
        admin = User(username='admin', email='admin@test.com', role='admin', full_name='Admin')
        admin.set_password('adminpass')
        
        # Create students
        student1 = User(username='student1', email='student1@test.com', role='student', full_name='S1')
        student1.set_password('pass1')
        
        student2 = User(username='student2', email='student2@test.com', role='student', full_name='S2')
        student2.set_password('pass2')
        
        db.session.add_all([admin, student1, student2])
        db.session.commit()
        
        # Login
        r = self.client.post('/api/auth/login', json={'username': 'admin', 'password': 'adminpass'})
        self.admin_token = r.get_json()['access_token']
        
        r = self.client.post('/api/auth/login', json={'username': 'student1', 'password': 'pass1'})
        self.student1_token = r.get_json()['access_token']
        
        r = self.client.post('/api/auth/login', json={'username': 'student2', 'password': 'pass2'})
        self.student2_token = r.get_json()['access_token']
    
    def _h(self, token=None):
        """Helper: get headers"""
        h = {'Content-Type': 'application/json'}
        if token:
            h['Authorization'] = f'Bearer {token}'
        return h
    
    def cleanup(self):
        """Cleanup"""
        db.session.close()
        db.drop_all()
        self.app_context.pop()
    
    # ========================================================================
    # TESTS
    # ========================================================================
    
    def test_auth_password_not_leaked(self):
        """TEST 1: Password never in API response"""
        print("\n[TEST 1] Password Never Leaked")
        resp = self.client.get('/api/auth/profile', headers=self._h(self.student1_token))
        user_data = resp.get_json()['user']
        
        if 'password_hash' in user_data or 'password' in user_data:
            print("  ✗ FAIL: Password leaked")
            return False
        
        print("  ✓ PASS: Password not leaked")
        return True
    
    def test_student_cannot_access_admin_apis(self):
        """TEST 2: Student blocked from admin endpoints"""
        print("\n[TEST 2] Student Cannot Access Admin APIs")
        
        r = self.client.get('/api/admin/exams', headers=self._h(self.student1_token))
        if r.status_code != 403:
            print(f"  ✗ FAIL: Got {r.status_code}, expected 403")
            return False
        
        r = self.client.post('/api/admin/exams', headers=self._h(self.student1_token),
                             json={'name': 'X', 'duration_minutes': 10})
        if r.status_code != 403:
            print(f"  ✗ FAIL: Got {r.status_code}, expected 403")
            return False
        
        print("  ✓ PASS: Student blocked from admin APIs")
        return True
    
    def test_unauthenticated_blocked(self):
        """TEST 3: Unauthenticated users blocked"""
        print("\n[TEST 3] Unauthenticated Users Blocked")
        
        r = self.client.get('/api/student/exams')
        if r.status_code not in [401, 422]:
            print(f"  ✗ FAIL: Got {r.status_code}, expected 401/422")
            return False
        
        print("  ✓ PASS: Unauthenticated blocked")
        return True
    
    def test_correct_answers_not_leaked(self):
        """TEST 4: Correct answers never returned to students"""
        print("\n[TEST 4] Correct Answers Not Leaked to Students")
        
        # Create exam
        admin_id = db.session.query(User).filter_by(username='admin').first().id
        
        exam = Exam(name='Test Exam', duration_minutes=30, created_by=admin_id, is_active=True)
        db.session.add(exam)
        db.session.flush()
        
        q = Question(exam_id=exam.id, question_text='Q1?', order_number=1)
        db.session.add(q)
        db.session.flush()
        
        opt = Option(question_id=q.id, option_text='Opt', option_order=1, is_correct=True)
        db.session.add(opt)
        db.session.commit()
        
        # Start exam as student1
        student1_id = db.session.query(User).filter_by(username='student1').first().id
        r = self.client.post(f'/api/student/exams/{exam.id}/start', headers=self._h(self.student1_token))
        
        if r.status_code != 201:
            print(f"  ✗ FAIL: Could not start exam: {r.status_code}")
            return False
        
        sub_id = r.get_json()['submission_id']
        
        # Get questions
        r = self.client.get(f'/api/student/submissions/{sub_id}/questions', headers=self._h(self.student1_token))
        questions = r.get_json()['questions']
        
        # Check that is_correct is not in options
        for q in questions:
            for opt in q.get('options', []):
                if 'is_correct' in opt:
                    print(f"  ✗ FAIL: is_correct leaked in option")
                    return False
        
        print("  ✓ PASS: Correct answers not leaked")
        return True
    
    def test_submitted_exam_cannot_change(self):
        """TEST 5: Submitted exam cannot accept new answers"""
        print("\n[TEST 5] Submitted Exam Cannot Accept Changes")
        
        admin_id = db.session.query(User).filter_by(username='admin').first().id
        student_id = db.session.query(User).filter_by(username='student2').first().id
        
        # Create exam
        exam = Exam(name='Test Exam 2', duration_minutes=30, created_by=admin_id, is_active=True)
        db.session.add(exam)
        db.session.flush()
        
        q = Question(exam_id=exam.id, question_text='Q1?', order_number=1)
        db.session.add(q)
        db.session.flush()
        
        opt = Option(question_id=q.id, option_text='Opt', option_order=1, is_correct=True)
        db.session.add(opt)
        db.session.flush()
        
        # Create submitted submission
        sub = ExamSubmission(student_id=student_id, exam_id=exam.id, duration_minutes=30,
                            status='submitted', submitted_at=datetime.utcnow())
        db.session.add(sub)
        db.session.commit()
        
        # Try to answer
        r = self.client.post(f'/api/student/submissions/{sub.id}/answer',
                            headers=self._h(self.student2_token),
                            json={'question_id': q.id, 'selected_option_id': opt.id})
        
        if r.status_code != 403:
            print(f"  ✗ FAIL: Got {r.status_code}, expected 403")
            return False
        
        print("  ✓ PASS: Submitted exam blocked")
        return True
    
    def test_student_cannot_access_other_student_result(self):
        """TEST 6: Student cannot access other student's result (IDOR)"""
        print("\n[TEST 6] Student Cannot Access Other Student's Result")
        
        admin_id = db.session.query(User).filter_by(username='admin').first().id
        student1_id = db.session.query(User).filter_by(username='student1').first().id
        
        # Create exam
        exam = Exam(name='Test Exam 3', duration_minutes=30, created_by=admin_id, is_active=True)
        db.session.add(exam)
        db.session.flush()
        
        # Create submission + result for student1
        sub = ExamSubmission(student_id=student1_id, exam_id=exam.id, duration_minutes=30,
                            status='submitted', submitted_at=datetime.utcnow())
        db.session.add(sub)
        db.session.flush()
        
        result = Result(submission_id=sub.id, student_id=student1_id, exam_id=exam.id,
                       total_questions=1, correct_answers=0, incorrect_answers=1, unanswered=0,
                       score=0, total_marks=1, percentage=Decimal('0.00'), is_passed=False,
                       submitted_at=datetime.utcnow())
        db.session.add(result)
        db.session.commit()
        
        # Try to access as student2
        r = self.client.get(f'/api/student/results/{sub.id}', headers=self._h(self.student2_token))
        
        if r.status_code != 403:
            print(f"  ✗ FAIL: Got {r.status_code}, expected 403")
            return False
        
        print("  ✓ PASS: Student cannot access other student's result")
        return True
    
    def test_expired_exam_rejected(self):
        """TEST 7: Expired exam rejects new answers"""
        print("\n[TEST 7] Expired Exam Rejects Answers")
        
        admin_id = db.session.query(User).filter_by(username='admin').first().id
        student_id = db.session.query(User).filter_by(username='student1').first().id
        
        # Create exam
        exam = Exam(name='Test Exam 4', duration_minutes=30, created_by=admin_id, is_active=True)
        db.session.add(exam)
        db.session.flush()
        
        q = Question(exam_id=exam.id, question_text='Q1?', order_number=1)
        db.session.add(q)
        db.session.flush()
        
        opt = Option(question_id=q.id, option_text='Opt', option_order=1, is_correct=True)
        db.session.add(opt)
        db.session.flush()
        
        # Create submission started 40 minutes ago (duration 30)
        sub = ExamSubmission(student_id=student_id, exam_id=exam.id, duration_minutes=30,
                            status='in_progress',
                            started_at=datetime.utcnow() - timedelta(minutes=40))
        db.session.add(sub)
        db.session.commit()
        
        # Try to answer
        r = self.client.post(f'/api/student/submissions/{sub.id}/answer',
                            headers=self._h(self.student1_token),
                            json={'question_id': q.id, 'selected_option_id': opt.id})
        
        if r.status_code != 410:  # 410 Gone
            print(f"  ✗ FAIL: Got {r.status_code}, expected 410")
            return False
        
        print("  ✓ PASS: Expired exam rejected")
        return True
    
    def test_admin_authorization(self):
        """TEST 8: Admin can only access own exams"""
        print("\n[TEST 8] Admin Authorization (Own Exams Only)")
        
        admin_id = db.session.query(User).filter_by(username='admin').first().id
        
        # Create exam1 by admin
        exam1 = Exam(name='Admin Exam 1', duration_minutes=30, created_by=admin_id, is_active=True)
        db.session.add(exam1)
        db.session.commit()
        
        # Try to access own exam - should work
        r = self.client.get(f'/api/admin/exams/{exam1.id}', headers=self._h(self.admin_token))
        if r.status_code != 200:
            print(f"  ✗ FAIL: Cannot access own exam: {r.status_code}")
            return False
        
        # Create another admin
        admin2 = User(username='admin2', email='admin2@test.com', role='admin', full_name='Admin2')
        admin2.set_password('admin2pass')
        db.session.add(admin2)
        db.session.commit()
        
        # Login as admin2
        r = self.client.post('/api/auth/login', json={'username': 'admin2', 'password': 'admin2pass'})
        admin2_token = r.get_json()['access_token']
        
        # Try to access admin1's exam as admin2 - should fail
        r = self.client.get(f'/api/admin/exams/{exam1.id}', headers=self._h(admin2_token))
        if r.status_code != 403:
            print(f"  ✗ FAIL: Got {r.status_code}, expected 403")
            return False
        
        print("  ✓ PASS: Admin authorization working")
        return True
    
    def test_validation_question_belongs_to_exam(self):
        """TEST 9: Answer validation - question belongs to exam"""
        print("\n[TEST 9] Answer Validation - Question Belongs to Exam")
        
        admin_id = db.session.query(User).filter_by(username='admin').first().id
        student_id = db.session.query(User).filter_by(username='student1').first().id
        
        # Create exam1
        exam1 = Exam(name='Exam 1', duration_minutes=30, created_by=admin_id, is_active=True)
        db.session.add(exam1)
        db.session.flush()
        
        # Create exam2
        exam2 = Exam(name='Exam 2', duration_minutes=30, created_by=admin_id, is_active=True)
        db.session.add(exam2)
        db.session.flush()
        
        # Create question for exam2
        q_exam2 = Question(exam_id=exam2.id, question_text='Q2?', order_number=1)
        db.session.add(q_exam2)
        db.session.commit()
        
        # Start exam1
        r = self.client.post(f'/api/student/exams/{exam1.id}/start', headers=self._h(self.student1_token))
        sub_id = r.get_json()['submission_id']
        
        # Try to answer with question from exam2
        r = self.client.post(f'/api/student/submissions/{sub_id}/answer',
                            headers=self._h(self.student1_token),
                            json={'question_id': q_exam2.id, 'selected_option_id': None})
        
        if r.status_code != 404:
            print(f"  ✗ FAIL: Got {r.status_code}, expected 404")
            return False
        
        print("  ✓ PASS: Question validation working")
        return True
    
    def test_backend_score_calculation(self):
        """TEST 10: Backend calculates score (not frontend)"""
        print("\n[TEST 10] Backend Score Calculation")
        
        admin_id = db.session.query(User).filter_by(username='admin').first().id
        student_id = db.session.query(User).filter_by(username='student2').first().id
        
        # Create exam
        exam = Exam(name='Score Test Exam', duration_minutes=30, created_by=admin_id, is_active=True)
        db.session.add(exam)
        db.session.flush()
        
        # Create question
        q = Question(exam_id=exam.id, question_text='Q?', order_number=1)
        db.session.add(q)
        db.session.flush()
        
        # Create options
        opt_correct = Option(question_id=q.id, option_text='Correct', option_order=1, is_correct=True)
        opt_wrong = Option(question_id=q.id, option_text='Wrong', option_order=2, is_correct=False)
        db.session.add_all([opt_correct, opt_wrong])
        db.session.commit()
        
        # Start exam
        r = self.client.post(f'/api/student/exams/{exam.id}/start', headers=self._h(self.student2_token))
        sub_id = r.get_json()['submission_id']
        
        # Answer correctly
        self.client.post(f'/api/student/submissions/{sub_id}/answer',
                        headers=self._h(self.student2_token),
                        json={'question_id': q.id, 'selected_option_id': opt_correct.id})
        
        # Submit
        r = self.client.post(f'/api/student/submissions/{sub_id}/submit',
                            headers=self._h(self.student2_token), json={})
        
        result = r.get_json()['result']
        
        # Verify score was calculated on backend
        if result['score'] != 1 or result['percentage'] != 100.0:
            print(f"  ✗ FAIL: Score calculation wrong: {result}")
            return False
        
        print("  ✓ PASS: Backend score calculated correctly")
        return True
    
    def run_all(self):
        """Run all tests"""
        print("\n" + "="*70)
        print("SECURITY AUDIT TEST SUITE")
        print("="*70)
        
        tests = [
            self.test_auth_password_not_leaked,
            self.test_student_cannot_access_admin_apis,
            self.test_unauthenticated_blocked,
            self.test_correct_answers_not_leaked,
            self.test_submitted_exam_cannot_change,
            self.test_student_cannot_access_other_student_result,
            self.test_expired_exam_rejected,
            self.test_admin_authorization,
            self.test_validation_question_belongs_to_exam,
            self.test_backend_score_calculation,
        ]
        
        passed = sum(1 for t in tests if t())
        failed = len(tests) - passed
        
        print("\n" + "="*70)
        print(f"RESULTS: {passed}/{len(tests)} PASSED, {failed} FAILED")
        print("="*70)
        
        return failed == 0

if __name__ == '__main__':
    tester = SecurityAuditTests()
    try:
        success = tester.run_all()
        tester.cleanup()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
