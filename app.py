import os
import json
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import (db, User, QuestionBank, LessonPlan, Slide, Worksheet, FlashCard,
                    ReportCard, Student, Teacher, FeeRecord, Exam, Notice, UploadedImage,
                    Subject, Unit, Lesson, FileDocument,
                    CLASS_CHOICES, SUBJECT_CHOICES, QUESTION_TYPES, DIFFICULTY_LEVELS)

app = Flask(__name__)
app.config.from_object(Config)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'teacher')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))
        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    total_questions = QuestionBank.query.count()
    total_lessons = LessonPlan.query.count()
    total_slides = Slide.query.count()
    total_worksheets = Worksheet.query.count()
    notices = Notice.query.order_by(Notice.created_at.desc()).limit(5).all()
    recent_questions = QuestionBank.query.order_by(QuestionBank.created_at.desc()).limit(5).all()
    return render_template('dashboard.html',
                         total_students=total_students, total_teachers=total_teachers,
                         total_questions=total_questions, total_lessons=total_lessons,
                         total_slides=total_slides, total_worksheets=total_worksheets,
                         notices=notices, recent_questions=recent_questions,
                         classes=CLASS_CHOICES, subjects=SUBJECT_CHOICES)


@app.route('/generators')
@login_required
def generators():
    return render_template('generators/index.html',
                         classes=CLASS_CHOICES, subjects=SUBJECT_CHOICES,
                         question_types=QUESTION_TYPES, difficulties=DIFFICULTY_LEVELS)


@app.route('/generators/question-paper', methods=['GET', 'POST'])
@login_required
def question_paper_generator():
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        subject = request.form.get('subject')
        chapter = request.form.get('chapter')
        q_type = request.form.get('question_type')
        difficulty = request.form.get('difficulty')
        num_questions = int(request.form.get('num_questions', 10))
        total_marks = int(request.form.get('total_marks', 50))
        duration = request.form.get('duration', '2 Hours')
        language = request.form.get('language', 'English')

        query = QuestionBank.query
        if class_name: query = query.filter_by(class_name=class_name)
        if subject: query = query.filter_by(subject=subject)
        if chapter: query = query.filter_by(chapter=chapter)
        if q_type: query = query.filter_by(question_type=q_type)
        if difficulty: query = query.filter_by(difficulty=difficulty)
        if language != 'Both': query = query.filter_by(language=language)

        questions = query.limit(num_questions).all()
        return render_template('generators/question_paper_result.html',
                             questions=questions, class_name=class_name, subject=subject,
                             chapter=chapter, total_marks=total_marks, duration=duration,
                             date=date.today().strftime('%B %d, %Y'))

    return render_template('generators/question_paper.html',
                         classes=CLASS_CHOICES, subjects=SUBJECT_CHOICES,
                         question_types=QUESTION_TYPES, difficulties=DIFFICULTY_LEVELS)


@app.route('/generators/model-paper', methods=['GET', 'POST'])
@login_required
def model_paper_generator():
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        subject = request.form.get('subject')
        total_marks = int(request.form.get('total_marks', 100))
        duration = request.form.get('duration', '3 Hours')
        language = request.form.get('language', 'English')

        questions = QuestionBank.query.filter_by(class_name=class_name, subject=subject, language=language).all()
        return render_template('generators/model_paper_result.html',
                             questions=questions[:50], class_name=class_name, subject=subject,
                             total_marks=total_marks, duration=duration,
                             date=date.today().strftime('%B %d, %Y'))

    return render_template('generators/model_paper.html',
                         classes=CLASS_CHOICES, subjects=SUBJECT_CHOICES)


@app.route('/generators/practice-paper', methods=['GET', 'POST'])
@login_required
def practice_paper_generator():
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        subject = request.form.get('subject')
        chapter = request.form.get('chapter')
        language = request.form.get('language', 'English')
        num_questions = int(request.form.get('num_questions', 15))

        questions = QuestionBank.query.filter_by(class_name=class_name, subject=subject, language=language)
        if chapter: questions = questions.filter_by(chapter=chapter)
        questions = questions.limit(num_questions).all()
        return render_template('generators/practice_paper_result.html',
                             questions=questions, class_name=class_name, subject=subject,
                             date=date.today().strftime('%B %d, %Y'))

    return render_template('generators/practice_paper.html',
                         classes=CLASS_CHOICES, subjects=SUBJECT_CHOICES)


@app.route('/generators/mcq', methods=['GET', 'POST'])
@login_required
def mcq_generator():
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        subject = request.form.get('subject')
        chapter = request.form.get('chapter')
        difficulty = request.form.get('difficulty')
        num_questions = int(request.form.get('num_questions', 20))
        language = request.form.get('language', 'English')

        query = QuestionBank.query.filter_by(class_name=class_name, subject=subject, question_type='MCQ', language=language)
        if chapter: query = query.filter_by(chapter=chapter)
        if difficulty: query = query.filter_by(difficulty=difficulty)
        questions = query.limit(num_questions).all()
        return render_template('generators/mcq_result.html',
                             questions=questions, class_name=class_name, subject=subject,
                             date=date.today().strftime('%B %d, %Y'))

    return render_template('generators/mcq.html',
                         classes=CLASS_CHOICES, subjects=SUBJECT_CHOICES,
                         difficulties=DIFFICULTY_LEVELS)


@app.route('/generators/test', methods=['GET', 'POST'])
@login_required
def test_generator():
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        subject = request.form.get('subject')
        test_type = request.form.get('test_type', 'Unit Test')
        num_questions = int(request.form.get('num_questions', 10))
        total_marks = int(request.form.get('total_marks', 25))
        language = request.form.get('language', 'English')

        questions = QuestionBank.query.filter_by(class_name=class_name, subject=subject, language=language).limit(num_questions).all()
        return render_template('generators/test_result.html',
                             questions=questions, class_name=class_name, subject=subject,
                             test_type=test_type, total_marks=total_marks,
                             date=date.today().strftime('%B %d, %Y'))

    return render_template('generators/test.html',
                         classes=CLASS_CHOICES, subjects=SUBJECT_CHOICES)


@app.route('/generators/lesson-plan', methods=['GET', 'POST'])
@login_required
def lesson_plan_generator():
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        subject = request.form.get('subject')
        chapter = request.form.get('chapter')
        topic = request.form.get('topic')
        duration = request.form.get('duration', '45 minutes')
        language = request.form.get('language', 'English')

        lesson = LessonPlan(class_name=class_name, subject=subject, chapter=chapter,
                           topic=topic, duration=duration, language=language,
                           objectives=request.form.get('objectives'),
                           content=request.form.get('content'),
                           activities=request.form.get('activities'),
                           assessment=request.form.get('assessment'),
                           created_by=current_user.id)
        db.session.add(lesson)
        db.session.commit()
        return render_template('generators/lesson_plan_result.html', lesson=lesson)

    return render_template('generators/lesson_plan.html',
                         classes=CLASS_CHOICES, subjects=SUBJECT_CHOICES)


@app.route('/generators/slide', methods=['GET', 'POST'])
@login_required
def slide_generator():
    if request.method == 'POST':
        title = request.form.get('title')
        class_name = request.form.get('class_name')
        subject = request.form.get('subject')
        chapter = request.form.get('chapter')
        slides_content = request.form.get('slides_content')
        language = request.form.get('language', 'English')

        slide = Slide(title=title, class_name=class_name, subject=subject,
                     chapter=chapter, slides_data=slides_content, language=language,
                     created_by=current_user.id)
        db.session.add(slide)
        db.session.commit()
        flash('PPT/Slides generated successfully!', 'success')
        return redirect(url_for('slide_generator'))

    return render_template('generators/slide.html',
                         classes=CLASS_CHOICES, subjects=SUBJECT_CHOICES)


@app.route('/generators/flashcard', methods=['GET', 'POST'])
@login_required
def flashcard_generator():
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        subject = request.form.get('subject')
        chapter = request.form.get('chapter')
        front = request.form.get('front')
        back = request.form.get('back')
        language = request.form.get('language', 'English')

        card = FlashCard(class_name=class_name, subject=subject, chapter=chapter,
                        front=front, back=back, language=language, created_by=current_user.id)
        db.session.add(card)
        db.session.commit()
        flash('Flash card created!', 'success')

    cards = FlashCard.query.filter_by(created_by=current_user.id).order_by(FlashCard.created_at.desc()).limit(20).all()
    return render_template('generators/flashcard.html',
                         classes=CLASS_CHOICES, subjects=SUBJECT_CHOICES, cards=cards)


