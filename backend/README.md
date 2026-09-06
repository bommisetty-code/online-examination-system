# Online Exam System - Backend (Flask)

## Overview
This is the Flask backend REST API for the Online Examination System. It handles authentication, exam management, student submissions, and scoring.

## Setup Instructions

### 1. Prerequisites
- Python 3.8+
- MySQL 8.0+
- pip (Python package manager)

### 2. Create Virtual Environment
```bash
python -m venv venv
```

### 3. Activate Virtual Environment
**Windows (PowerShell):**
```bash
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```bash
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Database

#### Option A: Using MySQL
1. Open MySQL command line or MySQL Workbench
2. Create database:
```sql
CREATE DATABASE online_exam_system;
```

3. Update `.env` file with your MySQL credentials:
```
DATABASE_URL=mysql+mysqlconnector://username:password@localhost/online_exam_system
```

#### Option B: Using SQLite (for development/testing)
Update `.env`:
```
DATABASE_URL=sqlite:///online_exam_system.db
```

### 6. Initialize Database

**Option A: Using Python script**
```bash
python init_db.py
```

This will:
- Create all tables
- Create a default admin user (username: admin, password: Admin123)
- Create a test student user (username: student, password: Student123)

**Option B: Manual table creation**
After running the app for the first time, tables will be auto-created by SQLAlchemy.

### 7. Run the Application
```bash
python run.py
```

The server will start on `http://localhost:5000`

## Environment Variables (.env)

```env
FLASK_ENV=development
FLASK_APP=run.py
FLASK_DEBUG=1

# Database Configuration
DATABASE_URL=mysql+mysqlconnector://root:password@localhost/online_exam_system

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production-12345

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## API Documentation

### Authentication Endpoints
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - User login
- `GET /api/auth/profile` - Get current user profile
- `POST /api/auth/logout` - User logout

### Admin Endpoints
- `GET /api/admin/exams` - Get all exams
- `POST /api/admin/exams` - Create new exam
- `GET /api/admin/exams/<exam_id>` - Get exam details
- `PUT /api/admin/exams/<exam_id>` - Update exam
- `DELETE /api/admin/exams/<exam_id>` - Delete exam
- `PATCH /api/admin/exams/<exam_id>/activate` - Activate/deactivate exam
- `GET /api/admin/exams/<exam_id>/questions` - Get all questions
- `POST /api/admin/exams/<exam_id>/questions` - Create question
- `PUT /api/admin/exams/<exam_id>/questions/<question_id>` - Update question
- `DELETE /api/admin/exams/<exam_id>/questions/<question_id>` - Delete question
- `GET /api/admin/exams/<exam_id>/results` - Get exam results
- `GET /api/admin/exams/<exam_id>/results/<student_id>` - Get student result details

### Student Endpoints
- `GET /api/student/exams` - Get available exams
- `GET /api/student/exams/<exam_id>` - Get exam details
- `POST /api/student/exams/<exam_id>/start` - Start an exam
- `GET /api/student/submissions/<submission_id>/questions` - Get exam questions
- `POST /api/student/submissions/<submission_id>/answer` - Submit an answer
- `GET /api/student/submissions/<submission_id>/status` - Get submission status
- `POST /api/student/submissions/<submission_id>/submit` - Submit exam
- `GET /api/student/results/<submission_id>` - Get exam result
- `GET /api/student/results/history` - Get all results

## Project Structure

```
backend/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── models.py             # SQLAlchemy models
│   ├── auth_routes.py        # Authentication endpoints
│   ├── admin_routes.py       # Admin endpoints
│   ├── student_routes.py     # Student endpoints
│   ├── decorators.py         # Role-based access control
│   ├── validators.py         # Input validation
│   ├── services.py           # Business logic services
│   ├── errors.py             # Custom exceptions
│   └── routes.py             # Blueprint exports
├── config.py                 # Configuration settings
├── run.py                    # Server entry point
├── init_db.py               # Database initialization
├── requirements.txt          # Python dependencies
├── .env                     # Environment variables
└── README.md                # This file
```

## Security Notes

✅ **Implemented:**
- Password hashing with bcrypt
- JWT token-based authentication
- Role-based access control (Admin/Student)
- CORS protection
- SQL injection prevention via ORM
- Backend validation of all inputs
- Server-side exam state management
- Timer validation on backend
- Correct answers never sent to student

⚠️ **Production Recommendations:**
- Change JWT_SECRET_KEY in production
- Use HTTPS instead of HTTP
- Configure CORS_ORIGINS for your frontend domain
- Set FLASK_DEBUG=0 in production
- Use a production database server
- Implement rate limiting
- Add logging and monitoring
- Regular security audits

## Testing

### Test Login with curl
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123"}'
```

### Test Create Exam (with token)
```bash
curl -X POST http://localhost:5000/api/admin/exams \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name":"Math Quiz",
    "description":"Basic Math Test",
    "duration_minutes":30,
    "passing_percentage":60
  }'
```

## Troubleshooting

### Database Connection Error
- Verify MySQL is running
- Check DATABASE_URL in .env
- Ensure credentials are correct
- Create database: `CREATE DATABASE online_exam_system;`

### Port Already in Use
- Default port is 5000
- Change in run.py: `app.run(..., port=5001)`

### JWT Token Errors
- Ensure Authorization header format: `Bearer <token>`
- Check JWT_SECRET_KEY is set
- Verify token hasn't expired

## License
MIT License
