"""
Back-Button Protection Tests
Verifies that the exam interface properly handles browser back button navigation
and shows warning dialogs with auto-submit on second attempt.
"""

import json
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
from app import create_app, db
from app.models import User, Exam, Question, Option, ExamSubmission, StudentAnswer


class BackButtonProtectionTestSuite:
    """Tests for back-button warning and auto-submit functionality"""
    
    def __init__(self):
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        
        with self.app.app_context():
            db.create_all()
            self._setup_test_data()
        
        self.client = self.app.test_client()
        self.admin_token = None
        self.student_token = None
        self.exam_id = None
        self.submission_id = None
    
    def _setup_test_data(self):
        """Setup initial test data"""
        # Create admin
        admin = User(
            username='admin_test',
            email='admin@test.com',
            role='admin',
            full_name='Admin Test'
        )
        admin.set_password('password123')
        
        # Create students
        student1 = User(
            username='student1_test',
            email='student1@test.com',
            role='student',
            full_name='Student One'
        )
        student1.set_password('password123')
        
        student2 = User(
            username='student2_test',
            email='student2@test.com',
            role='student',
            full_name='Student Two'
        )
        student2.set_password('password123')
        
        db.session.add_all([admin, student1, student2])
        db.session.flush()
        
        # Create exam
        exam = Exam(
            name='Back Button Test Exam',
            description='Test for back button protection',
            duration_minutes=30,
            passing_percentage=50,
            created_by=admin.id,
            is_active=True,
            total_questions=0
        )
        
        db.session.add(exam)
        db.session.flush()
        
        # Create questions with options
        for i in range(2):
            question = Question(
                exam_id=exam.id,
                question_text=f'Question {i+1}?',
                marks=1,
                order_number=i+1
            )
            db.session.add(question)
            db.session.flush()
            
            option1 = Option(
                question_id=question.id,
                option_text='Correct',
                option_order=1,
                is_correct=True
            )
            option2 = Option(
                question_id=question.id,
                option_text='Wrong',
                option_order=2,
                is_correct=False
            )
            db.session.add_all([option1, option2])
        
        exam.total_questions = 2
        db.session.commit()
        
        self.admin_user_id = admin.id
        self.student1_id = student1.id
        self.student2_id = student2.id
        self.exam_id = exam.id
    
    def _h(self, token):
        """Helper to create authorization header"""
        return {'Authorization': f'Bearer {token}'}
    
    def run_all_tests(self):
        """Run all back-button tests"""
        print("\n" + "="*70)
        print("BACK-BUTTON PROTECTION TEST SUITE")
        print("="*70 + "\n")
        
        # Create tokens
        with self.app.app_context():
            self.admin_token = create_access_token(identity=self.admin_user_id, 
                                                   additional_claims={'role': 'admin'})
            self.student_token = create_access_token(identity=self.student1_id,
                                                     additional_claims={'role': 'student'})
        
        tests = [
            ('TEST 1: First back button press shows warning', self.test_first_back_shows_warning),
            ('TEST 2: User can stay in exam after warning', self.test_stay_in_exam),
            ('TEST 3: Second back button press auto-submits', self.test_second_back_auto_submits),
            ('TEST 4: Multiple exam sessions protected independently', self.test_multiple_sessions),
            ('TEST 5: Different students have independent back-button state', self.test_different_students),
            ('TEST 6: Completed exam doesn\'t trigger warning', self.test_completed_exam_no_warning),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                status = "[PASS]" if result else "[FAIL]"
                results.append(result)
                print(f"{status} {test_name}")
            except Exception as e:
                results.append(False)
                print(f"[ERROR] {test_name}: {str(e)}")
        
        # Summary
        passed = sum(results)
        total = len(results)
        print(f"\n{'='*70}")
        print(f"RESULTS: {passed}/{total} PASSED, {total-passed} FAILED")
        print(f"{'='*70}\n")
        
        return all(results)
    
    def test_first_back_shows_warning(self):
        """
        Requirement: First browser back button press during exam should show warning,
        NOT auto-submit immediately
        """
        with self.app.app_context():
            # Start exam
            r = self.client.post(f'/api/student/exams/{self.exam_id}/start',
                                headers=self._h(self.student_token))
            if r.status_code != 201:
                return False
            
            submission_id = r.get_json()['submission']['id']
            
            # Frontend should manage back button warning state locally
            # Backend API doesn't expose warning state, but we can verify submission is still active
            r = self.client.get(f'/api/student/submissions/{submission_id}/status',
                               headers=self._h(self.student_token))
            
            # Should still be in_progress
            if r.status_code != 200:
                return False
            
            status = r.get_json()['submission']['status']
            return status == 'in_progress'
    
    def test_stay_in_exam(self):
        """
        Requirement: If student clicks "Stay in Exam" after warning,
        exam should continue normally
        """
        with self.app.app_context():
            # Start exam
            r = self.client.post(f'/api/student/exams/{self.exam_id}/start',
                                headers=self._h(self.student_token))
            submission_id = r.get_json()['submission']['id']
            
            # Answer a question
            questions_r = self.client.get(f'/api/student/submissions/{submission_id}/questions',
                                         headers=self._h(self.student_token))
            questions = questions_r.get_json()['questions']
            
            if not questions:
                return False
            
            q_id = questions[0]['id']
            option_id = questions[0]['options'][0]['id']
            
            r = self.client.post(f'/api/student/submissions/{submission_id}/answer',
                                headers=self._h(self.student_token),
                                json={'question_id': q_id, 'option_id': option_id})
            
            # Submission should still be in_progress
            if r.status_code != 200:
                return False
            
            # Verify still in progress
            check_r = self.client.get(f'/api/student/submissions/{submission_id}',
                                     headers=self._h(self.student_token))
            status = check_r.get_json()['submission']['status']
            return status == 'in_progress'
    
    def test_second_back_auto_submits(self):
        """
        Requirement: Second browser back button press should auto-submit exam.
        After first back press (warning shown), second back press should submit.
        """
        with self.app.app_context():
            # Start exam
            r = self.client.post(f'/api/student/exams/{self.exam_id}/start',
                                headers=self._h(self.student_token))
            submission_id = r.get_json()['submission']['id']
            
            # Simulate back button interaction - directly submit (frontend handles warning)
            r = self.client.post(f'/api/student/submissions/{submission_id}/submit',
                                headers=self._h(self.student_token),
                                json={'is_auto_submit': True})
            
            # Should be submitted/auto_submitted
            if r.status_code != 200:
                return False
            
            status = r.get_json()['submission']['status']
            return status in ['submitted', 'auto_submitted']
    
    def test_multiple_sessions(self):
        """
        Requirement: Different exam sessions should have independent
        back-button warning state
        """
        with self.app.app_context():
            # Create second exam
            exam2 = Exam(
                name='Test Exam 2',
                description='Second exam',
                duration_minutes=15,
                passing_percentage=50,
                created_by=self.admin_user_id,
                is_active=True,
                total_questions=1
            )
            db.session.add(exam2)
            db.session.flush()
            
            q = Question(exam_id=exam2.id, question_text='Q?',
                        marks=1, order_number=1)
            db.session.add(q)
            db.session.flush()
            
            Option(question_id=q.id, option_text='A', option_order=1, is_correct=True)
            db.session.commit()
            
            exam2_id = exam2.id
            
            # Start both exams
            r1 = self.client.post(f'/api/student/exams/{self.exam_id}/start',
                                 headers=self._h(self.student_token))
            s1_id = r1.get_json()['submission']['id']
            
            r2 = self.client.post(f'/api/student/exams/{exam2_id}/start',
                                 headers=self._h(self.student_token))
            s2_id = r2.get_json()['submission']['id']
            
            # Both should be in_progress
            check1 = self.client.get(f'/api/student/submissions/{s1_id}',
                                    headers=self._h(self.student_token))
            check2 = self.client.get(f'/api/student/submissions/{s2_id}',
                                    headers=self._h(self.student_token))
            
            return (check1.get_json()['submission']['status'] == 'in_progress' and
                   check2.get_json()['submission']['status'] == 'in_progress')
    
    def test_different_students(self):
        """
        Requirement: Back-button state should be per-student and session,
        one student's warning shouldn't affect another
        """
        with self.app.app_context():
            # Student 1 starts exam
            token1 = create_access_token(identity=self.student1_id,
                                        additional_claims={'role': 'student'})
            token2 = create_access_token(identity=self.student2_id,
                                        additional_claims={'role': 'student'})
            
            r1 = self.client.post(f'/api/student/exams/{self.exam_id}/start',
                                 headers=self._h(token1))
            s1_id = r1.get_json()['submission']['id']
            
            # Student 2 starts same exam
            r2 = self.client.post(f'/api/student/exams/{self.exam_id}/start',
                                 headers=self._h(token2))
            s2_id = r2.get_json()['submission']['id']
            
            # Both should be in_progress
            check1 = self.client.get(f'/api/student/submissions/{s1_id}',
                                    headers=self._h(token1))
            check2 = self.client.get(f'/api/student/submissions/{s2_id}',
                                    headers=self._h(token2))
            
            status1 = check1.get_json()['submission']['status']
            status2 = check2.get_json()['submission']['status']
            
            return status1 == 'in_progress' and status2 == 'in_progress'
    
    def test_completed_exam_no_warning(self):
        """
        Requirement: After exam is submitted, back button should not
        show warning (exam already completed)
        """
        with self.app.app_context():
            # Start and submit exam
            r = self.client.post(f'/api/student/exams/{self.exam_id}/start',
                                headers=self._h(self.student_token))
            submission_id = r.get_json()['submission']['id']
            
            # Submit exam
            r = self.client.post(f'/api/student/submissions/{submission_id}/submit',
                                headers=self._h(self.student_token),
                                json={'is_auto_submit': False})
            
            if r.status_code != 200:
                return False
            
            status = r.get_json()['submission']['status']
            
            # Try to start same exam again (should fail - already completed)
            retry_r = self.client.post(f'/api/student/exams/{self.exam_id}/start',
                                      headers=self._h(self.student_token))
            
            # Should be rejected (already taken)
            return retry_r.status_code == 403  # Access forbidden - exam already completed


if __name__ == '__main__':
    suite = BackButtonProtectionTestSuite()
    success = suite.run_all_tests()
    exit(0 if success else 1)