@app.route('/generators/worksheet', methods=['GET', 'POST'])
@login_required
def worksheet_generator():
    if request.method == 'POST':
        title = request.form.get('title')
        class_name = request.form.get('class_name')
        subject = request.form.get('subject')
        chapter = request.form.get('chapter')
        content = request.form.get('content')
        total_marks = int(request.form.get('total_marks', 20))
        language = request.form.get('language', 'English')

        ws = Worksheet(title=title, class_name=class_name, subject=subject,
                      chapter=chapter, content=content, total_marks=total_marks,
                      language=language, created_by=current_user.id)
        db.session.add(ws)
        db.session.commit()
        flash('Worksheet generated!', 'success')
        return redirect(url_for('worksheet_generator'))

    return render_template('generators/worksheet.html',
                         classes=CLASS_CHOICES, subjects=SUBJECT_CHOICES)


@app.route('/generators/report-card', methods=['GET', 'POST'])
@login_required
def report_card_generator():
    if request.method == 'POST':
        student_name = request.form.get('student_name')
        class_name = request.form.get('class_name')
        roll_no = request.form.get('roll_no')
        term = request.form.get('term')
        subjects_data = request.form.get('subjects_data')
        total_marks = int(request.form.get('total_marks', 500))
        obtained_marks = int(request.form.get('obtained_marks', 0))
        grade = request.form.get('grade', 'A')
        remarks = request.form.get('remarks')

        rc = ReportCard(student_name=student_name, class_name=class_name, roll_no=roll_no,
                       term=term, subjects_data=subjects_data, total_marks=total_marks,
                       obtained_marks=obtained_marks, grade=grade, remarks=remarks,
                       created_by=current_user.id)
        db.session.add(rc)
        db.session.commit()
        flash('Report card generated!', 'success')
        return redirect(url_for('report_card_generator'))

    return render_template('generators/report_card.html',
                         classes=CLASS_CHOICES, subjects=SUBJECT_CHOICES)


@app.route('/generators/quick-notes', methods=['GET', 'POST'])
@login_required
def quick_notes():
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        subject = request.form.get('subject')
        chapter = request.form.get('chapter')
        language = request.form.get('language', 'English')
        flash(f'Quick revision notes for {subject} - {chapter} generated!', 'success')

    return render_template('generators/quick_notes.html',
                         classes=CLASS_CHOICES, subjects=SUBJECT_CHOICES)


@app.route('/question-bank')
@login_required
def question_bank():
    class_filter = request.args.get('class', '')
    subject_filter = request.args.get('subject', '')
    type_filter = request.args.get('type', '')

    query = QuestionBank.query
    if class_filter: query = query.filter_by(class_name=class_filter)
    if subject_filter: query = query.filter_by(subject=subject_filter)
    if type_filter: query = query.filter_by(question_type=type_filter)

    questions = query.order_by(QuestionBank.created_at.desc()).all()
    return render_template('notes/question_bank.html',
                         questions=questions, classes=CLASS_CHOICES,
                         subjects=SUBJECT_CHOICES, question_types=QUESTION_TYPES,
                         class_filter=class_filter, subject_filter=subject_filter)


@app.route('/question-bank/add', methods=['GET', 'POST'])
@login_required
def add_question():
    if request.method == 'POST':
        q = QuestionBank(
            class_name=request.form.get('class_name'),
            subject=request.form.get('subject'),
            chapter=request.form.get('chapter'),
            question_type=request.form.get('question_type'),
            question_text=request.form.get('question_text'),
            option_a=request.form.get('option_a'),
            option_b=request.form.get('option_b'),
            option_c=request.form.get('option_c'),
            option_d=request.form.get('option_d'),
            correct_answer=request.form.get('correct_answer'),
            difficulty=request.form.get('difficulty', 'Medium'),
            language=request.form.get('language', 'English'),
            created_by=current_user.id
        )
        db.session.add(q)
        db.session.commit()
        flash('Question added successfully!', 'success')
        return redirect(url_for('question_bank'))

    return render_template('notes/add_question.html',
                         classes=CLASS_CHOICES, subjects=SUBJECT_CHOICES,
                         question_types=QUESTION_TYPES, difficulties=DIFFICULTY_LEVELS)


@app.route('/question-bank/delete/<int:qid>', methods=['POST'])
@login_required
def delete_question(qid):
    q = QuestionBank.query.get_or_404(qid)
    db.session.delete(q)
    db.session.commit()
    flash('Question deleted!', 'success')
    return redirect(url_for('question_bank'))


@app.route('/smart-notes')
@login_required
def smart_notes():
    class_filter = request.args.get('class', '')
    subject_filter = request.args.get('subject', '')

    query = LessonPlan.query
    if class_filter: query = query.filter_by(class_name=class_filter)
    if subject_filter: query = query.filter_by(subject=subject_filter)
    lessons = query.order_by(LessonPlan.created_at.desc()).all()
    return render_template('notes/smart_notes.html',
                         lessons=lessons, classes=CLASS_CHOICES, subjects=SUBJECT_CHOICES)


@app.route('/school/students')
@login_required
def school_students():
    students = Student.query.order_by(Student.name).all()
    return render_template('school/students.html', students=students, classes=CLASS_CHOICES)


@app.route('/school/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        s = Student(
            name=request.form.get('name'),
            roll_no=request.form.get('roll_no'),
            class_name=request.form.get('class_name'),
            section=request.form.get('section'),
            phone=request.form.get('phone'),
            parent_name=request.form.get('parent_name'),
            address=request.form.get('address')
        )
        db.session.add(s)
        db.session.commit()
        flash('Student added successfully!', 'success')
        return redirect(url_for('school_students'))
    return render_template('school/add_student.html', classes=CLASS_CHOICES)


@app.route('/school/teachers')
@login_required
def school_teachers():
    teachers = Teacher.query.order_by(Teacher.name).all()
    return render_template('school/teachers.html', teachers=teachers, subjects=SUBJECT_CHOICES)


@app.route('/school/teachers/add', methods=['GET', 'POST'])
@login_required
def add_teacher():
    if request.method == 'POST':
        t = Teacher(
            name=request.form.get('name'),
            subject=request.form.get('subject'),
            qualification=request.form.get('qualification'),
            phone=request.form.get('phone')
        )
        db.session.add(t)
        db.session.commit()
        flash('Teacher added successfully!', 'success')
        return redirect(url_for('school_teachers'))
    return render_template('school/add_teacher.html', subjects=SUBJECT_CHOICES)


@app.route('/school/fees')
@login_required
def school_fees():
    students = Student.query.all()
    return render_template('school/fees.html', students=students)


@app.route('/school/exams')
@login_required
def school_exams():
    exams = Exam.query.order_by(Exam.date.desc()).all()
    return render_template('school/exams.html', exams=exams, classes=CLASS_CHOICES, subjects=SUBJECT_CHOICES)


@app.route('/school/exams/add', methods=['GET', 'POST'])
@login_required
def add_exam():
    if request.method == 'POST':
        e = Exam(
            name=request.form.get('name'),
            class_name=request.form.get('class_name'),
            subject=request.form.get('subject'),
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date(),
            total_marks=int(request.form.get('total_marks', 100))
        )
        db.session.add(e)
        db.session.commit()
        flash('Exam added successfully!', 'success')
        return redirect(url_for('school_exams'))
    return render_template('school/add_exam.html', classes=CLASS_CHOICES, subjects=SUBJECT_CHOICES)


@app.route('/school/notices')
@login_required
def school_notices():
    notices = Notice.query.order_by(Notice.created_at.desc()).all()
    return render_template('school/notices.html', notices=notices)


@app.route('/school/notices/add', methods=['GET', 'POST'])
@login_required
def add_notice():
    if request.method == 'POST':
        n = Notice(
            title=request.form.get('title'),
            content=request.form.get('content'),
            target=request.form.get('target', 'all'),
            created_by=current_user.id
        )
        db.session.add(n)
        db.session.commit()
        flash('Notice published!', 'success')
        return redirect(url_for('school_notices'))
    return render_template('school/add_notice.html')


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_image():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        if file:
            filename = datetime.now().strftime('%Y%m%d_%H%M%S_') + file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img = UploadedImage(
                filename=filename, original_name=file.filename,
                category=request.form.get('category'),
                description=request.form.get('description'),
                uploaded_by=current_user.id
            )
            db.session.add(img)
            db.session.commit()
            flash('Image uploaded successfully!', 'success')
            return redirect(url_for('upload_image'))

    images = UploadedImage.query.order_by(UploadedImage.created_at.desc()).all()
    return render_template('school/upload.html', images=images)


