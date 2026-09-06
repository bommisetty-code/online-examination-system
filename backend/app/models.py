from app import db
from datetime import datetime
from bcrypt import hashpw, gensalt, checkpw


# ============================================================
# USER MODEL
# ============================================================

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    full_name = db.Column(
        db.String(255),
        nullable=True
    )

    role = db.Column(
        db.Enum('admin', 'student'),
        nullable=False,
        default='student',
        index=True
    )

    # --------------------------------------------------------
    # Student Class
    # Admin -> NULL
    # Student -> 7th / 8th / 10th
    # --------------------------------------------------------

    student_class = db.Column(
        db.Enum('7th', '8th', '10th'),
        nullable=True,
        index=True
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        index=True
    )

    last_login = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # --------------------------------------------------------
    # Relationships
    # --------------------------------------------------------

    exams_created = db.relationship(
        'Exam',
        foreign_keys='Exam.created_by',
        backref='admin',
        cascade='all, delete-orphan'
    )

    submissions = db.relationship(
        'ExamSubmission',
        backref='student',
        cascade='all, delete-orphan'
    )

    # --------------------------------------------------------
    # Password
    # --------------------------------------------------------

    def set_password(self, password):
        self.password_hash = hashpw(
            password.encode('utf-8'),
            gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        return checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    # --------------------------------------------------------
    # Dictionary
    # --------------------------------------------------------

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name,
            'role': self.role,
            'student_class': self.student_class,
            'is_active': self.is_active,
            'last_login': (
                self.last_login.isoformat()
                if self.last_login
                else None
            ),
            'created_at': (
                self.created_at.isoformat()
                if self.created_at
                else None
            )
        }


# ============================================================
# EXAM MODEL
# ============================================================

class Exam(db.Model):
    __tablename__ = 'exams'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(255),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    duration_minutes = db.Column(
        db.Integer,
        nullable=False
    )

    # --------------------------------------------------------
    # Exam Class
    # MUST be student_class because database and routes
    # use the same name.
    # --------------------------------------------------------

    student_class = db.Column(
        db.Enum('7th', '8th', '10th'),
        nullable=False,
        index=True
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey(
            'users.id',
            ondelete='CASCADE'
        ),
        nullable=False,
        index=True
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        index=True
    )

    total_questions = db.Column(
        db.Integer,
        default=0,
        nullable=True
    )

    passing_percentage = db.Column(
        db.Numeric(5, 2),
        default=50.00,
        nullable=True
    )

    exam_code = db.Column(
        db.String(50),
        unique=True,
        index=True,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # --------------------------------------------------------
    # Relationships
    # --------------------------------------------------------

    questions = db.relationship(
        'Question',
        backref='exam',
        cascade='all, delete-orphan'
    )

    submissions = db.relationship(
        'ExamSubmission',
        backref='exam',
        cascade='all, delete-orphan'
    )

    results = db.relationship(
        'Result',
        backref='exam',
        cascade='all, delete-orphan'
    )

    # --------------------------------------------------------
    # Dictionary
    # --------------------------------------------------------

    def to_dict(self, include_questions=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'duration_minutes': self.duration_minutes,

            # IMPORTANT
            'student_class': self.student_class,

            'is_active': self.is_active,
            'total_questions': self.total_questions or 0,

            # Prevent float(None) error
            'passing_percentage': (
                float(self.passing_percentage)
                if self.passing_percentage is not None
                else 50.0
            ),

            'exam_code': self.exam_code,

            'created_at': (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),

            'updated_at': (
                self.updated_at.isoformat()
                if self.updated_at
                else None
            )
        }

        if include_questions:
            data['questions'] = [
                q.to_dict(include_options=True)
                for q in self.questions
            ]

        return data


# ============================================================
# QUESTION MODEL
# ============================================================

class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    exam_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'exams.id',
            ondelete='CASCADE'
        ),
        nullable=False,
        index=True
    )

    question_text = db.Column(
        db.Text,
        nullable=False
    )

    question_type = db.Column(
        db.Enum('multiple_choice'),
        default='multiple_choice',
        nullable=False
    )

    marks = db.Column(
        db.Integer,
        default=1,
        nullable=False
    )

    order_number = db.Column(
        db.Integer,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # --------------------------------------------------------
    # Relationships
    # --------------------------------------------------------

    options = db.relationship(
        'Option',
        backref='question',
        cascade='all, delete-orphan'
    )

    student_answers = db.relationship(
        'StudentAnswer',
        backref='question',
        cascade='all, delete-orphan'
    )

    __table_args__ = (
        db.Index(
            'idx_order',
            'order_number'
        ),
    )

    # --------------------------------------------------------
    # Dictionary
    # --------------------------------------------------------

    def to_dict(self, include_options=False):
        data = {
            'id': self.id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'marks': self.marks,
            'order_number': self.order_number
        }

        if include_options:
            # IMPORTANT:
            # Correct answer must NOT be sent to students.
            data['options'] = [
                {
                    'id': opt.id,
                    'option_text': opt.option_text,
                    'option_order': opt.option_order
                }
                for opt in self.options
            ]

        return data


# ============================================================
# OPTION MODEL
# ============================================================

class Option(db.Model):
    __tablename__ = 'options'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    question_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'questions.id',
            ondelete='CASCADE'
        ),
        nullable=False,
        index=True
    )

    option_text = db.Column(
        db.String(500),
        nullable=False
    )

    option_order = db.Column(
        db.Integer,
        nullable=False
    )

    is_correct = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def to_dict(self, include_correct=False):
        data = {
            'id': self.id,
            'option_text': self.option_text,
            'option_order': self.option_order
        }

        # Only Admin/Result processing should request this.
        if include_correct:
            data['is_correct'] = self.is_correct

        return data


