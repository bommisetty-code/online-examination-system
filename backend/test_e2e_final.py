"""
End-to-End Integration Tests (ASCII-safe version)
Comprehensive workflow testing for Admin and Student flows
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import User, Exam, Question, Option
from datetime import datetime, timedelta

class E2EIntegrationTests:
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
        admin = User(username='admin', email='admin@test.com', role='admin', full_name='Admin')
        admin.set_password('adminpass')
        
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
    # ADMIN WORKFLOW TESTS
    # ========================================================================
    
    def test_admin_workflow(self):
        """ADMIN E2E: Login -> Create Exam -> Add Questions -> Activate -> View Results"""
        print("\n[ADMIN E2E TEST]")
        
        print("  1. Create exam...")
        r = self.client.post('/api/admin/exams', headers=self._h(self.admin_token),
                            json={'name': 'E2E Test Exam', 'duration_minutes': 30,
                                  'passing_percentage': 60, 'description': 'E2E test'})
        if r.status_code != 201:
            print(f"    [FAIL] Create exam {r.status_code}")
            return False
        exam_id = r.get_json()['exam']['id']
        print(f"    [OK] Created exam ID {exam_id}")
        
        print("  2. Add questions with options...")
        for i in range(2):
            r = self.client.post(f'/api/admin/exams/{exam_id}/questions',
                                headers=self._h(self.admin_token),
                                json={'question_text': f'Question {i+1}?',
                                      'marks': 1,
                                      'options': [
                                          {'option_text': 'Correct Answer', 'is_correct': True},
                                          {'option_text': 'Wrong Answer', 'is_correct': False}
                                      ]})
            if r.status_code != 201:
                print(f"    [FAIL] Add question {r.status_code}")
                print(f"           Response: {r.get_json()}")
                return False
        print(f"    [OK] Added 2 questions with options")
        
        print("  4. Activate exam...")
        r = self.client.patch(f'/api/admin/exams/{exam_id}/activate',
                             headers=self._h(self.admin_token),
                             json={'is_active': True})
        if r.status_code != 200:
            print(f"    [FAIL] Activate exam {r.status_code}")
            return False
        print(f"    [OK] Exam activated")
        
        print("  5. Students take exam...")
        # Student 1 starts exam
        r = self.client.post(f'/api/student/exams/{exam_id}/start',
                            headers=self._h(self.student1_token))
        if r.status_code != 201:
            print(f"    [FAIL] Start exam {r.status_code}")
            return False
        sub1_id = r.get_json()['submission_id']
        
        # Student 1 answers questions
        r = self.client.get(f'/api/student/submissions/{sub1_id}/questions',
                           headers=self._h(self.student1_token))
        questions = r.get_json()['questions']
        
        for q in questions:
            opts = q.get('options', [])
            if opts:
                self.client.post(f'/api/student/submissions/{sub1_id}/answer',
                                headers=self._h(self.student1_token),
                                json={'question_id': q['id'], 'selected_option_id': opts[0]['id']})
        
        # Submit
        r = self.client.post(f'/api/student/submissions/{sub1_id}/submit',
                            headers=self._h(self.student1_token), json={})
        if r.status_code != 200:
            print(f"    [FAIL] Submit exam {r.status_code}")
            return False
        print(f"    [OK] Student 1 completed exam")
        
        print("  6. View results...")
        r = self.client.get('/api/admin/exams', headers=self._h(self.admin_token))
        if r.status_code != 200:
            print(f"    [FAIL] Get exams {r.status_code}")
            return False
        exams = r.get_json()['exams']
        
        r = self.client.get(f'/api/admin/exams/{exam_id}/results',
                           headers=self._h(self.admin_token))
        if r.status_code != 200:
            print(f"    [FAIL] Get results {r.status_code}")
            return False
        results = r.get_json()['results']
        
        if len(results) == 0:
            print(f"    [FAIL] No results found")
            return False
        print(f"    [OK] Viewed results (found {len(results)} submission(s))")
        
        print("  [OK] ADMIN WORKFLOW COMPLETED")
        return True
    
    # ========================================================================
    # STUDENT WORKFLOW TESTS
    # ========================================================================
    
    def test_student_workflow(self):
        """STUDENT E2E: Login -> View Exams -> Start -> Answer -> Submit -> View Result"""
        print("\n[STUDENT E2E TEST]")
        
        print("  1. Create and activate exam (by admin)...")
        r = self.client.post('/api/admin/exams', headers=self._h(self.admin_token),
                            json={'name': 'Student E2E Test', 'duration_minutes': 30,
                                  'passing_percentage': 50, 'is_active': True})
        exam_id = r.get_json()['exam']['id']
        
        # Add question with options
        r = self.client.post(f'/api/admin/exams/{exam_id}/questions',
                            headers=self._h(self.admin_token),
                            json={'question_text': 'Sample Q?', 
                                  'marks': 1,
                                  'options': [
                                      {'option_text': 'A', 'is_correct': True},
                                      {'option_text': 'B', 'is_correct': False}
                                  ]})
        if r.status_code != 201:
            print(f"    [FAIL] Create question {r.status_code}")
            print(f"           Response: {r.get_json()}")
            raise Exception("Failed to create question")
        print("  [OK] Exam created with questions")
        
        print("  2. View available exams...")
        r = self.client.get('/api/student/exams', headers=self._h(self.student2_token))
        if r.status_code != 200:
            print(f"    [FAIL] Get exams {r.status_code}")
            return False
        exams = r.get_json()['exams']
        
        # Find our exam
        target_exam = next((e for e in exams if e['id'] == exam_id), None)
        if not target_exam:
            print(f"    [FAIL] Exam not found in available list")
            return False
        if target_exam['already_taken']:
            print(f"    [FAIL] Should not be marked as taken")
            return False
        print(f"    [OK] Exam visible in student list")
        
        print("  3. Start exam...")
        r = self.client.post(f'/api/student/exams/{exam_id}/start',
                            headers=self._h(self.student2_token))
        if r.status_code != 201:
            print(f"    [FAIL] Start exam {r.status_code}")
            return False
        sub_id = r.get_json()['submission_id']
        print(f"    [OK] Exam started (submission ID: {sub_id})")
        
        print("  4. Get questions and answer...")
        r = self.client.get(f'/api/student/submissions/{sub_id}/questions',
                           headers=self._h(self.student2_token))
        if r.status_code != 200:
            print(f"    [FAIL] Get questions {r.status_code}")
            return False
        questions = r.get_json()['questions']
        
        for q in questions:
            opts = q.get('options', [])
            if len(opts) > 0:
                # Answer with first option
                r = self.client.post(f'/api/student/submissions/{sub_id}/answer',
                                    headers=self._h(self.student2_token),
                                    json={'question_id': q['id'], 'selected_option_id': opts[0]['id']})
                if r.status_code != 200:
                    print(f"    [FAIL] Answer question {r.status_code}")
                    return False
        print(f"    [OK] Answered all questions")
        
        print("  5. Submit exam...")
        r = self.client.post(f'/api/student/submissions/{sub_id}/submit',
                            headers=self._h(self.student2_token), json={})
        if r.status_code != 200:
            print(f"    [FAIL] Submit exam {r.status_code}")
            return False
        result = r.get_json()['result']
        print(f"    [OK] Exam submitted (Score: {result['percentage']}%)")
        
        print("  6. View result...")
        r = self.client.get(f'/api/student/results/{sub_id}',
                           headers=self._h(self.student2_token))
        if r.status_code != 200:
            print(f"    [FAIL] Get result {r.status_code}")
            return False
        print(f"    [OK] Result retrieved")
        
        print("  7. Verify cannot retake exam...")
        r = self.client.post(f'/api/student/exams/{exam_id}/start',
                            headers=self._h(self.student2_token))
        if r.status_code != 409:  # Conflict
            print(f"    [FAIL] Should not allow retake {r.status_code}")
            return False
        print(f"    [OK] Cannot retake exam (correctly rejected)")
        
        print("  [OK] STUDENT WORKFLOW COMPLETED")
        return True
    
    def test_student_refresh_during_exam(self):
        """STUDENT TEST: Refresh during exam should maintain session"""
        print("\n[STUDENT REFRESH TEST]")
        
        # Setup exam
        r = self.client.post('/api/admin/exams', headers=self._h(self.admin_token),
                            json={'name': 'Refresh Test', 'duration_minutes': 30, 'is_active': True})
        exam_id = r.get_json()['exam']['id']
        
        r = self.client.post(f'/api/admin/exams/{exam_id}/questions',
                            headers=self._h(self.admin_token),
                            json={'question_text': 'Q?',
                                  'marks': 1,
                                  'options': [
                                      {'option_text': 'O', 'is_correct': True}
                                  ]})
        
        print("  1. Start exam...")
        r = self.client.post(f'/api/student/exams/{exam_id}/start',
                            headers=self._h(self.student1_token))
        sub_id = r.get_json()['submission_id']
        
        print("  2. Get questions (first load)...")
        r = self.client.get(f'/api/student/submissions/{sub_id}/questions',
                           headers=self._h(self.student1_token))
        questions_1 = r.get_json()['questions']
        
        print("  3. Refresh (get questions again - simulates refresh)...")
        r = self.client.get(f'/api/student/submissions/{sub_id}/questions',
                           headers=self._h(self.student1_token))
        questions_2 = r.get_json()['questions']
        
        if len(questions_1) != len(questions_2):
            print(f"    [FAIL] Question count changed")
            return False
        
        print(f"    [OK] Refresh maintained session ({len(questions_2)} questions)")
        print("  [OK] REFRESH TEST COMPLETED")
        return True
    
    def run_all(self):
        """Run all E2E tests"""
        print("\n" + "="*70)
        print("END-TO-END INTEGRATION TEST SUITE")
        print("="*70)
        
        tests = [
            ("Admin Workflow", self.test_admin_workflow),
            ("Student Workflow", self.test_student_workflow),
            ("Student Refresh", self.test_student_refresh_during_exam),
        ]
        
        results = []
        for name, test_func in tests:
            try:
                result = test_func()
                results.append((name, result))
            except Exception as e:
                print(f"\n  [ERROR] EXCEPTION: {e}")
                import traceback
                traceback.print_exc()
                results.append((name, False))
        
        passed = sum(1 for _, r in results if r)
        failed = len(results) - passed
        
        print("\n" + "="*70)
        print(f"RESULTS: {passed}/{len(results)} PASSED, {failed} FAILED")
        print("="*70)
        
        return failed == 0

if __name__ == '__main__':
    tester = E2EIntegrationTests()
    try:
        success = tester.run_all()
        tester.cleanup()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FATAL] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
