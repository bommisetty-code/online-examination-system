# Online Examination System - Complete Design Proposal

## 1. PROJECT ARCHITECTURE

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT TIER (Frontend)                     │
│                      React.js Application                        │
│                   (Mobile/Tablet/Desktop)                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ HTTP/REST API (JSON)
                     │ CORS enabled
                     │
┌────────────────────▼────────────────────────────────────────────┐
│                    APPLICATION TIER (Backend)                   │
│                  Flask REST API Server                           │
│    (Authentication, Authorization, Business Logic)              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ SQL Queries
                     │
┌────────────────────▼────────────────────────────────────────────┐
│                      DATA TIER (Database)                        │
│                    MySQL Database                               │
│         (Users, Exams, Questions, Submissions, Results)        │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architecture Principles:
- **Separation of Concerns**: Frontend handles UI/UX, Backend handles business logic and security
- **Stateless REST APIs**: Each request is independent; state stored in DB
- **Session Management**: JWT tokens or Flask sessions for authentication
- **Backend Validation**: All exam state, timer, and scoring logic validated server-side
- **Security First**: No sensitive data in frontend; correct answers never sent to client during exam

---

## 2. FOLDER STRUCTURE

### Frontend (React.js)
```
frontend/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── manifest.json
├── src/
│   ├── components/
│   │   ├── Admin/
│   │   │   ├── AdminDashboard.jsx
│   │   │   ├── ExamForm.jsx
│   │   │   ├── ExamList.jsx
│   │   │   ├── QuestionForm.jsx
│   │   │   ├── QuestionList.jsx
│   │   │   ├── OptionForm.jsx
│   │   │   └── ExamManagement.jsx
│   │   ├── Student/
│   │   │   ├── StudentDashboard.jsx
│   │   │   ├── ExamListStudent.jsx
│   │   │   ├── ExamStart.jsx
│   │   │   ├── ExamInterface.jsx
│   │   │   ├── Question.jsx
│   │   │   ├── Timer.jsx
│   │   │   ├── ProgressBar.jsx
│   │   │   ├── ResultScreen.jsx
│   │   │   └── BackButtonWarning.jsx
│   │   ├── Auth/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── LogoutButton.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   └── Common/
│   │       ├── Navbar.jsx
│   │       ├── Footer.jsx
│   │       └── LoadingSpinner.jsx
│   ├── pages/
│   │   ├── AdminPage.jsx
│   │   ├── StudentPage.jsx
│   │   ├── LoginPage.jsx
│   │   ├── NotFoundPage.jsx
│   │   └── ResultsPage.jsx
│   ├── services/
│   │   ├── api.js (Axios instance with interceptors)
│   │   ├── authService.js
│   │   ├── examService.js
│   │   └── studentService.js
│   ├── hooks/
│   │   ├── useAuth.js
│   │   ├── useTimer.js
│   │   ├── useExamState.js
│   │   └── useBackButton.js
│   ├── context/
│   │   ├── AuthContext.js
│   │   └── ExamContext.js
│   ├── utils/
│   │   ├── constants.js
│   │   ├── formatters.js
│   │   ├── validators.js
│   │   └── storage.js
│   ├── styles/
│   │   ├── App.css
│   │   ├── responsive.css
│   │   └── variables.css
│   ├── App.jsx
│   ├── App.css
│   └── index.jsx
├── package.json
├── .env.example
├── .gitignore
└── README.md
```