@app.route('/ai-assistant')
@login_required
def ai_assistant():
    return render_template('ai/assistant.html')


@app.route('/api/generate-content', methods=['POST'])
@login_required
def api_generate_content():
    data = request.get_json()
    content_type = data.get('type')
    class_name = data.get('class_name')
    subject = data.get('subject')
    topic = data.get('topic')

    sample_content = {
        'mcq': [
            {'q': f'What is the primary function of {topic}?', 'a': 'Option A', 'b': 'Option B', 'c': 'Option C', 'd': 'Option D', 'ans': 'Option A'},
            {'q': f'Which describes {topic} best?', 'a': 'Description 1', 'b': 'Description 2', 'c': 'Description 3', 'd': 'Description 4', 'ans': 'Description 1'},
        ],
        'short_answer': [
            f'Define {topic} in your own words.',
            f'List any three characteristics of {topic}.',
            f'Explain the importance of {topic} in {subject}.',
        ],
        'long_answer': [
            f'Describe {topic} in detail with examples.',
            f'Explain the various aspects of {topic} and their significance.',
        ],
        'lesson_plan': {
            'objectives': f'Understand the concept of {topic}\nApply knowledge of {topic} in real life\nAnalyze different aspects of {topic}',
            'content': f'Introduction to {topic}\nDetailed explanation\nKey concepts and definitions\nExamples and illustrations\nSummary',
            'activities': f'Discussion about {topic}\nGroup activity\nIndividual practice\nQ&A session',
            'assessment': f'Quiz on {topic}\nWorksheet assignment\nProject work'
        }
    }

    return jsonify({'success': True, 'data': sample_content.get(content_type, sample_content['mcq'])})


@app.route('/admin/cdc-info')
def cdc_info():
    return render_template('cdc_info.html')


@app.route('/files')
@login_required
def files_list():
    class_filter = request.args.get('class', '')
    query = FileDocument.query
    if class_filter:
        query = query.filter_by(class_name=class_filter)
    files = query.order_by(FileDocument.created_at.desc()).all()
    return render_template('files/list.html', files=files, classes=CLASS_CHOICES, class_filter=class_filter)


@app.route('/files/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        if file:
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'bin'
            filename = datetime.now().strftime('%Y%m%d_%H%M%S_') + file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            fd = FileDocument(
                filename=filename,
                original_name=file.filename,
                category=request.form.get('category'),
                description=request.form.get('description'),
                class_name=request.form.get('class_name'),
                subject=request.form.get('subject'),
                file_type=ext,
                uploaded_by=current_user.id
            )
            db.session.add(fd)
            db.session.commit()
            flash('File uploaded successfully!', 'success')
            return redirect(url_for('files_list'))

    return render_template('files/upload.html', classes=CLASS_CHOICES, subjects=SUBJECT_CHOICES)


@app.route('/files/download/<int:fid>')
@login_required
def download_file(fid):
    fd = FileDocument.query.get_or_404(fid)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], fd.filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name=fd.original_name)
    flash('File not found', 'danger')
    return redirect(url_for('files_list'))


@app.route('/files/delete/<int:fid>', methods=['POST'])
@login_required
def delete_file(fid):
    fd = FileDocument.query.get_or_404(fid)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], fd.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(fd)
    db.session.commit()
    flash('File deleted!', 'success')
    return redirect(url_for('files_list'))


def init_db():
def curriculum_list():
    class_filter = request.args.get('class', '')
    subjects = Subject.query
    if class_filter:
        subjects = subjects.filter_by(class_name=class_filter)
    subjects = subjects.order_by(Subject.class_name, Subject.name).all()
    return render_template('curriculum/list.html', subjects=subjects, classes=CLASS_CHOICES, class_filter=class_filter)


@app.route('/curriculum/subjects/<int:sid>/units')
@login_required
def units_list(sid):
    subject = Subject.query.get_or_404(sid)
    units = Unit.query.filter_by(subject_id=sid).order_by(Unit.order).all()
    return render_template('curriculum/units.html', subject=subject, units=units)


@app.route('/curriculum/units/<int:uid>/lessons')
@login_required
def lessons_list(uid):
    unit = Unit.query.get_or_404(uid)
    lessons = Lesson.query.filter_by(unit_id=uid).order_by(Lesson.order).all()
    return render_template('curriculum/lessons.html', unit=unit, lessons=lessons)


@app.route('/curriculum/subjects/<int:sid>/units/add', methods=['GET', 'POST'])
@login_required
def add_unit(sid):
    subject = Subject.query.get_or_404(sid)
    if request.method == 'POST':
        u = Unit(subject_id=sid, name=request.form.get('name'),
                 description=request.form.get('description'),
                 order=int(request.form.get('order', 1)))
        db.session.add(u)
        db.session.commit()
        flash('Unit added!', 'success')
        return redirect(url_for('units_list', sid=sid))
    return render_template('curriculum/add_unit.html', subject=subject)


@app.route('/curriculum/units/<int:uid>/lessons/add', methods=['GET', 'POST'])
@login_required
def add_lesson(uid):
    unit = Unit.query.get_or_404(uid)
    if request.method == 'POST':
        l = Lesson(unit_id=uid, name=request.form.get('name'),
                   description=request.form.get('description'),
                   content=request.form.get('content'),
                   order=int(request.form.get('order', 1)))
        db.session.add(l)
        db.session.commit()
        flash('Lesson added!', 'success')
        return redirect(url_for('lessons_list', uid=uid))
    return render_template('curriculum/add_lesson.html', unit=unit)


def init_db():
    with app.app_context():
        db.create_all()
        if User.query.count() == 0:
            admin = User(name='Admin', email='admin@akeasypathshala.com', role='admin')
            admin.set_password('admin123')
            teacher = User(name='Teacher', email='teacher@akeasypathshala.com', role='teacher')
            teacher.set_password('teacher123')
            db.session.add_all([admin, teacher])
            db.session.commit()
            print("Database initialized!")
            print("Admin: admin@akeasypathshala.com / admin123")
            print("Teacher: teacher@akeasypathshala.com / teacher123")