# ============================================================
# EXAM SUBMISSION MODEL
# ============================================================

class ExamSubmission(db.Model):
    __tablename__ = 'exam_submissions'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'users.id',
            ondelete='CASCADE'
        ),
        nullable=False,
        index=True
    )

    exam_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'exams.id',
            ondelete='CASCADE'
        ),
        nullable=False,
        index=True
    )

    # Duration captured when the attempt starts.
    # Later exam duration changes will NOT affect
    # an already started attempt.
    duration_minutes = db.Column(
        db.Integer,
        nullable=False
    )

    status = db.Column(
        db.Enum(
            'in_progress',
            'submitted',
            'auto_submitted'
        ),
        default='in_progress',
        index=True
    )

    started_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    submitted_at = db.Column(
        db.DateTime,
        nullable=True
    )

    time_spent_seconds = db.Column(
        db.Integer,
        nullable=True
    )

    ip_address = db.Column(
        db.String(50),
        nullable=True
    )

    user_agent = db.Column(
        db.String(500),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # --------------------------------------------------------
    # Relationships
    # --------------------------------------------------------

    student_answers = db.relationship(
        'StudentAnswer',
        backref='submission',
        cascade='all, delete-orphan'
    )

    result = db.relationship(
        'Result',
        uselist=False,
        backref='submission',
        cascade='all, delete-orphan'
    )

    # --------------------------------------------------------
    # One student can attempt one exam only once.
    # --------------------------------------------------------

    __table_args__ = (
        db.UniqueConstraint(
            'student_id',
            'exam_id',
            name='unique_submission'
        ),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'exam_id': self.exam_id,
            'duration_minutes': self.duration_minutes,
            'status': self.status,

            'started_at': (
                self.started_at.isoformat()
                if self.started_at
                else None
            ),

            'submitted_at': (
                self.submitted_at.isoformat()
                if self.submitted_at
                else None
            ),

            'time_spent_seconds': self.time_spent_seconds
        }


# ============================================================
# STUDENT ANSWER MODEL
# ============================================================

class StudentAnswer(db.Model):
    __tablename__ = 'student_answers'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    submission_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'exam_submissions.id',
            ondelete='CASCADE'
        ),
        nullable=False,
        index=True
    )

    question_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'questions.id',
            ondelete='CASCADE'
        ),
        nullable=False,
        index=True
    )

    selected_option_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'options.id',
            ondelete='SET NULL'
        ),
        nullable=True
    )

    is_correct = db.Column(
        db.Boolean,
        nullable=True
    )

    answered_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint(
            'submission_id',
            'question_id',
            name='unique_answer'
        ),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'submission_id': self.submission_id,
            'question_id': self.question_id,
            'selected_option_id': self.selected_option_id,
            'is_correct': self.is_correct,

            'answered_at': (
                self.answered_at.isoformat()
                if self.answered_at
                else None
            )
        }


# ============================================================
# RESULT MODEL
# ============================================================

class Result(db.Model):
    __tablename__ = 'results'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    submission_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'exam_submissions.id',
            ondelete='CASCADE'
        ),
        nullable=False,
        unique=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'users.id',
            ondelete='CASCADE'
        ),
        nullable=False,
        index=True
    )

    exam_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'exams.id',
            ondelete='CASCADE'
        ),
        nullable=False,
        index=True
    )

    total_questions = db.Column(
        db.Integer,
        nullable=False
    )

    correct_answers = db.Column(
        db.Integer,
        nullable=False
    )

    incorrect_answers = db.Column(
        db.Integer,
        nullable=False
    )

    unanswered = db.Column(
        db.Integer,
        nullable=False
    )

    score = db.Column(
        db.Integer,
        nullable=False
    )

    total_marks = db.Column(
        db.Integer,
        nullable=False
    )

    percentage = db.Column(
        db.Numeric(5, 2),
        nullable=False
    )

    is_passed = db.Column(
        db.Boolean,
        nullable=False
    )

    submitted_at = db.Column(
        db.DateTime,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            'id': self.id,
            'submission_id': self.submission_id,
            'student_id': self.student_id,
            'exam_id': self.exam_id,

            'total_questions': self.total_questions,
            'correct_answers': self.correct_answers,
            'incorrect_answers': self.incorrect_answers,
            'unanswered': self.unanswered,

            'score': self.score,
            'total_marks': self.total_marks,

            'percentage': (
                float(self.percentage)
                if self.percentage is not None
                else 0.0
            ),

            'is_passed': self.is_passed,

            'submitted_at': (
                self.submitted_at.isoformat()
                if self.submitted_at
                else None
            ),

            'created_at': (
                self.created_at.isoformat()
                if self.created_at
                else None
            )
        }