### Backend (Python Flask)
```
backend/
├── app.py (Flask app entry point)
├── config.py (Configuration settings)
├── requirements.txt
├── .env.example
├── .gitignore
├── run.py (Server runner)
│
├── app/
│   ├── __init__.py (Flask app factory)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── exam.py
│   │   ├── question.py
│   │   ├── option.py
│   │   ├── exam_submission.py
│   │   ├── student_answer.py
│   │   └── result.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py
│   │   ├── admin_routes.py
│   │   ├── student_routes.py
│   │   └── result_routes.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── exam_service.py
│   │   ├── question_service.py
│   │   ├── submission_service.py
│   │   ├── scoring_service.py
│   │   └── email_service.py (optional)
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── decorators.py (role-based access)
│   │   ├── validators.py
│   │   ├── security.py (password hashing)
│   │   ├── constants.py
│   │   └── errors.py (custom exceptions)
│   └── middleware/
│       ├── __init__.py
│       ├── auth_middleware.py
│       └── error_handler.py
│
└── README.md
```

---

## 3. MYSQL DATABASE SCHEMA

### Database: `online_exam_system`

#### Table 1: users
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role ENUM('admin', 'student') NOT NULL DEFAULT 'student',
    is_active BOOLEAN DEFAULT TRUE,
    last_login DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_is_active (is_active)
);
```

#### Table 2: exams
```sql
CREATE TABLE exams (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    duration_minutes INT NOT NULL,
    created_by INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    total_questions INT DEFAULT 0,
    passing_percentage DECIMAL(5, 2) DEFAULT 50.00,
    exam_code VARCHAR(50) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_created_by (created_by),
    INDEX idx_is_active (is_active),
    INDEX idx_exam_code (exam_code)
);
```

#### Table 3: questions
```sql
CREATE TABLE questions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    exam_id INT NOT NULL,
    question_text TEXT NOT NULL,
    question_type ENUM('multiple_choice') DEFAULT 'multiple_choice',
    marks INT DEFAULT 1,
    order_number INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    INDEX idx_exam_id (exam_id),
    INDEX idx_order (order_number)
);
```

#### Table 4: options
```sql
CREATE TABLE options (
    id INT PRIMARY KEY AUTO_INCREMENT,
    question_id INT NOT NULL,
    option_text VARCHAR(500) NOT NULL,
    option_order INT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    INDEX idx_question_id (question_id),
    INDEX idx_option_order (option_order)
);
```

#### Table 5: exam_submissions
```sql
CREATE TABLE exam_submissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    exam_id INT NOT NULL,
    duration_minutes INT NOT NULL,
    status ENUM('in_progress', 'submitted', 'auto_submitted') DEFAULT 'in_progress',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_at DATETIME,
    time_spent_seconds INT,
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    INDEX idx_student_id (student_id),
    INDEX idx_exam_id (exam_id),
    INDEX idx_status (status),
    UNIQUE KEY unique_submission (student_id, exam_id)
);
```

**Important:** The `duration_minutes` field captures the exam duration at the time the student starts the exam. This ensures that if an admin updates the exam duration later, students who have already started will continue with their original duration, while new students will get the new duration.

#### Table 6: student_answers
```sql
CREATE TABLE student_answers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    submission_id INT NOT NULL,
    question_id INT NOT NULL,
    selected_option_id INT,
    is_correct BOOLEAN,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (submission_id) REFERENCES exam_submissions(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (selected_option_id) REFERENCES options(id) ON DELETE SET NULL,
    INDEX idx_submission_id (submission_id),
    INDEX idx_question_id (question_id),
    UNIQUE KEY unique_answer (submission_id, question_id)
);
```

#### Table 7: results
```sql
CREATE TABLE results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    submission_id INT NOT NULL UNIQUE,
    student_id INT NOT NULL,
    exam_id INT NOT NULL,
    total_questions INT NOT NULL,
    correct_answers INT NOT NULL,
    incorrect_answers INT NOT NULL,
    unanswered INT NOT NULL,
    score INT NOT NULL,
    total_marks INT NOT NULL,
    percentage DECIMAL(5, 2) NOT NULL,
    is_passed BOOLEAN NOT NULL,
    submitted_at DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (submission_id) REFERENCES exam_submissions(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    INDEX idx_student_id (student_id),
    INDEX idx_exam_id (exam_id),
    INDEX idx_submitted_at (submitted_at)
);
```

#### Table 8: exam_student_access (Optional - for access control)
```sql
CREATE TABLE exam_student_access (
    id INT PRIMARY KEY AUTO_INCREMENT,
    exam_id INT NOT NULL,
    student_id INT NOT NULL,
    can_access BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_access (exam_id, student_id),
    INDEX idx_exam_id (exam_id),
    INDEX idx_student_id (student_id)
);
```

### Database Relationships
```
users (1) ──→ (M) exams (created_by)
users (1) ──→ (M) exam_submissions (student_id)
exams (1) ──→ (M) questions
exams (1) ──→ (M) exam_submissions
exams (1) ──→ (M) results
questions (1) ──→ (M) options
questions (1) ──→ (M) student_answers
options (1) ──→ (M) student_answers
exam_submissions (1) ──→ (M) student_answers
exam_submissions (1) ──→ (1) results
```

---

## 4. REST API ENDPOINTS

### Authentication Endpoints
```
POST   /api/auth/register
       Request: { email, username, password, full_name, role }
       Response: { user_id, message }