def populate_curriculum():
    with app.app_context():
        if Subject.query.count() == 0:
            curriculum = {
                'Class 1': {
                    'English': [
                        ('Unit 1: The Alphabet', ['Lesson 1: Aa', 'Lesson 2: Bb', 'Lesson 3: Cc', 'Lesson 4: Dd', 'Lesson 5: Ee']),
                        ('Unit 2: My Family', ['Lesson 1: My Mother', 'Lesson 2: My Father', 'Lesson 3: My Brother', 'Lesson 4: My Sister']),
                        ('Unit 3: My School', ['Lesson 1: My Classroom', 'Lesson 2: My Teacher', 'Lesson 3: My Friends', 'Lesson 4: My Books']),
                        ('Unit 4: Animals', ['Lesson 1: Pet Animals', 'Lesson 2: Wild Animals', 'Lesson 3: Birds', 'Lesson 4: Fish']),
                        ('Unit 5: Fruits and Vegetables', ['Lesson 1: Fruits', 'Lesson 2: Vegetables', 'Lesson 3: Eating Habits']),
                    ],
                    'Nepali': [
                        ('Unit 1: Nepali Lipi', ['Lesson 1: Ka', 'Lesson 2: Kha', 'Lesson 3: Ga', 'Lesson 4: Gha']),
                        ('Unit 2: Mero Parivar', ['Lesson 1: Mai', 'Lesson 2: Baba', 'Lesson 3: Aama']),
                        ('Unit 3: Mero School', ['Lesson 1: Sadan', 'Lesson 2: Guru']),
                    ],
                    'Mathematics': [
                        ('Unit 1: Numbers 1-10', ['Lesson 1: Counting 1-5', 'Lesson 2: Counting 6-10', 'Lesson 3: Writing Numbers']),
                        ('Unit 2: Addition', ['Lesson 1: Add with Objects', 'Lesson 2: Add with Numbers']),
                        ('Unit 3: Subtraction', ['Lesson 1: Subtract with Objects', 'Lesson 2: Subtract with Numbers']),
                        ('Unit 4: Shapes', ['Lesson 1: Circle', 'Lesson 2: Square', 'Lesson 3: Triangle', 'Lesson 4: Rectangle']),
                    ],
                    'Science': [
                        ('Unit 1: Our Body', ['Lesson 1: Head and Brain', 'Lesson 2: Hands and Legs', 'Lesson 3: Eyes and Ears']),
                        ('Unit 2: Plants', ['Lesson 1: Parts of a Plant', 'Lesson 2: Water and Plants', 'Lesson 3: Flowers']),
                        ('Unit 3: Animals', ['Lesson 1: Mammals', 'Lesson 2: Birds', 'Lesson 3: Insects']),
                    ],
                    'Social Studies': [
                        ('Unit 1: My Home', ['Lesson 1: My House', 'Lesson 2: My Neighbours', 'Lesson 3: My Village/City']),
                        ('Unit 2: Nepal', ['Lesson 1: Nepal is My Country', 'Lesson 2: National Symbols', 'Lesson 3: Festivals']),
                    ],
                    'Computer': [
                        ('Unit 1: Computer Basics', ['Lesson 1: What is a Computer?', 'Lesson 2: Parts of a Computer']),
                    ],
                    'Health': [
                        ('Unit 1: Cleanliness', ['Lesson 1: Hand Washing', 'Lesson 2: Brushing Teeth', 'Lesson 3: Clean Food']),
                    ],
                },
                'Class 2': {
                    'English': [
                        ('Unit 1: Reading Together', ['Lesson 1: A Nice Day', 'Lesson 2: My Pet', 'Lesson 3: Colors']),
                        ('Unit 2: My World', ['Lesson 1: My Home', 'Lesson 2: My Neighbourhood', 'Lesson 3: My Country']),
                        ('Unit 3: Fun with Words', ['Lesson 1: Action Words', 'Lesson 2: Describing Words', 'Lesson 3: Opposite Words']),
                        ('Unit 4: Stories', ['Lesson 1: The Tortoise and the Hare', 'Lesson 2: The Thirsty Crow', 'Lesson 3: The Lion and the Mouse']),
                        ('Unit 5: Poems', ['Lesson 1: Twinkle Twinkle', 'Lesson 2: One Two Buckle My Shoe']),
                    ],
                    'Nepali': [
                        ('Unit 1: Nepali Lipi', ['Lesson 1: Na', 'Lesson 2: Cha', 'Lesson 3: Ja', 'Lesson 4: Nya']),
                        ('Unit 2: Mero Desh', ['Lesson 1: Nepal ko Samanya', 'Lesson 2: Nepal ko Parichay']),
                        ('Unit 3: Kishori Geet', ['Lesson 1: Nepali Lok Geet']),
                    ],
                    'Mathematics': [
                        ('Unit 1: Numbers 1-100', ['Lesson 1: Counting', 'Lesson 2: Place Value', 'Lesson 3: Writing Numbers']),
                        ('Unit 2: Addition and Subtraction', ['Lesson 1: Addition', 'Lesson 2: Subtraction', 'Lesson 3: Word Problems']),
                        ('Unit 3: Measurement', ['Lesson 1: Length', 'Lesson 2: Weight', 'Lesson 3: Capacity']),
                        ('Unit 4: Time and Money', ['Lesson 1: Days and Months', 'Lesson 2: Coins and Notes']),
                    ],
                    'Science': [
                        ('Unit 1: Matter', ['Lesson 1: Hard and Soft', 'Lesson 2: Rough and Smooth', 'Lesson 3: Heavy and Light']),
                        ('Unit 2: Living and Non-Living', ['Lesson 1: Living Things', 'Lesson 2: Non-Living Things']),
                        ('Unit 3: Water', ['Lesson 1: Sources of Water', 'Lesson 2: Water Cycle', 'Lesson 3: Saving Water']),
                    ],
                    'Social Studies': [
                        ('Unit 1: Community Helpers', ['Lesson 1: Doctor', 'Lesson 2: Teacher', 'Lesson 3: Farmer', 'Lesson 4: Police']),
                        ('Unit 2: Nepal', ['Lesson 1: Nepal ko Rajya', 'Lesson 2: Nepal ko Jati-Bhat']),
                    ],
                    'Computer': [
                        ('Unit 1: Using Computer', ['Lesson 1: Turning On/Off', 'Lesson 2: Mouse', 'Lesson 3: Keyboard']),
                    ],
                    'Health': [
                        ('Unit 1: Health and Hygiene', ['Lesson 1: Balanced Diet', 'Lesson 2: Exercise', 'Lesson 3: Sleep']),
                    ],
                },
                'Class 3': {
                    'English': [
                        ('Unit 1: The World in a Garden', ['Lesson 1: Plants Around Us', 'Lesson 2: In the Garden', 'Lesson 3: Flowers']),
                        ('Unit 2: Good Habits', ['Lesson 1: Early to Bed', 'Lesson 2: Cleanliness', 'Lesson 3: Sharing']),
                        ('Unit 3: Stories and Poems', ['Lesson 1: The Magic Garden', 'Lesson 2: The Little Bird', 'Lesson 3: Rhymes']),
                        ('Unit 4: Our Friends', ['Lesson 1: Human Friends', 'Lesson 2: Animal Friends', 'Lesson 3: Books are Friends']),
                        ('Unit 5: Travel', ['Lesson 1: By Air', 'Lesson 2: By Train', 'Lesson 3: By Road']),
                    ],
                    'Nepali': [
                        ('Unit 1: Nepali Lipi', ['Lesson 1: Pa', 'Lesson 2: Pha', 'Lesson 3: Ba', 'Lesson 4: Bha']),
                        ('Unit 2: Mero Desh Nepal', ['Lesson 1: Nepal ko Itihas', 'Lesson 2: Nepal ko Prant']),
                        ('Unit 3: Kishori Kavita', ['Lesson 1: Nepali Kavita']),
                    ],
                    'Mathematics': [
                        ('Unit 1: Numbers beyond 100', ['Lesson 1: Hundreds', 'Lesson 2: Thousands', 'Lesson 3: Place Value']),
                        ('Unit 2: Multiplication', ['Lesson 1: Tables of 2-5', 'Lesson 2: Tables of 6-9', 'Lesson 3: Word Problems']),
                        ('Unit 3: Division', ['Lesson 1: Basic Division', 'Lesson 2: Division with Remainder']),
                        ('Unit 4: Fractions', ['Lesson 1: Half', 'Lesson 2: Quarter', 'Lesson 3: Third']),
                    ],
                    'Science': [
                        ('Unit 1: Force and Motion', ['Lesson 1: Push and Pull', 'Lesson 2: Fast and Slow', 'Lesson 3: Direction']),
                        ('Unit 2: Light and Shadow', ['Lesson 1: Sources of Light', 'Lesson 2: Shadows', 'Lesson 3: Reflection']),
                        ('Unit 3: Rocks and Soil', ['Lesson 1: Types of Rocks', 'Lesson 2: Soil', 'Lesson 3: Uses of Rocks']),
                    ],
                    'Social Studies': [
                        ('Unit 1: Our Culture', ['Lesson 1: Festivals', 'Lesson 2: Dress', 'Lesson 3: Food', 'Lesson 4: Language']),
                        ('Unit 2: Map and Direction', ['Lesson 1: Directions', 'Lesson 2: Map Reading']),
                    ],
                    'Computer': [
                        ('Unit 1: Introduction to Software', ['Lesson 1: What is Software?', 'Lesson 2: Drawing on Computer']),
                    ],
                    'Health': [
                        ('Unit 1: Our Health', ['Lesson 1: Balanced Diet', 'Lesson 2: Diseases and Prevention', 'Lesson 3: First Aid']),
                    ],
                },
                'Class 4': {
                    'English': [
                        ('Unit 1: My World', ['Lesson 1: My Home', 'Lesson 2: My Neighbourhood', 'Lesson 3: My City']),
                        ('Unit 2: Stories', ['Lesson 1: The Boy and the Mangoes', 'Lesson 2: The Clever Fox', 'Lesson 3: The Kind Baker']),
                        ('Unit 3: Poems', ['Lesson 1: Rain', 'Lesson 2: The Swing', 'Lesson 3: My Mother']),
                        ('Unit 4: Let Us Communicate', ['Lesson 1: Letter Writing', 'Lesson 2: Email', 'Lesson 3: Telephonic Conversation']),
                        ('Unit 5: People Who Help Us', ['Lesson 1: Doctor', 'Lesson 2: Fire Fighter', 'Lesson 3: Postman']),
                    ],
                    'Nepali': [
                        ('Unit 1: Nepali Lipi', ['Lesson 1: Ma', 'Lesson 2: Cha', 'Lesson 3: Ya', 'Lesson 4: Ra']),
                        ('Unit 2: Nepali Lok Katha', ['Lesson 1: Lok Katha 1', 'Lesson 2: Lok Katha 2']),
                        ('Unit 3: Mero Desh', ['Lesson 1: Nepal ko Mahal']),
                    ],
                    'Mathematics': [
                        ('Unit 1: Large Numbers', ['Lesson 1: Numbers up to 10000', 'Lesson 2: Place Value', 'Lesson 3: Comparing Numbers']),
                        ('Unit 2: Multiplication and Division', ['Lesson 1: Tables', 'Lesson 2: Long Multiplication', 'Lesson 3: Long Division']),
                        ('Unit 3: Fractions', ['Lesson 1: Equivalent Fractions', 'Lesson 2: Adding Fractions', 'Lesson 3: Subtracting Fractions']),
                        ('Unit 4: Measurement', ['Lesson 1: Length', 'Lesson 2: Mass', 'Lesson 3: Capacity', 'Lesson 4: Time']),
                    ],
                    'Science': [
                        ('Unit 1: Living Things', ['Lesson 1: Characteristics of Living Things', 'Lesson 2: Habitats', 'Lesson 3: Adaptation']),
                        ('Unit 2: Our Environment', ['Lesson 1: Air', 'Lesson 2: Water', 'Lesson 3: Soil', 'Lesson 4: Pollution']),
                        ('Unit 3: Force and Energy', ['Lesson 1: Types of Forces', 'Lesson 2: Energy']),
                    ],
                    'Social Studies': [
                        ('Unit 1: Nepal ko Itihas', ['Lesson 1: Ancient Nepal', 'Lesson 2: Medieval Nepal', 'Lesson 3: Modern Nepal']),
                        ('Unit 2: Nepal ko Bhugol', ['Lesson 1: Location', 'Lesson 2: Mountains', 'Lesson 3: Rivers', 'Lesson 4: Climate']),
                    ],
                    'Computer': [
                        ('Unit 1: Internet', ['Lesson 1: What is Internet?', 'Lesson 2: Browsing', 'Lesson 3: Safe Internet']),
                    ],
                    'Health': [
                        ('Unit 1: Disease Prevention', ['Lesson 1: Communicable Diseases', 'Lesson 2: Non-Communicable Diseases', 'Lesson 3: Vaccination']),
                    ],
                },
                'Class 5': {
                    'English': [
                        ('Unit 1: Adventure', ['Lesson 1: Ali and the Magic Carpet', 'Lesson 2: The Brave Little Tailor', 'Lesson 3: Journey to the Centre of the Earth']),
                        ('Unit 2: Animal Kingdom', ['Lesson 1: Mammals', 'Lesson 2: Birds', 'Lesson 3: Reptiles', 'Lesson 4: Insects']),
                        ('Unit 3: Poems and Rhymes', ['Lesson 1: The Owl and the Pussycat', 'Lesson 2: The Land of Nod']),
                        ('Unit 4: People Who Help Us', ['Lesson 1: Community Workers', 'Lesson 2: Volunteers']),
                        ('Unit 5: Let Us Communicate', ['Lesson 1: Notice Writing', 'Lesson 2: Diary Entry', 'Lesson 3: Story Writing']),
                    ],
                    'Nepali': [
                        ('Unit 1: Nepali Sahitya', ['Lesson 1: Nepali Kabita', 'Lesson 2: Nepali Katha']),
                        ('Unit 2: Mero Desh Nepal', ['Lesson 1: Nepal ko Mukhtesher Sthan']),
                        ('Unit 3: Nepali Lipi', ['Lesson 1: Writing Practice']),
                    ],
                    'Mathematics': [
                        ('Unit 1: Numbers', ['Lesson 1: Numbers up to 100000', 'Lesson 2: Roman Numerals', 'Lesson 3: Operations']),
                        ('Unit 2: Fractions and Decimals', ['Lesson 1: Fractions', 'Lesson 2: Decimals', 'Lesson 3: Conversion']),
                        ('Unit 3: Geometry', ['Lesson 1: Lines and Angles', 'Lesson 2: Triangles', 'Lesson 3: Quadrilaterals']),
                        ('Unit 4: Measurement', ['Lesson 1: Area', 'Lesson 2: Perimeter', 'Lesson 3: Volume']),
                    ],
                    'Science': [
                        ('Unit 1: Matter', ['Lesson 1: States of Matter', 'Lesson 2: Changes in Matter', 'Lesson 3: Mixtures and Solutions']),
                        ('Unit 2: Living Things', ['Lesson 1: Cells', 'Lesson 2: Plant and Animal Cells', 'Lesson 3: Microorganisms']),
                        ('Unit 3: Force and Motion', ['Lesson 1: Newton Laws', 'Lesson 2: Friction', 'Lesson 3: Simple Machines']),
                    ],
                    'Social Studies': [
                        ('Unit 1: Nepal ko Itihas', ['Lesson 1: Ancient Civilization', 'Lesson 2: Shah Dynasty']),
                        ('Unit 2: Nepal ko Bhugol', ['Lesson 1: Physical Features', 'Lesson 2: Natural Resources']),
                        ('Unit 3: Economic Activities', ['Lesson 1: Agriculture', 'Lesson 2: Industry', 'Lesson 3: Trade']),
                    ],
                    'Computer': [
                        ('Unit 1: Programming Basics', ['Lesson 1: What is Programming?', 'Lesson 2: Scratch Basics']),
                    ],
                    'Health': [
                        ('Unit 1: Personal Health', ['Lesson 1: Nutrition', 'Lesson 2: Exercise', 'Lesson 3: Mental Health']),
                    ],
                },
                'Class 6': {
                    'English': [
                        ('Unit 1: English Literature', ['Lesson 1: Prose', 'Lesson 2: Poetry', 'Lesson 3: Drama']),
                        ('Unit 2: Grammar', ['Lesson 1: Parts of Speech', 'Lesson 2: Tenses', 'Lesson 3: Subject-Verb Agreement']),
                        ('Unit 3: Writing Skills', ['Lesson 1: Letter Writing', 'Lesson 2: Paragraph Writing', 'Lesson 3: Essay Writing']),
                        ('Unit 4: Comprehension', ['Lesson 1: Reading Comprehension', 'Lesson 2: Answering Questions']),
                        ('Unit 5: Vocabulary', ['Lesson 1: Synonyms and Antonyms', 'Lesson 2: One Word Substitution', 'Lesson 3: Idioms']),
                    ],
                    'Nepali': [
                        ('Unit 1: Nepali Sahitya', ['Lesson 1: Bhanubhakta Acharya', 'Lesson 2: Lakshmi Prasad Devkota']),
                        ('Unit 2: Nepali Grammar', ['Lesson 1: Byakaran', 'Lesson 2: Sandhi']),
                        ('Unit 3: Nepali Writing', ['Lesson 1: Nibandh', 'Lesson 2: Kavita']),
                    ],
                    'Mathematics': [
                        ('Unit 1: Number System', ['Lesson 1: Integers', 'Lesson 2: Rational Numbers', 'Lesson 3: Exponents']),
                        ('Unit 2: Algebra', ['Lesson 1: Variables and Expressions', 'Lesson 2: Linear Equations', 'Lesson 3: Polynomials']),
                        ('Unit 3: Geometry', ['Lesson 1: Lines and Angles', 'Lesson 2: Triangles', 'Lesson 3: Quadrilaterals', 'Lesson 4: Circles']),
                        ('Unit 4: Ratio and Proportion', ['Lesson 1: Ratios', 'Lesson 2: Proportions', 'Lesson 3: Percentage']),
                    ],
                    'Science': [
                        ('Unit 1: Biology', ['Lesson 1: Cell', 'Lesson 2: Tissues', 'Lesson 3: Plant Physiology']),
                        ('Unit 2: Physics', ['Lesson 1: Force and Pressure', 'Lesson 2: Motion', 'Lesson 3: Sound']),
                        ('Unit 3: Chemistry', ['Lesson 1: Matter', 'Lesson 2: Elements and Compounds', 'Lesson 3: Water']),
                    ],
                    'Social Studies': [
                        ('Unit 1: Nepal ko Itihas', ['Lesson 1: Ancient History', 'Lesson 2: Medieval Period', 'Lesson 3: Modern History']),
                        ('Unit 2: Nepal ko Bhugol', ['Lesson 1: Physical Geography', 'Lesson 2: Climate', 'Lesson 3: Natural Disasters']),
                        ('Unit 3: Economics', ['Lesson 1: Economic System', 'Lesson 2: National Income']),
                    ],
                    'Computer': [
                        ('Unit 1: Programming', ['Lesson 1: Introduction to Python', 'Lesson 2: Variables', 'Lesson 3: Loops']),
                    ],
                    'Health': [
                        ('Unit 1: Adolescence', ['Lesson 1: Physical Changes', 'Lesson 2: Mental Health', 'Lesson 3: Nutrition']),
                    ],
                },
                'Class 7': {
                    'English': [
                        ('Unit 1: Literature', ['Lesson 1: Prose - The Cop and the Anthem', 'Lesson 2: Poetry - Daffodils', 'Lesson 3: Supplementary Reading']),
                        ('Unit 2: Grammar', ['Lesson 1: Tenses', 'Lesson 2: Active and Passive Voice', 'Lesson 3: Direct and Indirect Speech']),
                        ('Unit 3: Writing', ['Lesson 1: Formal Letter', 'Lesson 2: Report Writing', 'Lesson 3: Story Writing']),
                        ('Unit 4: Comprehension', ['Lesson 1: Unseen Passage', 'Lesson 2: Poetry Analysis']),
                        ('Unit 5: Vocabulary', ['Lesson 1: Word Formation', 'Lesson 2: Phrasal Verbs', 'Lesson 3: One Word Substitution']),
                    ],
                    'Nepali': [
                        ('Unit 1: Nepali Sahitya', ['Lesson 1: Bhanubhakta', 'Lesson 2: Moti Laxmi', 'Lesson 3: Siddhicharan']),
                        ('Unit 2: Grammar', ['Lesson 1: Byakaran', 'Lesson 2: Muddha Prayog']),
                        ('Unit 3: Writing', ['Lesson 1: Nibandh', 'Lesson 2: Patralekhan']),
                    ],
                    'Mathematics': [
                        ('Unit 1: Algebra', ['Lesson 1: Linear Equations', 'Lesson 2: Inequalities', 'Lesson 3: Polynomials', 'Lesson 4: Factorization']),
                        ('Unit 2: Geometry', ['Lesson 1: Congruence', 'Lesson 2: Similarity', 'Lesson 3: Pythagoras Theorem']),
                        ('Unit 3: Mensuration', ['Lesson 1: Area and Perimeter', 'Lesson 2: Surface Area', 'Lesson 3: Volume']),
                        ('Unit 4: Statistics', ['Lesson 1: Data Collection', 'Lesson 2: Graphs', 'Lesson 3: Mean Median Mode']),
                    ],
                    'Science': [
                        ('Unit 1: Biology', ['Lesson 1: Nutrition in Plants', 'Lesson 2: Nutrition in Animals', 'Lesson 3: Respiration']),
                        ('Unit 2: Physics', ['Lesson 1: Heat', 'Lesson 2: Light', 'Lesson 3: Sound Waves']),
                        ('Unit 3: Chemistry', ['Lesson 1: Atomic Structure', 'Lesson 2: Chemical Bonds', 'Lesson 3: Acids and Bases']),
                    ],
                    'Social Studies': [
                        ('Unit 1: Nepal ko Itihas', ['Lesson 1: Shah Dynasty', 'Lesson 2: Rana Period', 'Lesson 3: Democracy Movement']),
                        ('Unit 2: Nepal ko Bhugol', ['Lesson 1: Himalayas', 'Lesson 2: Rivers', 'Lesson 3: Climate Zones']),
                        ('Unit 3: Citizenship', ['Lesson 1: Rights and Duties', 'Lesson 2: Constitution of Nepal']),
                    ],
                    'Computer': [
                        ('Unit 1: Data and Information', ['Lesson 1: Data Types', 'Lesson 2: Spreadsheet Basics', 'Lesson 3: Database Basics']),
                    ],
                    'Health': [
                        ('Unit 1: Disease and Health', ['Lesson 1: Communicable Diseases', 'Lesson 2: Non-Communicable Diseases', 'Lesson 3: First Aid']),
                    ],
                },
                'Class 8': {
                    'English': [
                        ('Unit 1: Literature', ['Lesson 1: The Blue Bird', 'Lesson 2: The Cop and the Anthem', 'Lesson 3: Supplementary']),
                        ('Unit 2: Grammar', ['Lesson 1: Tenses', 'Lesson 2: Voice', 'Lesson 3: Speech', 'Lesson 4: Articles']),
                        ('Unit 3: Writing', ['Lesson 1: Essay', 'Lesson 2: Letter', 'Lesson 3: Story', 'Lesson 4: Dialogue']),
                        ('Unit 4: Comprehension', ['Lesson 1: Reading Skills', 'Lesson 2: Summary Writing']),
                        ('Unit 5: Vocabulary', ['Lesson 1: Synonyms', 'Lesson 2: Antonyms', 'Lesson 3: Idioms and Phrases']),
                    ],
                    'Nepali': [
                        ('Unit 1: Nepali Sahitya', ['Lesson 1: Bhanubhakta', 'Lesson 2: Lakshmi Prasad Devkota', 'Lesson 3: Siddhicharan']),
                        ('Unit 2: Grammar', ['Lesson 1: Byakaran', 'Lesson 2: Sandhi', 'Lesson 3: Samas']),
                        ('Unit 3: Writing', ['Lesson 1: Nibandh', 'Lesson 2: Patra', 'Lesson 3: Sankalp Patra']),
                    ],
                    'Mathematics': [
                        ('Unit 1: Algebra', ['Lesson 1: Exponents and Powers', 'Lesson 2: Algebraic Expressions', 'Lesson 3: Factorization', 'Lesson 4: Linear Equations']),
                        ('Unit 2: Geometry', ['Lesson 1: Lines and Angles', 'Lesson 2: Triangles', 'Lesson 3: Quadrilaterals', 'Lesson 4: Circles']),
                        ('Unit 3: Mensuration', ['Lesson 1: Surface Area', 'Lesson 2: Volume', 'Lesson 3: Herons Formula']),
                        ('Unit 4: Statistics', ['Lesson 1: Data Handling', 'Lesson 2: Probability']),
                    ],
                    'Science': [
                        ('Unit 1: Physics', ['Lesson 1: Force and Pressure', 'Lesson 2: Friction', 'Lesson 3: Sound', 'Lesson 4: Light']),
                        ('Unit 2: Chemistry', ['Lesson 1: Matter', 'Lesson 2: Atoms and Molecules', 'Lesson 3: Chemical Reactions']),
                        ('Unit 3: Biology', ['Lesson 1: Cell', 'Lesson 2: Reproduction', 'Lesson 3: Ecosystem']),
                    ],
                    'Social Studies': [
                        ('Unit 1: Nepal ko Itihas', ['Lesson 1: Ancient Nepal', 'Lesson 2: Medieval Nepal', 'Lesson 3: Modern Nepal']),
                        ('Unit 2: Nepal ko Bhugol', ['Lesson 1: Physical Features', 'Lesson 2: Natural Resources', 'Lesson 3: Environment']),
                        ('Unit 3: Economics', ['Lesson 1: Economic Development', 'Lesson 2: Budget and Planning']),
                    ],
                    'Computer': [
                        ('Unit 1: Networks', ['Lesson 1: What is Network?', 'Lesson 2: Internet', 'Lesson 3: HTML Basics']),
                    ],
                    'Health': [
                        ('Unit 1: Population and Health', ['Lesson 1: Population Growth', 'Lesson 2: Reproductive Health', 'Lesson 3: Drug Abuse']),
                    ],
                },
                'Class 9': {
                    'English': [
                        ('Unit 1: Literature', ['Lesson 1: The Necklace', 'Lesson 2: The Sound of Music', 'Lesson 3: Katha']),
                        ('Unit 2: Grammar', ['Lesson 1: Tenses', 'Lesson 2: Modals', 'Lesson 3: Subject-Verb Agreement', 'Lesson 4: Reported Speech']),
                        ('Unit 3: Writing', ['Lesson 1: Article', 'Lesson 2: Speech', 'Lesson 3: Story', 'Lesson 4: Notice']),
                        ('Unit 4: Comprehension', ['Lesson 1: Unseen Passage', 'Lesson 2: Poetry Appreciation']),
                        ('Unit 5: Vocabulary', ['Lesson 1: Word Power', 'Lesson 2: One Word Substitution', 'Lesson 3: Idioms']),
                    ],
                    'Nepali': [
                        ('Unit 1: Nepali Sahitya', ['Lesson 1: Bhanubhakta', 'Lesson 2: Devkota', 'Lesson 3: Sharma']),
                        ('Unit 2: Grammar', ['Lesson 1: Byakaran', 'Lesson 2: Samas', 'Lesson 3: Paryayvachi']),
                        ('Unit 3: Writing', ['Lesson 1: Nibandh', 'Lesson 2: Patra', 'Lesson 3: Pravartak']),
                    ],
                    'Mathematics': [
                        ('Unit 1: Real Numbers', ['Lesson 1: Euclids Division Lemma', 'Lesson 2: Fundamental Theorem of Arithmetic', 'Lesson 3: Irrational Numbers']),
                        ('Unit 2: Polynomials', ['Lesson 1: Zeroes of Polynomial', 'Lesson 2: Remainder Theorem', 'Lesson 3: Factorisation']),
                        ('Unit 3: Coordinate Geometry', ['Lesson 1: Cartesian Plane', 'Lesson 2: Distance Formula', 'Lesson 3: Section Formula']),
                        ('Unit 4: Linear Equations', ['Lesson 1: Two Variables', 'Lesson 2: Graphical Method', 'Lesson 3: Algebraic Methods']),
                    ],
                    'Science': [
                        ('Unit 1: Matter', ['Lesson 1: Particle Nature', 'Lesson 2: Atoms', 'Lesson 3: Molecules', 'Lesson 4: Ions']),
                        ('Unit 2: Biology', ['Lesson 1: Cell', 'Lesson 2: Tissues', 'Lesson 3: Plant Tissues', 'Lesson 4: Animal Tissues']),
                        ('Unit 3: Physics', ['Lesson 1: Motion', 'Lesson 2: Laws of Motion', 'Lesson 3: Gravitation']),
                        ('Unit 4: Chemistry', ['Lesson 1: Atoms', 'Lesson 2: Molecules', 'Lesson 3: Chemical Reactions']),
                    ],
                    'Social Studies': [
                        ('Unit 1: Nepal ko Itihas', ['Lesson 1: Ancient Nepal', 'Lesson 2: Medieval', 'Lesson 3: Modern Nepal']),
                        ('Unit 2: Nepal ko Bhugol', ['Lesson 1: Physical', 'Lesson 2: Climate', 'Lesson 3: Natural Resources']),
                        ('Unit 3: Economics', ['Lesson 1: Economic Concepts', 'Lesson 2: National Income']),
                    ],
                    'Computer': [
                        ('Unit 1: Networking', ['Lesson 1: Types of Networks', 'Lesson 2: Internet Protocols', 'Lesson 3: HTML']),
                    ],
                    'Health': [
                        ('Unit 1: Health and Disease', ['Lesson 1: Health', 'Lesson 2: Diseases', 'Lesson 3: Immunity']),
                    ],
                },
                'Class 10': {
                    'English': [
                        ('Unit 1: Literature', ['Lesson 1: Two Gentlemen of Verona', 'Lesson 2: Mrs. Packletide Tiger', 'Lesson 3: The Letter']),
                        ('Unit 2: Grammar', ['Lesson 1: Tenses', 'Lesson 2: Modals', 'Lesson 3: Subject-Verb Agreement', 'Lesson 4: Reported Speech', 'Lesson 5: Determiners']),
                        ('Unit 3: Writing', ['Lesson 1: Letter', 'Lesson 2: Speech', 'Lesson 3: Report', 'Lesson 4: Article']),
                        ('Unit 4: Literature', ['Lesson 1: Poetry', 'Lesson 2: Supplementary Reader']),
                        ('Unit 5: Vocabulary', ['Lesson 1: Word Power', 'Lesson 2: Phrasal Verbs', 'Lesson 3: Idioms and Phrases']),
                    ],
                    'Nepali': [
                        ('Unit 1: Nepali Sahitya', ['Lesson 1: Bhanubhakta', 'Lesson 2: Devkota', 'Lesson 3: Sharma', 'Lesson 4: Lekhan']),
                        ('Unit 2: Grammar', ['Lesson 1: Byakaran', 'Lesson 2: Sandhi', 'Lesson 3: Samas', 'Lesson 4: Paryayvachi']),
                        ('Unit 3: Writing', ['Lesson 1: Nibandh', 'Lesson 2: Patra', 'Lesson 3: Sankalp']),
                    ],
                    'Mathematics': [
                        ('Unit 1: Real Numbers', ['Lesson 1: Euclids Division', 'Lesson 2: HCF and LCM', 'Lesson 3: Irrational Numbers']),
                        ('Unit 2: Polynomials', ['Lesson 1: Zeroes', 'Lesson 2: Remainder Theorem', 'Lesson 3: Factorisation']),
                        ('Unit 3: Linear Equations', ['Lesson 1: Pair of Linear Equations', 'Lesson 2: Graphical Method', 'Lesson 3: Algebraic Methods']),
                        ('Unit 4: Quadratic Equations', ['Lesson 1: Standard Form', 'Lesson 2: Factorisation', 'Lesson 3: Quadratic Formula']),
                        ('Unit 5: Arithmetic Progressions', ['Lesson 1: AP Basics', 'Lesson 2: nth Term', 'Lesson 3: Sum of AP']),
                    ],
                    'Science': [
                        ('Unit 1: Chemical Reactions', ['Lesson 1: Types of Reactions', 'Lesson 2: Acids Bases Salts', 'Lesson 3: Metals and Non-Metals']),
                        ('Unit 2: Life Processes', ['Lesson 1: Nutrition', 'Lesson 2: Respiration', 'Lesson 3: Transportation', 'Lesson 4: Excretion']),
                        ('Unit 3: Control and Coordination', ['Lesson 1: Nervous System', 'Lesson 2: Hormones', 'Lesson 3: Plants']),
                        ('Unit 4: Electricity', ['Lesson 1: Electric Current', 'Lesson 2: Ohms Law', 'Lesson 3: Circuits']),
                    ],
                    'Social Studies': [
                        ('Unit 1: Nepal ko Itihas', ['Lesson 1: Ancient', 'Lesson 2: Medieval', 'Lesson 3: Modern', 'Lesson 4: Contemporary']),
                        ('Unit 2: Nepal ko Bhugol', ['Lesson 1: Physical', 'Lesson 2: Climate', 'Lesson 3: Resources']),
                        ('Unit 3: Economics', ['Lesson 1: Development', 'Lesson 2: Sectors', 'Lesson 3: Globalisation']),
                        ('Unit 4: Civics', ['Lesson 1: Democracy', 'Lesson 2: Constitution', 'Lesson 3: Rights']),
                    ],
                    'Computer': [
                        ('Unit 1: Internet and Web', ['Lesson 1: WWW', 'Lesson 2: HTML', 'Lesson 3: Networking']),
                    ],
                    'Health': [
                        ('Unit 1: Health and Population', ['Lesson 1: Reproductive Health', 'Lesson 2: Common Diseases', 'Lesson 3: First Aid']),
                    ],
                },
                'Class 11': {
                    'English': [
                        ('Unit 1: Literature', ['Lesson 1: The Portrait of a Lady', 'Lesson 2: We Are Not Afraid to Die', 'Lesson 3: The Ailing Planet']),
                        ('Unit 2: Grammar', ['Lesson 1: Tenses', 'Lesson 2: Modals', 'Lesson 3: Voice', 'Lesson 4: Speech']),
                        ('Unit 3: Writing', ['Lesson 1: Essay', 'Lesson 2: Report', 'Lesson 3: Letter', 'Lesson 4: Notice']),
                        ('Unit 4: Poetry', ['Lesson 1: A Photograph', 'Lesson 2: The Lake Isle of Innisfree']),
                        ('Unit 5: Hornbill Supplementary', ['Lesson 1: The Portrait of a Lady', 'Lesson 2: We Are Not Afraid to Die']),
                    ],
                    'Nepali': [
                        ('Unit 1: Nepali Sahitya', ['Lesson 1: Bhanubhakta', 'Lesson 2: Devkota', 'Lesson 3: Sharma', 'Lesson 4: Lekhan']),
                        ('Unit 2: Grammar', ['Lesson 1: Byakaran', 'Lesson 2: Sandhi', 'Lesson 3: Samas']),
                        ('Unit 3: Writing', ['Lesson 1: Nibandh', 'Lesson 2: Patra', 'Lesson 3: Sankalp']),
                    ],
                    'Mathematics': [
                        ('Unit 1: Sets and Functions', ['Lesson 1: Sets', 'Lesson 2: Relations and Functions', 'Lesson 3: Trigonometric Functions']),
                        ('Unit 2: Algebra', ['Lesson 1: Complex Numbers', 'Lesson 2: Quadratic Equations', 'Lesson 3: Sequences and Series']),
                        ('Unit 3: Coordinate Geometry', ['Lesson 1: Straight Lines', 'Lesson 2: Conic Sections']),
                        ('Unit 4: Calculus', ['Lesson 1: Limits', 'Lesson 2: Derivatives', 'Lesson 3: Applications of Derivatives']),
                    ],
                    'Physics': [
                        ('Unit 1: Physical World', ['Lesson 1: Scope of Physics', 'Lesson 2: Units and Measurements']),
                        ('Unit 2: Kinematics', ['Lesson 1: Motion in a Straight Line', 'Lesson 2: Motion in a Plane']),
                        ('Unit 3: Laws of Motion', ['Lesson 1: Newtons Laws', 'Lesson 2: Applications']),
                        ('Unit 4: Work Energy Power', ['Lesson 1: Work', 'Lesson 2: Energy', 'Lesson 3: Power']),
                    ],
                    'Chemistry': [
                        ('Unit 1: Some Basic Concepts', ['Lesson 1: Matter', 'Lesson 2: Atomic Theory', 'Lesson 3: Chemical Bonding']),
                        ('Unit 2: Structure of Atom', ['Lesson 1: Atomic Models', 'Lesson 2: Quantum Numbers']),
                        ('Unit 3: Classification of Elements', ['Lesson 1: Periodic Table', 'Lesson 2: Periodic Properties']),
                    ],
                    'Biology': [
                        ('Unit 1: The Living World', ['Lesson 1: Biodiversity', 'Lesson 2: Classification']),
                        ('Unit 2: Biological Molecules', ['Lesson 1: Carbohydrates', 'Lesson 2: Proteins', 'Lesson 3: Nucleic Acids']),
                        ('Unit 3: Cell', ['Lesson 1: Cell Structure', 'Lesson 2: Cell Organelles', 'Lesson 3: Cell Division']),
                    ],
                },
                'Class 12': {
                    'English': [
                        ('Unit 1: Literature', ['Lesson 1: Flamingo - Prose', 'Lesson 2: Flamingo - Poetry', 'Lesson 3: Vistas - Supplementary']),
                        ('Unit 2: Grammar', ['Lesson 1: Tenses', 'Lesson 2: Modals', 'Lesson 3: Voice', 'Lesson 4: Speech', 'Lesson 5: Determiners']),
                        ('Unit 3: Writing', ['Lesson 1: Essay', 'Lesson 2: Report', 'Lesson 3: Letter', 'Lesson 4: Notice', 'Lesson 5: Poster']),
                        ('Unit 4: Poetry', ['Lesson 1: My Mother at Sixty-Six', 'Lesson 2: An Elementary School Classroom']),
                        ('Unit 5: Vistas', ['Lesson 1: The Third Level', 'Lesson 2: The Tiger King', 'Lesson 3: Journey to the End of the Earth']),
                    ],
                    'Nepali': [
                        ('Unit 1: Nepali Sahitya', ['Lesson 1: Bhanubhakta', 'Lesson 2: Devkota', 'Lesson 3: Sharma', 'Lesson 4: Lekhan']),
                        ('Unit 2: Grammar', ['Lesson 1: Byakaran', 'Lesson 2: Sandhi', 'Lesson 3: Samas', 'Lesson 4: Paryayvachi']),
                        ('Unit 3: Writing', ['Lesson 1: Nibandh', 'Lesson 2: Patra', 'Lesson 3: Sankalp', 'Lesson 4: Pravartak']),
                    ],
                    'Mathematics': [
                        ('Unit 1: Relations and Functions', ['Lesson 1: Types of Relations', 'Lesson 2: Functions', 'Lesson 3: Inverse Functions']),
                        ('Unit 2: Algebra', ['Lesson 1: Matrices', 'Lesson 2: Determinants', 'Lesson 3: Continuity', 'Lesson 4: Differentiability']),
                        ('Unit 3: Calculus', ['Lesson 1: Integration', 'Lesson 2: Applications of Integration', 'Lesson 3: Differential Equations']),
                        ('Unit 4: Vectors and 3D Geometry', ['Lesson 1: Vectors', 'Lesson 2: Three Dimensional Geometry']),
                        ('Unit 5: Linear Programming', ['Lesson 1: LP Problems', 'Lesson 2: Graphical Method']),
                    ],
                    'Physics': [
                        ('Unit 1: Electrostatics', ['Lesson 1: Electric Charges', 'Lesson 2: Coulombs Law', 'Lesson 3: Electric Field']),
                        ('Unit 2: Current Electricity', ['Lesson 1: Ohms Law', 'Lesson 2: Kirchhoffs Laws', 'Lesson 3: Wheatstone Bridge']),
                        ('Unit 3: Magnetism', ['Lesson 1: Magnetic Field', 'Lesson 2: Electromagnetic Induction']),
                        ('Unit 4: Optics', ['Lesson 1: Reflection', 'Lesson 2: Refraction', 'Lesson 3: Wave Optics']),
                    ],
                    'Chemistry': [
                        ('Unit 1: Solid State', ['Lesson 1: Types of Solids', 'Lesson 2: Unit Cells', 'Lesson 3: Packing Efficiency']),
                        ('Unit 2: Solutions', ['Lesson 1: Types of Solutions', 'Lesson 2: Raoult Law', 'Lesson 3: Colligative Properties']),
                        ('Unit 3: Electrochemistry', ['Lesson 1: Redox Reactions', 'Lesson 2: Electrochemical Cells', 'Lesson 3: Nernst Equation']),
                        ('Unit 4: Organic Chemistry', ['Lesson 1: Hydrocarbons', 'Lesson 2: Haloalkanes', 'Lesson 3: Alcohols Phenols Ethers']),
                    ],
                    'Biology': [
                        ('Unit 1: Reproduction', ['Lesson 1: Human Reproduction', 'Lesson 2: Plant Reproduction', 'Lesson 3: Reproductive Health']),
                        ('Unit 2: Genetics', ['Lesson 1: Mendelian Inheritance', 'Lesson 2: Molecular Basis of Inheritance', 'Lesson 3: Evolution']),
                        ('Unit 3: Biotechnology', ['Lesson 1: Principles', 'Lesson 2: Applications', 'Lesson 3: GMOs']),
                        ('Unit 4: Ecology', ['Lesson 1: Ecosystem', 'Lesson 2: Biodiversity', 'Lesson 3: Environmental Issues']),
                    ],
                    'Accountancy': [
                        ('Unit 1: Accounting Basics', ['Lesson 1: Theory Base', 'Lesson 2: Accounting Process', 'Lesson 3: Subsidiary Books']),
                        ('Unit 2: Partnership', ['Lesson 1: Nature', 'Lesson 2: Admission', 'Lesson 3: Retirement']),
                        ('Unit 3: Company Accounts', ['Lesson 1: Shares', 'Lesson 2: Debentures', 'Lesson 3: Financial Statements']),
                    ],
                    'Business Studies': [
                        ('Unit 1: Business Nature', ['Lesson 1: Forms of Business', 'Lesson 2: Business Services']),
                        ('Unit 2: Management', ['Lesson 1: Principles', 'Lesson 2: Functions', 'Lesson 3: Planning']),
                        ('Unit 3: Marketing', ['Lesson 1: Marketing Mix', 'Lesson 2: Consumer Protection']),
                    ],
                    'Economics': [
                        ('Unit 1: Introductory Macroeconomics', ['Lesson 1: National Income', 'Lesson 2: Money and Banking', 'Lesson 3: Government Budget']),
                        ('Unit 2: Indian Economic Development', ['Lesson 1: Poverty', 'Lesson 2: Infrastructure', 'Lesson 3: Liberalisation']),
                    ],
                },
            }

            for cls, subjects_data in curriculum.items():
                for subj_name, units_data in subjects_data.items():
                    subj = Subject.query.filter_by(name=subj_name, class_name=cls).first()
                    if not subj:
                        subj = Subject(name=subj_name, code=f'{cls.replace(" ","")}-{subj_name[:3].upper()}', class_name=cls)
                        db.session.add(subj)
                        db.session.flush()

                    for unit_name, lessons_list in units_data:
                        unit = Unit.query.filter_by(subject_id=subj.id, name=unit_name).first()
                        if not unit:
                            unit = Unit(subject_id=subj.id, name=unit_name, order=units_data.index((unit_name, lessons_list)) + 1)
                            db.session.add(unit)
                            db.session.flush()

                        for lesson_name in lessons_list:
                            lesson = Lesson.query.filter_by(unit_id=unit.id, name=lesson_name).first()
                            if not lesson:
                                lesson = Lesson(unit_id=unit.id, name=lesson_name, order=lessons_list.index(lesson_name) + 1)
                                db.session.add(lesson)

            db.session.commit()
            print(f"Curriculum populated! Subjects: {Subject.query.count()}, Units: {Unit.query.count()}, Lessons: {Lesson.query.count()}")


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
