import os
import json
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import (db, User, QuestionBank, LessonPlan, Slide, Worksheet, FlashCard,
                    ReportCard, Student, Teacher, FeeRecord, Exam, Notice, UploadedImage,
                    CLASS_CHOICES, SUBJECT_CHOICES, QUESTION_TYPES, DIFFICULTY_LEVELS)

app = Flask(__name__)
app.config.from_object(Config)

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

            sample_questions = [
                QuestionBank(class_name='Class 8', subject='Science', chapter='Force and Pressure',
                           question_type='MCQ', question_text='What is the SI unit of force?',
                           option_a='Newton', option_b='Joule', option_c='Pascal', option_d='Watt',
                           correct_answer='Newton', difficulty='Easy', language='English', created_by=admin.id),
                QuestionBank(class_name='Class 8', subject='Science', chapter='Force and Pressure',
                           question_type='MCQ', question_text='Force is a ____. quantity.',
                           option_a='Scalar', option_b='Vector', option_c='Both', option_d='None',
                           correct_answer='Vector', difficulty='Easy', language='English', created_by=admin.id),
                QuestionBank(class_name='Class 8', subject='Science', chapter='Light',
                           question_type='MCQ', question_text='The speed of light in vacuum is:',
                           option_a='3 x 10^8 m/s', option_b='3 x 10^6 m/s', option_c='3 x 10^10 m/s', option_d='3 x 10^5 m/s',
                           correct_answer='3 x 10^8 m/s', difficulty='Medium', language='English', created_by=admin.id),
                QuestionBank(class_name='Class 10', subject='Mathematics', chapter='Algebra',
                           question_type='MCQ', question_text='The value of x in 2x + 5 = 15 is:',
                           option_a='5', option_b='10', option_c='7.5', option_d='8',
                           correct_answer='5', difficulty='Easy', language='English', created_by=admin.id),
                QuestionBank(class_name='Class 10', subject='English', chapter='Grammar',
                           question_type='Very Short Answer', question_text='Define a noun with one example.',
                           difficulty='Easy', language='English', created_by=admin.id),
            ]
            db.session.add_all(sample_questions)
            db.session.commit()
            print("Database initialized!")
            print("Admin: admin@akeasypathshala.com / admin123")
            print("Teacher: teacher@akeasypathshala.com / teacher123")


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