POST   /api/auth/login
       Request: { username, password }
       Response: { token, user_id, role, username }

POST   /api/auth/logout
       Headers: Authorization: Bearer <token>
       Response: { message }

GET    /api/auth/profile
       Headers: Authorization: Bearer <token>
       Response: { user_id, email, username, full_name, role }
```

### Admin Endpoints - Exam Management
```
GET    /api/admin/exams
       Headers: Authorization: Bearer <admin_token>
       Response: List of all exams with metadata

POST   /api/admin/exams
       Headers: Authorization: Bearer <admin_token>
       Request: { name, description, duration_minutes, passing_percentage }
       Response: { exam_id, message }

GET    /api/admin/exams/<exam_id>
       Headers: Authorization: Bearer <admin_token>
       Response: Exam details with questions count

PUT    /api/admin/exams/<exam_id>
       Headers: Authorization: Bearer <admin_token>
       Request: { name, description, duration_minutes, passing_percentage, is_active }
       Response: { message }

DELETE /api/admin/exams/<exam_id>
       Headers: Authorization: Bearer <admin_token>
       Response: { message }

PATCH  /api/admin/exams/<exam_id>/activate
       Headers: Authorization: Bearer <admin_token>
       Request: { is_active }
       Response: { message }
```

### Admin Endpoints - Question Management
```
GET    /api/admin/exams/<exam_id>/questions
       Headers: Authorization: Bearer <admin_token>
       Response: List of all questions with options

POST   /api/admin/exams/<exam_id>/questions
       Headers: Authorization: Bearer <admin_token>
       Request: { question_text, marks, options: [{ text, is_correct }, ...] }
       Response: { question_id, message }

GET    /api/admin/exams/<exam_id>/questions/<question_id>
       Headers: Authorization: Bearer <admin_token>
       Response: Question with all options

PUT    /api/admin/exams/<exam_id>/questions/<question_id>
       Headers: Authorization: Bearer <admin_token>
       Request: { question_text, marks, options: [...] }
       Response: { message }

DELETE /api/admin/exams/<exam_id>/questions/<question_id>
       Headers: Authorization: Bearer <admin_token>
       Response: { message }
```

### Admin Endpoints - Results
```
GET    /api/admin/exams/<exam_id>/results
       Headers: Authorization: Bearer <admin_token>
       Response: List of all student results for exam

GET    /api/admin/exams/<exam_id>/results/<student_id>
       Headers: Authorization: Bearer <admin_token>
       Response: Detailed result with answers for specific student
```

### Student Endpoints - Exam Access
```
GET    /api/student/exams
       Headers: Authorization: Bearer <student_token>
       Response: List of available exams for student

GET    /api/student/exams/<exam_id>
       Headers: Authorization: Bearer <student_token>
       Response: Exam details (name, duration, question_count)
       Note: Does NOT return correct answers

