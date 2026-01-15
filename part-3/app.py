"""
Part 3: Flask-SQLAlchemy ORM
============================
Say goodbye to raw SQL! Use Python classes to work with databases.

What You'll Learn:
- Setting up Flask-SQLAlchemy
- Creating Models (Python classes = database tables)
- ORM queries instead of raw SQL
- Relationships between tables (One-to-Many)

Prerequisites: Complete part-1 and part-2
Install: pip install flask-sqlalchemy
"""
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# =============================================================================
# DATABASE CONFIG
# =============================================================================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =============================================================================
# MODELS
# =============================================================================

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    # One Teacher → Many Courses
    courses = db.relationship('Course', backref='teacher', lazy=True)

    def __repr__(self):
        return f'<Teacher {self.name}>'


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)

    # One Course → Many Students
    students = db.relationship('Student', backref='course', lazy=True)

    def __repr__(self):
        return f'<Course {self.name}>'


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    def __repr__(self):
        return f'<Student {self.name}>'

# =============================================================================
# ROUTES
# =============================================================================

@app.route('/')
def index():
    students = Student.query.all()
    return render_template('index.html', students=students)


@app.route('/courses')
def courses():
    # Demonstrate ordering and optional limiting via query params
    query = Course.query.order_by(Course.name)
    limit = request.args.get('limit', type=int)
    if limit:
        query = query.limit(limit)
    courses = query.all()
    return render_template('courses.html', courses=courses)


@app.route('/teachers')
def teachers_view():
    # Order teachers by name
    teachers = Teacher.query.order_by(Teacher.name).all()
    return render_template('teachers.html', teachers=teachers)


@app.route('/courses/teacher/<int:teacher_id>')
def courses_by_teacher(teacher_id):
    # Filter courses by teacher using filter()
    teacher = Teacher.query.get_or_404(teacher_id)
    courses = Course.query.filter(Course.teacher_id == teacher_id).order_by(Course.name).all()
    return render_template('courses.html', courses=courses, teacher=teacher)


@app.route('/add', methods=['GET', 'POST'])
def add_student():
    courses = Course.query.all()

    if request.method == 'POST':
        student = Student(
            name=request.form['name'],
            email=request.form['email'],
            course_id=request.form['course_id']
        )
        db.session.add(student)
        db.session.commit()
        flash('Student added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add.html', courses=courses)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    student = Student.query.get_or_404(id)
    courses = Course.query.all()

    if request.method == 'POST':
        student.name = request.form['name']
        student.email = request.form['email']
        student.course_id = request.form['course_id']
        db.session.commit()
        flash('Student updated!', 'success')
        return redirect(url_for('index'))

    return render_template('edit.html', student=student, courses=courses)


@app.route('/delete/<int:id>')
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted!', 'danger')
    return redirect(url_for('index'))


@app.route('/add-course', methods=['GET', 'POST'])
def add_course():
    teachers = Teacher.query.all()

    if request.method == 'POST':
        course = Course(
            name=request.form['name'],
            description=request.form.get('description'),
            teacher_id=request.form['teacher_id']
        )
        db.session.add(course)
        db.session.commit()
        flash('Course added!', 'success')
        return redirect(url_for('courses'))

    return render_template('add_course.html', teachers=teachers)


@app.route('/add-teacher', methods=['GET', 'POST'])
def add_teacher():
    if request.method == 'POST':
        teacher = Teacher(
            name=request.form['name'],
            email=request.form['email']
        )
        db.session.add(teacher)
        db.session.commit()
        flash('Teacher added!', 'success')
        return redirect(url_for('courses'))

    return render_template('add_teacher.html')

# =============================================================================
# INIT DATABASE
# =============================================================================

def init_db():
    with app.app_context():
        db.create_all()

        if Teacher.query.count() == 0:
            teachers = [
                Teacher(name='Dr. Sharma', email='sharma@example.com'),
                Teacher(name='Prof. Mehta', email='mehta@example.com'),
            ]
            db.session.add_all(teachers)
            db.session.commit()

        if Course.query.count() == 0:
            courses = [
                Course(name='Python Basics', description='Learn Python', teacher_id=1),
                Course(name='Web Development', description='Flask & Web', teacher_id=2),
            ]
            db.session.add_all(courses)
            db.session.commit()


if __name__ == '__main__':
    init_db()
    app.run(debug=True)

# =============================================================================
# ORM vs RAW SQL COMPARISON:
# =============================================================================
#
# Operation      | Raw SQL                          | SQLAlchemy ORM
# ---------------|----------------------------------|---------------------------
# Get all        | SELECT * FROM students           | Student.query.all()
# Get by ID      | SELECT * WHERE id = ?            | Student.query.get(id)
# Filter         | SELECT * WHERE name = ?          | Student.query.filter_by(name='John')
# Insert         | INSERT INTO students VALUES...   | db.session.add(student)
# Update         | UPDATE students SET...           | student.name = 'New'; db.session.commit()
# Delete         | DELETE FROM students WHERE...    | db.session.delete(student)
#
# =============================================================================
# COMMON QUERY METHODS:
# =============================================================================
#
# Student.query.all()                    - Get all records
# Student.query.first()                  - Get first record
# Student.query.get(1)                   - Get by primary key
# Student.query.get_or_404(1)            - Get or show 404 error
# Student.query.filter_by(name='John')   - Filter by exact value
# Student.query.filter(Student.name.like('%john%'))  - Filter with LIKE
# Student.query.order_by(Student.name)   - Order results
# Student.query.count()                  - Count records
#
# =============================================================================


# =============================================================================
# EXERCISE:
# =============================================================================
#
# 1. Add a `Teacher` model with a relationship to Course
# 2. Try different query methods: `filter()`, `order_by()`, `limit()`
#
# =============================================================================
