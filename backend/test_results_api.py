"""Test the results API endpoints"""
import sys
sys.path.insert(0, '.')

from app import create_app, db
from app.models import User, Exam, Question, Option, ExamSubmission, StudentAnswer, Result
from datetime import datetime, timedelta
import json

# Create test app
app = create_app('testing')
client = app.test_client()

# Create test data
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

print("Testing Admin Results API...")
print("=" * 60)

# Login
login_response = client.post('/api/auth/login', json={
    'username': 'testadmin',
    'password': 'Password1'
})

if login_response.status_code != 200:
    print(f"✗ Login failed: {login_response.status_code}")
    print(json.dumps(login_response.get_json(), indent=2))
    sys.exit(1)

token = login_response.get_json()['access_token']
headers = {'Authorization': f'Bearer {token}'}
print(f"✓ Admin login successful (token length: {len(token)})")

# Test: Get all exams
print("\n1. Testing GET /api/admin/exams")
exams_response = client.get('/api/admin/exams', headers=headers)
print(f"   Status: {exams_response.status_code}")
if exams_response.status_code == 200:
    exams = exams_response.get_json()['exams']
    print(f"   ✓ Found {len(exams)} exam(s)")
    if exams:
        exam_id = exams[0]['id']
        print(f"   ✓ First exam ID: {exam_id}")
    else:
        print("   ✗ No exams found!")
        sys.exit(1)
else:
    print(f"   ✗ Failed to get exams: {exams_response.get_json()}")
    sys.exit(1)

# Test: Get exam results
print(f"\n2. Testing GET /api/admin/exams/{exam_id}/results")
results_response = client.get(f'/api/admin/exams/{exam_id}/results', headers=headers)
print(f"   Status: {results_response.status_code}")
if results_response.status_code == 200:
    results = results_response.get_json()['results']
    print(f"   ✓ Found {len(results)} result(s)")
    if results:
        result = results[0]
        print(f"   ✓ Student: {result['student']['full_name']} ({result['student']['email']})")
        print(f"   ✓ Score: {result['result']['score']}/{result['result']['total_marks']}")
        print(f"   ✓ Percentage: {result['result']['percentage']}%")
        print(f"   ✓ Status: {'Passed' if result['result']['is_passed'] else 'Failed'}")
        student_id = result['student']['id']
    else:
        print("   ✗ No results found for this exam!")
        sys.exit(1)
else:
    print(f"   ✗ Failed to get results: {results_response.get_json()}")
    sys.exit(1)

# Test: Get detailed student result
print(f"\n3. Testing GET /api/admin/exams/{exam_id}/results/{student_id}")
detail_response = client.get(f'/api/admin/exams/{exam_id}/results/{student_id}', headers=headers)
print(f"   Status: {detail_response.status_code}")
if detail_response.status_code == 200:
    data = detail_response.get_json()
    print(f"   ✓ Result ID: {data['result']['id']}")
    print(f"   ✓ Correct answers: {data['result']['correct_answers']}")
    print(f"   ✓ Incorrect answers: {data['result']['incorrect_answers']}")
    print(f"   ✓ Unanswered: {data['result']['unanswered']}")
    print(f"   ✓ Found {len(data['answers'])} answer(s)")
    for i, answer in enumerate(data['answers'], 1):
        print(f"      Q{i}: {answer['question_text'][:40]}... → {answer['is_correct']}")
else:
    print(f"   ✗ Failed to get detailed result: {detail_response.get_json()}")
    sys.exit(1)

# Test: Try to access as student (should fail)
print(f"\n4. Testing Access Control (Student should NOT access)")
student_response = client.post('/api/auth/login', json={
    'username': 'teststudent',
    'password': 'Password1'
})
student_token = student_response.get_json()['access_token']
student_headers = {'Authorization': f'Bearer {student_token}'}

access_test = client.get(f'/api/admin/exams/{exam_id}/results', headers=student_headers)
print(f"   Status: {access_test.status_code}")
if access_test.status_code == 403:
    print(f"   ✓ Access correctly denied to student (403)")
else:
    print(f"   ✗ ERROR: Student should not access admin endpoints! Got {access_test.status_code}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ All API tests passed!")