POST   /api/student/exams/<exam_id>/start
       Headers: Authorization: Bearer <student_token>
       Response: { submission_id, exam_started_at, duration_minutes }
       Note: Creates a new exam_submission record
       Note: Captures exam's current duration_minutes at start time
       Note: Rejects if student has already completed this exam
```

### Student Endpoints - Exam Attempt
```
GET    /api/student/submissions/<submission_id>/questions
       Headers: Authorization: Bearer <student_token>
       Response: Questions for exam with options (no is_correct field)

POST   /api/student/submissions/<submission_id>/answer
       Headers: Authorization: Bearer <student_token>
       Request: { question_id, selected_option_id }
       Response: { message, saved_at }
       Note: Saves answer to student_answers table

GET    /api/student/submissions/<submission_id>/status
       Headers: Authorization: Bearer <student_token>
       Response: { submission_id, status, elapsed_seconds, remaining_seconds, is_active }
       Note: Server validates exam state; returns remaining time

POST   /api/student/submissions/<submission_id>/submit
       Headers: Authorization: Bearer <student_token>
       Request: {} (can include auto_submit: true for auto-submit)
       Response: { submission_id, status, message }
       Note: Calculates score and creates result record; prevents re-submission

GET    /api/student/results/<submission_id>
       Headers: Authorization: Bearer <student_token>
       Response: Result with score, percentage, correct/incorrect counts
       Note: Does NOT return student's answers or reveal correct answers

GET    /api/student/results/history
       Headers: Authorization: Bearer <student_token>
       Response: List of all completed exam results for student
```

---

## 5. USER FLOWS

### Admin User Flow

**1. Admin Login**
- Navigate to `/login`
- Enter username and password
- Backend validates credentials and issues JWT token
- Token stored in localStorage/sessionStorage
- Redirect to `/admin/dashboard`

**2. Admin Dashboard**
- Display list of all exams (active/inactive)
- Options to: Create new exam, Edit, Delete, View questions, Activate/Deactivate, View results

**3. Create Exam**
- Admin fills form: name, description, duration, passing percentage
- Submits POST request to `/api/admin/exams`
- Backend creates exam record with exam_id
- Redirect to exam details page

**4. Add Questions to Exam**
- Admin views exam detail
- Click "Add Question"
- Form with: question text, 4 options (A, B, C, D), select correct answer
- Submit → API call to `/api/admin/exams/<exam_id>/questions`
- Questions displayed in list with edit/delete options

**5. Edit/Delete Questions**
- Admin can modify question text or options
- Can mark different option as correct
- Backend updates questions and options tables
- Changes immediately reflected in questions list

**6. Activate/Deactivate Exam**
- Admin toggles exam status
- Active exams appear in student's available exams
- Inactive exams are hidden from students
- Changes effective immediately

**7. View Student Results**
- Admin navigates to exam results
- Sees list of students who took exam with scores
- Click on student → view detailed results with answers

---

### Student User Flow

**1. Student Login**
- Navigate to `/login`
- Enter username and password
- Backend validates and issues JWT token
- Redirect to `/student/dashboard`

**2. Student Dashboard**
- Display list of available active exams
- Show exam name, duration, question count
- Button to "Start Exam" for each available exam
- Display past results with scores

**3. Start Exam**
- Click "Start Exam" button
- Backend calls `/api/student/exams/<exam_id>/start`
- Creates exam_submission record with status='in_progress'
- Backend records start time and IP address
- Frontend receives submission_id and redirect to exam interface
- Timer starts

**4. Exam Interface**
- Displays:
  - Question number and total (e.g., "Question 1 of 50")
  - Question text
  - 4 options (A, B, C, D) with radio buttons
  - Countdown timer (updates every second)
  - Progress bar showing questions answered
  - Navigation: Previous/Next buttons
  - "Submit Exam" button
  
**5. Answer Question**
- Student selects an option
- Click "Save Answer" or "Next"
- Frontend sends POST to `/api/student/submissions/<submission_id>/answer`
- Backend saves to student_answers table
- UI shows answer marked/saved

**6. Timer Management**
- Frontend timer counts down from exam duration
- Every 5 seconds, frontend calls `/api/student/submissions/<submission_id>/status`
- Backend validates:
  - Submission is still in_progress
  - Time not exceeded
  - Student doesn't have multiple active submissions for same exam
- If time exceeded, backend returns status='expired'
- Frontend auto-submits exam

**7. Auto-Submit Behavior**
- When timer reaches 0:00
  - Frontend shows alert "Time's up! Exam submitted automatically."
  - Calls POST `/api/student/submissions/<submission_id>/submit` with auto_submit=true
  - Backend marks status='auto_submitted'
  - Redirects to results page

**8. Manual Submission**
- Student clicks "Submit Exam" button
- Frontend shows confirmation dialog
- On confirm: POST to `/api/student/submissions/<submission_id>/submit`
- Backend calculates score by comparing student_answers with correct options
- Creates result record
- Returns result data to frontend
- Redirect to results page

**9. Results Page**
- Display:
  - Exam name and date taken
  - Score (e.g., 45/50)
  - Percentage (90%)
  - Pass/Fail status
  - Correct/Incorrect/Unanswered counts
  - Time taken
- Button to return to dashboard

---

## 6. TIMER, EXAM STATE, AUTO-SUBMIT, AND BACK-BUTTON HANDLING

### Timer Implementation

**Frontend Timer:**
```javascript
// Timer counts down from duration_minutes
// Updates UI every second
// Polls backend every 5-10 seconds for validation
// If backend says time expired, immediately submit

