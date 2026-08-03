from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'teacher', 'student'), default='teacher')
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class QuestionBank(db.Model):
    __tablename__ = 'question_bank'
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    chapter = db.Column(db.String(200))
    question_type = db.Column(db.String(50), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(500))
    option_b = db.Column(db.String(500))
    option_c = db.Column(db.String(500))
    option_d = db.Column(db.String(500))
    correct_answer = db.Column(db.String(200))
    difficulty = db.Column(db.String(20), default='Medium')
    language = db.Column(db.String(10), default='English')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class LessonPlan(db.Model):
    __tablename__ = 'lesson_plans'
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    chapter = db.Column(db.String(200), nullable=False)
    topic = db.Column(db.String(300))
    objectives = db.Column(db.Text)
    content = db.Column(db.Text)
    activities = db.Column(db.Text)
    assessment = db.Column(db.Text)
    duration = db.Column(db.String(50))
    language = db.Column(db.String(10), default='English')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Slide(db.Model):
    __tablename__ = 'slides'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    chapter = db.Column(db.String(200))
    slides_data = db.Column(db.Text)
    file_path = db.Column(db.String(500))
    language = db.Column(db.String(10), default='English')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Worksheet(db.Model):
    __tablename__ = 'worksheets'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    chapter = db.Column(db.String(200))
    content = db.Column(db.Text)
    total_marks = db.Column(db.Integer, default=20)
    language = db.Column(db.String(10), default='English')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FlashCard(db.Model):
    __tablename__ = 'flash_cards'
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    chapter = db.Column(db.String(200))
    front = db.Column(db.String(500), nullable=False)
    back = db.Column(db.String(500), nullable=False)
    language = db.Column(db.String(10), default='English')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ReportCard(db.Model):
    __tablename__ = 'report_cards'
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    roll_no = db.Column(db.String(20))
    term = db.Column(db.String(50))
    subjects_data = db.Column(db.Text)
    total_marks = db.Column(db.Integer)
    obtained_marks = db.Column(db.Integer)
    grade = db.Column(db.String(10))
    remarks = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_no = db.Column(db.String(20))
    class_name = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    parent_name = db.Column(db.String(100))
    address = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100))
    qualification = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FeeRecord(db.Model):
    __tablename__ = 'fee_records'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(20))
    year = db.Column(db.Integer)
    status = db.Column(db.String(20), default='Pending')
    paid_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Exam(db.Model):
    __tablename__ = 'exams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(100))
    date = db.Column(db.Date)
    total_marks = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notice(db.Model):
    __tablename__ = 'notices'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text)
    target = db.Column(db.String(50), default='all')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UploadedImage(db.Model):
    __tablename__ = 'uploaded_images'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    original_name = db.Column(db.String(300))
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True)
    class_name = db.Column(db.String(50), nullable=False)
    max_marks = db.Column(db.Integer, default=100)
    units = db.relationship('Unit', backref='subject', lazy=True)


class Unit(db.Model):
    __tablename__ = 'units'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=1)
    lessons = db.relationship('Lesson', backref='unit', lazy=True)


class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    order = db.Column(db.Integer, default=1)


class FileDocument(db.Model):
    __tablename__ = 'file_documents'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    original_name = db.Column(db.String(300))
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    class_name = db.Column(db.String(50))
    subject = db.Column(db.String(100))
    file_type = db.Column(db.String(20), default='pdf')
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


CLASS_CHOICES = [
    'Nursery', 'LKG', 'UKG',
    'Class 1', 'Class 2', 'Class 3', 'Class 4', 'Class 5',
    'Class 6', 'Class 7', 'Class 8', 'Class 9', 'Class 10',
    'Class 11', 'Class 12'
]

SUBJECT_CHOICES = [
    'English', 'Nepali', 'Mathematics', 'Science', 'Social Studies',
    'Computer', 'Health', 'OPT Mathematics', 'Accountancy',
    'Business Studies', 'Finance', 'Physics', 'Chemistry',
    'Biology', 'Economics', 'Geography', 'History', 'Civics',
    'Sanskrit', 'Hindi', 'Art', 'Physical Education'
]

QUESTION_TYPES = [
    'MCQ', 'Very Short Answer', 'Short Answer', 'Long Answer',
    'Case Based', 'HOTS', 'Fill in the Blanks', 'True/False',
    'Match the Following'
]

DIFFICULTY_LEVELS = ['Easy', 'Medium', 'Hard']
