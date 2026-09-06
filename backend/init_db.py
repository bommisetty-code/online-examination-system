"""
Database initialization script
Run this to create tables in MySQL
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_db():
    """Initialize database"""
    from app import create_app, db
    
    app = create_app('development')
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")
        
        # Create a default admin user for testing
        from app.models import User
        
        # Check if admin exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Creating default admin user...")
            admin = User(
                email='admin@exam.com',
                username='admin',
                full_name='Administrator',
                role='admin',
                is_active=True
            )
            admin.set_password('Admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: username=admin, password=Admin123")
        else:
            print("Admin user already exists")
        
        # Create a test student user
        student = User.query.filter_by(username='student').first()
        if not student:
            print("Creating test student user...")
            student = User(
                email='student@exam.com',
                username='student',
                full_name='Test Student',
                role='student',
                is_active=True
            )
            student.set_password('Student123')
            db.session.add(student)
            db.session.commit()
            print("Student user created: username=student, password=Student123")
        else:
            print("Student user already exists")

if __name__ == '__main__':
    try:
        init_db()
        print("\nDatabase initialization complete!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)