const remainingSeconds = 
  (duration_minutes * 60) - elapsed_seconds;

if (remainingSeconds <= 0) {
  // Auto-submit
}
```

**Backend Validation:**
- When student requests questions/answer/status:
  - Calculate elapsed_seconds = NOW() - exam_submissions.started_at
  - Compare with exam.duration_minutes
  - If elapsed_seconds > duration_minutes:
    - Automatically set submission status = 'auto_submitted'
    - Calculate score and create result
    - Reject any further answer submissions

**Why Backend Validation is Critical:**
- Student could modify timer in browser console
- Student could have unreliable internet (local timer drifts)
- Ensures exam integrity and prevents cheating

### Exam State Management

**Backend State Tracking:**
- exam_submissions table tracks state with status field:
  - 'in_progress': Exam ongoing
  - 'submitted': Student clicked submit
  - 'auto_submitted': Timer reached zero

**Prevent Double Submission:**
```
Before accepting submission:
- SELECT * FROM exam_submissions 
  WHERE student_id = ? AND exam_id = ? 
  AND status IN ('in_progress', 'auto_submitted', 'submitted')
  
If submission exists:
  - If status = 'in_progress': Allow submission
  - If status = 'submitted' or 'auto_submitted': Reject with "Exam already submitted"
```

**Prevent Multiple Active Exams:**
```
Before starting exam:
- SELECT * FROM exam_submissions 
  WHERE student_id = ? AND exam_id = ?
  AND status = 'in_progress'
  
