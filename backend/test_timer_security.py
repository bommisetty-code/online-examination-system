"""
Timer Security Tests
Verifies timer security and exam duration handling
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import User, Exam, Question, Option, ExamSubmission
from datetime import datetime, timedelta
import time

class TimerSecurityTests:
    def __init__(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        self.admin_token = None
        self.student_token = None
        self._setup()
    
    def _setup(self):
        """Setup test data"""
        admin = User(username='admin', email='admin@test.com', role='admin', full_name='Admin')
        admin.set_password('adminpass')
        
        student = User(username='student', email='student@test.com', role='student', full_name='Student')
        student.set_password('studentpass')
        
        db.session.add_all([admin, student])
        db.session.commit()
        
        # Login
        r = self.client.post('/api/auth/login', json={'username': 'admin', 'password': 'adminpass'})
        self.admin_token = r.get_json()['access_token']
        
        r = self.client.post('/api/auth/login', json={'username': 'student', 'password': 'studentpass'})
        self.student_token = r.get_json()['access_token']
    
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
    # TIMER SECURITY TESTS
    # ========================================================================
    
    def test_1_duration_captured_at_start(self):
        """TEST 1: Duration is captured when exam starts"""
        print("\n[TEST 1] Duration Captured at Start Time")
        
        admin_id = db.session.query(User).filter_by(username='admin').first().id
        
        # Create exam with 30 minute duration
        exam = Exam(name='Timer Test 1', duration_minutes=30, created_by=admin_id, is_active=True)
        db.session.add(exam)
        db.session.commit()
        
        # Start exam
        r = self.client.post(f'/api/student/exams/{exam.id}/start', headers=self._h(self.student_token))
        sub_id = r.get_json()['submission_id']
        
        # Get submission
        submission = db.session.query(ExamSubmission).get(sub_id)
        
        # Verify duration was captured
        if submission.duration_minutes != 30:
            print(f"  ✗ FAIL: Duration not captured. Got {submission.duration_minutes}")
            return False
        
        print("  ✓ PASS: Duration captured at start")
        return True
    
    def test_2_admin_duration_change_doesnt_affect_ongoing(self):
        """TEST 2: Changing admin duration doesn't affect ongoing attempts"""
        print("\n[TEST 2] Admin Duration Change Doesn't Affect Ongoing Attempts")
        
        admin_id = db.session.query(User).filter_by(username='admin').first().id
        
        # Create exam with 30 minutes
        exam = Exam(name='Timer Test 2', duration_minutes=30, created_by=admin_id, is_active=True)
        db.session.add(exam)
        db.session.commit()
        
        # Start exam
        r = self.client.post(f'/api/student/exams/{exam.id}/start', headers=self._h(self.student_token))
        sub_id = r.get_json()['submission_id']
        
        # Admin changes duration to 60 minutes
        exam.duration_minutes = 60
        db.session.commit()
        
        # Get submission - should still have 30 minutes
        submission = db.session.query(ExamSubmission).get(sub_id)
        
        if submission.duration_minutes != 30:
            print(f"  ✗ FAIL: Duration changed. Got {submission.duration_minutes}")
            return False
        
        print("  ✓ PASS: Ongoing attempt keeps original duration")
        return True
    
    def test_3_backend_calculates_expiry(self):
        """TEST 3: Backend calculates expiry time correctly"""
        print("\n[TEST 3] Backend Calculates Expiry Correctly")
        
        admin_id = db.session.query(User).filter_by(username='admin').first().id
        
        # Create exam with 1 minute duration
        exam = Exam(name='Timer Test 3', duration_minutes=1, created_by=admin_id, is_active=True)
        db.session.add(exam)
        db.session.commit()
        
        # Start exam
        start_time = datetime.utcnow()
        r = self.client.post(f'/api/student/exams/{exam.id}/start', headers=self._h(self.student_token))
        sub_id = r.get_json()['submission_id']
        submission = db.session.query(ExamSubmission).get(sub_id)
        
        # Check that started_at is recent
        elapsed = (datetime.utcnow() - submission.started_at).total_seconds()
        
        if elapsed > 5:
            print(f"  ✗ FAIL: Start time too far from now: {elapsed}s")
            return False
        
        # Calculate when exam expires (should be 60 seconds from start)
        expected_expiry = submission.started_at + timedelta(seconds=submission.duration_minutes * 60)
        
        # Verify
        now = datetime.utcnow()
        diff = (expected_expiry - now).total_seconds()
        
        if abs(diff - 60) > 5:  # Allow 5 second variance
            print(f"  ✗ FAIL: Expiry time incorrect. Expected ~60s, got {diff}s")
            return False
        
        print("  ✓ PASS: Backend expiry calculation correct")
        return True
    
    def test_4_clock_skew_protection(self):
        """TEST 4: Backend validates time, not trusting client clock"""
        print("\n[TEST 4] Clock Skew Protection (Backend Validates)")
        
        admin_id = db.session.query(User).filter_by(username='admin').first().id
        student_id = db.session.query(User).filter_by(username='student').first().id
        
        # Create exam with 2 minute duration
        exam = Exam(name='Timer Test 4', duration_minutes=2, created_by=admin_id, is_active=True)
        db.session.add(exam)
        db.session.flush()
        
        q = Question(exam_id=exam.id, question_text='Q?', order_number=1)
        db.session.add(q)
        db.session.flush()
        
        opt = Option(question_id=q.id, option_text='O', option_order=1, is_correct=True)
        db.session.add(opt)
        db.session.commit()
        
        # Start exam
        r = self.client.post(f'/api/student/exams/{exam.id}/start', headers=self._h(self.student_token))
        sub_id = r.get_json()['submission_id']
        
        # Manually set started_at to 3 minutes ago (backend only - client can't change this)
        submission = db.session.query(ExamSubmission).get(sub_id)
        submission.started_at = datetime.utcnow() - timedelta(minutes=3)
        db.session.commit()
        
        # Try to submit answer - should be rejected as expired
        r = self.client.post(f'/api/student/submissions/{sub_id}/answer',
                            headers=self._h(self.student_token),
                            json={'question_id': q.id, 'selected_option_id': opt.id})
        
        if r.status_code != 410:  # 410 Gone (expired)
            print(f"  ✗ FAIL: Expected 410, got {r.status_code}")
            return False
        
        print("  ✓ PASS: Backend time validation working")
        return True
    
    def test_5_auto_submit_on_expiry(self):
        """TEST 5: Exam auto-submits when requesting after expiry"""
        print("\n[TEST 5] Auto-Submit on Expiry")
        
        admin_id = db.session.query(User).filter_by(username='admin').first().id
        student_id = db.session.query(User).filter_by(username='student').first().id
        
        # Create exam with 1 minute duration
        exam = Exam(name='Timer Test 5', duration_minutes=1, created_by=admin_id, is_active=True)
        db.session.add(exam)
        db.session.flush()
        
        q = Question(exam_id=exam.id, question_text='Q?', order_number=1)
        db.session.add(q)
        db.session.commit()
        
        # Start exam
        r = self.client.post(f'/api/student/exams/{exam.id}/start', headers=self._h(self.student_token))
        sub_id = r.get_json()['submission_id']
        
        # Set started_at to 2 minutes ago to simulate expiry
        submission = db.session.query(ExamSubmission).get(sub_id)
        submission.started_at = datetime.utcnow() - timedelta(minutes=2)
        db.session.commit()
        
        # Try to get questions - should trigger auto-submit and return 410
        r = self.client.get(f'/api/student/submissions/{sub_id}/questions',
                           headers=self._h(self.student_token))
        
        if r.status_code != 410:
            print(f"  ✗ FAIL: Expected 410, got {r.status_code}")
            return False
        
        # Verify submission was auto-submitted
        submission = db.session.query(ExamSubmission).get(sub_id)
        if submission.status != 'auto_submitted':
            print(f"  ✗ FAIL: Not auto-submitted. Status: {submission.status}")
            return False
        
        print("  ✓ PASS: Auto-submit on expiry working")
        return True
    
    def test_6_remaining_time_calculated_correctly(self):
        """TEST 6: Remaining time calculated correctly from backend"""
        print("\n[TEST 6] Remaining Time Calculation")
        
        admin_id = db.session.query(User).filter_by(username='admin').first().id
        
        # Create exam with 60 second duration
        exam = Exam(name='Timer Test 6', duration_minutes=1, created_by=admin_id, is_active=True)
        db.session.add(exam)
        db.session.commit()
        
        # Start exam
        r = self.client.post(f'/api/student/exams/{exam.id}/start', headers=self._h(self.student_token))
        resp_data = r.get_json()
        sub_id = resp_data['submission_id']
        
        # Immediately get status - remaining should be ~60 seconds
        r = self.client.get(f'/api/student/submissions/{sub_id}/status',
                           headers=self._h(self.student_token))
        
        status = r.get_json()
        remaining = status['remaining_seconds']
        
        # Should be close to 60 (allowing up to 5 seconds variance)
        if not (55 <= remaining <= 65):
            print(f"  ✗ FAIL: Remaining time incorrect. Expected ~60, got {remaining}")
            return False
        
        print(f"  ✓ PASS: Remaining time correct ({remaining}s)")
        return True
    
    def run_all(self):
        """Run all timer tests"""
        print("\n" + "="*70)
        print("TIMER SECURITY TEST SUITE")
        print("="*70)
        
        tests = [
            self.test_1_duration_captured_at_start,
            self.test_2_admin_duration_change_doesnt_affect_ongoing,
            self.test_3_backend_calculates_expiry,
            self.test_4_clock_skew_protection,
            self.test_5_auto_submit_on_expiry,
            self.test_6_remaining_time_calculated_correctly,
        ]
        
        passed = sum(1 for t in tests if t())
        failed = len(tests) - passed
        
        print("\n" + "="*70)
        print(f"RESULTS: {passed}/{len(tests)} PASSED, {failed} FAILED")
        print("="*70)
        
        return failed == 0

if __name__ == '__main__':
    tester = TimerSecurityTests()
    try:
        success = tester.run_all()
        tester.cleanup()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