If exists: Reject "Exam already started"
```

### Back-Button Behavior

**Frontend Implementation:**

1. **Detect Back-Button Attempt:**
   ```javascript
   useEffect(() => {
     const handlePopState = (e) => {
       if (isExamActive) {
         e.preventDefault();
         
         if (!backButtonWarningShown) {
           showWarningModal();
           setBackButtonWarningShown(true);
         } else {
           // Second attempt - auto-submit
           autoSubmitExam();
           setBackButtonWarningShown(false);
         }
       }
     };
     
     window.addEventListener('popstate', handlePopState);
     return () => window.removeEventListener('popstate', handlePopState);
   }, [isExamActive]);
   ```

2. **First Back-Button Click:**
   - Modal shows: "Are you sure? Leaving the exam will cause it to be submitted."
   - Options: "Stay in Exam" or "Leave Exam"
   - If "Stay": Close modal, continue exam
   - If "Leave": Auto-submit exam

3. **Mobile Back Button:**
   - Use React Router's `useBlocker` hook
   - Block navigation attempts with same warning flow

4. **Browser Back Button Disabled:**
   - Prevent history navigation during exam
   - Use `window.history.pushState()` to manage history
   - Listener on `popstate` event

**Backend Validation:**
- Even if student bypasses frontend:
  - Check submission status in `exam_submissions`
  - If already submitted/auto_submitted: Reject answer attempts
  - If time exceeded: Auto-submit via status check

**Why Backend Validation is Critical:**
- Student could disable JavaScript in browser
- Student could manipulate browser history
- Backend is source of truth for exam state

### Auto-Submit Flow Diagram
```
Exam Started (submission_id created)
    ↓
Timer Running (frontend counts down)
    ↓
Every 5-10 seconds: GET /api/student/submissions/<submission_id>/status
    ↓
    ├─ If status='expired' → Auto-submit on backend
    ├─ If user closes browser → Next request fails → Prompt to resume/resubmit
    └─ If time reaches 00:00 → Frontend auto-submits
    ↓
Submission Status = 'auto_submitted' or 'submitted'
    ↓
Result Created (score calculated)
    ↓
Student can only view results, not re-take exam
```

---

## 7. MISSING REQUIREMENTS & POTENTIAL PROBLEMS

### Missing Specifications

1. **Access Control Model**
   - Should only certain students be allowed to take certain exams?
   - Do all students have access to all exams?
   - Should we have exam_student_access table?
   - Recommendation: Implement access control table for flexibility

2. **Student Identification**
   - How do students get registered in system?
   - Does admin create student accounts?
   - Can students self-register?
   - Should there be email verification?
   - Recommendation: Clarify registration process

3. **Question Bank Reusability**
   - Can questions be reused across multiple exams?
   - Can questions be organized in categories?
   - Recommendation: Current design allows reusability

4. **Randomization**
   - Should questions appear in random order for each student?
   - Should options be shuffled for each student?
   - Recommendation: Add shuffle flags in questions table

5. **Exam Attempts**
   - Can student retake an exam multiple times?
   - If yes, should we track multiple submissions?
   - Current design allows multiple submissions (good)

6. **Negative Marking**
   - Is there negative marking for wrong answers?
   - Current design: Each question = 1 mark (no negative marking)
   - Recommendation: Add negative_marks field to questions

7. **Exam Duration Display**
   - Should remaining time be displayed to student?
   - Current design: Yes, countdown timer in frontend

8. **Review Before Submit**
   - Should student see summary of answers before final submit?
   - Recommendation: Add review page before submission

9. **Partial Scoring**
   - All or nothing for each question, or partial credit?
   - Current design: All or nothing

10. **Question Types**
    - Only multiple choice or also essay/short answer?
    - Current design: Only multiple choice
    - Recommendation: Extend if needed

---

### Potential Technical Problems & Solutions

**Problem 1: Network Lag and Timer Drift**
- Student's internet disconnects; frontend timer continues
- When reconnects, backend time has progressed differently
- Solution: Server-side timer validation; frontend trusts backend time
- Implementation: Sync time every 5 seconds; show "Syncing..." if lag detected

**Problem 2: Local Storage and State Recovery**
- Student refreshes page mid-exam; state lost
- Solution: Store submission_id and answers in backend; fetch on page load
- Implementation: Check for active exam_submission on mount; restore UI state

**Problem 3: Multiple Tab/Window Exploit**
- Student opens exam in 2 tabs; takes exam in both
- Solution: Backend rejects duplicate submissions; unique constraint on (student_id, exam_id)
- Implementation: Query returns error if submission already exists for this exam

**Problem 4: Mobile App Cache Issues**
- React app cached; student sees old exam content after admin updates it
- Solution: Cache busting with ETags or version numbers
- Implementation: Add version field to exams; invalidate cache on update

**Problem 5: Exam Active/Inactive Changes Mid-Exam**
- Admin deactivates exam while student is taking it
- Solution: Student can complete in-progress exams; only blocks new starts
- Implementation: Check is_active only when starting exam; allow submission for active submissions

**Problem 6: Password Security**
- Passwords stored in plain text would be critical vulnerability
- Solution: Use bcrypt/argon2 for password hashing
- Implementation: Hash on registration and login validation

**Problem 7: CORS and API Security**
- Frontend and backend on different origins
- Frontend could be accessed from any domain
- Solution: Proper CORS configuration; JWT token validation
- Implementation: CORS headers restricted to frontend domain; token in Authorization header

**Problem 8: SQL Injection**
- Malformed input in question_text or option_text
- Solution: Use parameterized queries (SQLAlchemy ORM)
- Implementation: Never concatenate user input into SQL

**Problem 9: Cheating Vectors**
- Student views network requests to see correct answers
- Solution: Correct answers never sent to browser during exam
- Implementation: API only returns options without is_correct; validation happens server-side

**Problem 10: Concurrent Modifications**
- Admin edits question while student is answering it
- Solution: Store question snapshot in student_answers
- Implementation: Include question_text in student_answers for audit trail

---

### Recommended Additional Features

1. **Session Management**
   - Add session timeout (e.g., logout after 30 mins inactivity)
   - Token refresh mechanism

2. **Audit Logging**
   - Log all admin actions (create/edit/delete exam)
   - Log student actions (start exam, answer, submit)
   - For compliance and debugging

3. **Exam Categories**
   - Organize exams by subject/topic
   - Help students find relevant exams

4. **Certificates**
   - Generate certificate for passing students
   - Download PDF option

5. **Analytics Dashboard**
   - Average score by exam
   - Pass rate statistics
   - Student performance trends

6. **Email Notifications**
   - Admin notified when all students complete
   - Student receives result summary email

7. **Question Import/Export**
   - CSV import for bulk question creation
   - Excel export of results

8. **Mobile App (Native)**
   - Better offline experience
   - Better back button handling on Android/iOS
   - Biometric login

---

## 8. IMPLEMENTATION PRIORITIES

### Phase 1 (MVP)
- [ ] User authentication (login/logout)
- [ ] Exam CRUD (create, read, update)
- [ ] Question & option CRUD
- [ ] Start exam and display questions
- [ ] Answer submission
- [ ] Timer (basic)
- [ ] Auto-submit on timeout
- [ ] Basic results calculation

### Phase 2 (Core Features)
- [ ] Back-button detection and warning
- [ ] Timer validation (server-side)
- [ ] Prevent double submission
- [ ] Review before submit
- [ ] Responsive UI (mobile/tablet/desktop)
- [ ] Admin results dashboard
- [ ] Student results history

### Phase 3 (Polish & Security)
- [ ] Input validation & error handling
- [ ] CORS and API security
- [ ] Password hashing & auth improvements
- [ ] Session management
- [ ] Exam access control
- [ ] Audit logging

### Phase 4 (Enhancement)
- [ ] Question randomization
- [ ] Partial scoring & negative marks
- [ ] Analytics dashboard
- [ ] Certificates
- [ ] Email notifications

---

## SUMMARY

This design provides:
✅ Clear separation between frontend, backend, and database
✅ Secure exam state management on backend
✅ Timer validation to prevent cheating
✅ Back-button handling with warnings
✅ Comprehensive API design
✅ Proper database schema with relationships
✅ User flow documentation
✅ Security considerations addressed
✅ Identified potential problems with solutions

**Ready to proceed with implementation?** 
Confirm and we will begin with:
1. Backend setup (Flask, SQLAlchemy models, database)
2. Frontend setup (React, components, context)
3. API endpoints implementation
4. Integration testing
